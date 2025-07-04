from paynow import Paynow
from django.conf import settings
from .models import Payment
import uuid
import logging

logger = logging.getLogger(__name__)

class PaynowService:
    def __init__(self):
        self.paynow = Paynow(
            integration_id=settings.PAYNOW_INTEGRATION_ID,
            integration_key=settings.PAYNOW_INTEGRATION_KEY,
            return_url=settings.PAYNOW_RETURN_URL,
            result_url=settings.PAYNOW_RESULT_URL
        )

    def create_payment(self, property_obj, user):
        if not hasattr(user, "phone_number") or not user.phone_number:
            raise ValueError("Phone number is required for mobile money payment.")

        # Use existing failed payment or create new
        payment = Payment.objects.filter(property=property_obj).first()

        amount = 20.00 if property_obj.listing_type == 'priority' else 10.00
        reference = f"PROP-{uuid.uuid4().hex[:8]}"  # always generate new reference

        if payment:
            if payment.status == Payment.PAID:
                raise ValueError("This property has already been paid for.")
            # Update existing failed/pending payment
            payment.reference = reference
            payment.amount = amount
            payment.listing_type = property_obj.listing_type
            payment.status = Payment.PENDING
            payment.poll_url = None  # reset poll URL
            payment.save()
        else:
            # Create new payment
            payment = Payment.objects.create(
                property=property_obj,
                user=user,
                listing_type=property_obj.listing_type,
                amount=amount,
                reference=reference
            )

        try:
            payment_data = self.paynow.create_payment(reference, user.email)
            payment_data.add(
                f"{property_obj.listing_type.title()} Listing - {property_obj.title}",
                float(amount)
            )
            response = self.paynow.send_mobile(
                payment_data,
                user.phone_number,
                'ecocash'
            )
        except Exception:
            logger.exception("Failed to initiate payment with Paynow for reference %s", reference)
            payment.status = Payment.FAILED
            payment.save()
            return None

        if response.success:
            payment.poll_url = response.poll_url
            payment.save()
            return response

        payment.status = Payment.FAILED
        payment.save()
        return None

    def check_payment_status(self, payment):
        try:
            status = self.paynow.check_transaction_status(payment.poll_url)
        except Exception:
            logger.exception("Failed to check payment status for reference %s", payment.reference)
            payment.status = Payment.FAILED
            payment.save()
            return False

        if status.paid:
            payment.status = Payment.PAID
            payment.save()

            property_obj = payment.property
            property_obj.is_paid = True
            property_obj.save()

            return True

        return False

paynow_service = PaynowService()