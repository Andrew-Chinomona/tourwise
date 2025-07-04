from paynow import Paynow
from django.conf import settings
from .models import Payment
import uuid


class PaynowService:
    def __init__(self):
        self.paynow = Paynow(
            integration_id=settings.PAYNOW_INTEGRATION_ID,
            integration_key=settings.PAYNOW_INTEGRATION_KEY,
            return_url=settings.PAYNOW_RETURN_URL,
            result_url=settings.PAYNOW_RESULT_URL
        )

    def create_payment(self, property_obj, user):
        # Generate unique reference
        reference = f"PROP-{uuid.uuid4().hex[:8]}"

        # Calculate amount based on listing type
        amount = 20.00 if property_obj.listing_type == 'priority' else 10.00

        # Create payment record
        payment = Payment.objects.create(
            property=property_obj,
            user=user,
            listing_type=property_obj.listing_type,
            amount=amount,
            reference=reference
        )

        # Create Paynow payment
        payment_data = self.paynow.create_payment(reference, user.email)

        # Add the item
        payment_data.add(
            f"{property_obj.listing_type.title()} Listing - {property_obj.title}",
            float(amount)
        )

        # Initiate mobile money transaction
        response = self.paynow.send_mobile(
            payment_data,
            user.phone_number,  # Assuming user has phone_number field
            'ecocash'  # or 'onemoney' depending on your needs
        )

        if response.success:
            # Update payment with poll URL
            payment.poll_url = response.poll_url
            payment.save()
            return response

        payment.status = Payment.FAILED
        payment.save()
        return None

    def check_payment_status(self, payment):
        status = self.paynow.check_transaction_status(payment.poll_url)
        if status.paid:
            payment.status = Payment.PAID
            payment.save()

            # Update property status
            property_obj = payment.property
            property_obj.is_paid = True
            property_obj.save()

            return True
        return False


# Create a singleton instance
paynow_service = PaynowService()