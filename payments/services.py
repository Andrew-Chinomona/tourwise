from paynow import Paynow
from django.conf import settings
from .models import Payment
import uuid
import logging
import os

logger = logging.getLogger(__name__)


class PaynowService:
    def __init__(self):
        # Check if we're in development mode
        self.is_test_mode = getattr(settings, 'PAYNOW_MODE', 'test') == 'test'
        self.is_dev_mode = getattr(settings, 'DEBUG', False)

        if self.is_dev_mode and self.is_test_mode:
            logger.info("Running in DEVELOPMENT TEST MODE - payments will be simulated")

        self.paynow = Paynow(
            integration_id=settings.PAYNOW_INTEGRATION_ID,
            integration_key=settings.PAYNOW_INTEGRATION_KEY,
            return_url=settings.PAYNOW_RETURN_URL,
            result_url=settings.PAYNOW_RESULT_URL
        )

    def _format_phone_number(self, phone_number):
        """Format phone number for Paynow"""
        if not phone_number:
            return None

        # Remove spaces and special characters
        phone = ''.join(filter(str.isdigit, phone_number))

        # Handle Zimbabwe numbers
        if phone.startswith('263'):
            return phone
        elif phone.startswith('0'):
            return '263' + phone[1:]
        elif len(phone) == 9:
            return '263' + phone
        else:
            return phone

    def _create_mock_response(self, payment, success=True):
        """Create a mock response for development testing"""

        class MockResponse:
            def __init__(self, success, poll_url, instructions):
                self.success = success
                self.poll_url = poll_url
                self.instructions = instructions

        if success:
            poll_url = f"/payments/status/{payment.reference}/"
            instructions = f"""
            <h4>🧪 DEVELOPMENT TEST MODE</h4>
            <p>This is a simulated payment for testing purposes.</p>
            <p><strong>Reference:</strong> {payment.reference}</p>
            <p><strong>Amount:</strong> ${payment.amount}</p>
            <p><strong>Phone:</strong> {payment.user.phone_number}</p>
            <div class="alert alert-info">
                <strong>To simulate successful payment:</strong><br>
                1. Wait 10 seconds for automatic success<br>
                2. Or click the "Simulate Success" button below
            </div>
            <button onclick="simulatePaymentSuccess()" class="btn btn-success">
                🎯 Simulate Successful Payment
            </button>
            """
        else:
            poll_url = None
            instructions = "Payment simulation failed"

        return MockResponse(success, poll_url, instructions)

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

        # DEVELOPMENT MODE: Use mock responses
        if self.is_dev_mode and self.is_test_mode:
            logger.info(f"DEVELOPMENT: Creating mock payment for reference {reference}")
            return self._create_mock_response(payment, success=True)

        # PRODUCTION MODE: Use real Paynow
        try:
            # Format phone number properly
            formatted_phone = self._format_phone_number(user.phone_number)
            if not formatted_phone:
                raise ValueError("Invalid phone number format")

            payment_data = self.paynow.create_payment(reference, user.email)
            payment_data.add(
                f"{property_obj.listing_type.title()} Listing - {property_obj.title}",
                float(amount)
            )

            # Use 'ecocash' for Econet numbers, 'onemoney' for OneMoney
            mobile_provider = 'onemoney' if formatted_phone.startswith('26378') else 'ecocash'

            response = self.paynow.send_mobile(
                payment_data,
                formatted_phone,
                mobile_provider
            )

            logger.info(f"Paynow response: {response.success}, Poll URL: {getattr(response, 'poll_url', 'None')}")

        except Exception as e:
            logger.exception(f"Failed to initiate payment with Paynow for reference {reference}: {str(e)}")
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
        # DEVELOPMENT MODE: Simulate successful payment after delay
        if self.is_dev_mode and self.is_test_mode:
            logger.info(f"DEVELOPMENT: Checking mock payment status for {payment.reference}")
            # Simulate successful payment after 10 seconds
            import time
            if hasattr(payment, '_created_at'):
                time_diff = time.time() - payment._created_at
                if time_diff > 10:  # 10 seconds delay
                    payment.status = Payment.PAID
                    payment.save()
                    property_obj = payment.property
                    property_obj.is_paid = True
                    property_obj.save()
                    logger.info(f"DEVELOPMENT: Mock payment successful for {payment.reference}")
                    return True
            return False

        # PRODUCTION MODE: Check real Paynow status
        try:
            status = self.paynow.check_transaction_status(payment.poll_url)
            logger.info(f"Paynow status check: {status.paid} for {payment.reference}")
        except Exception as e:
            logger.exception(f"Failed to check payment status for reference {payment.reference}: {str(e)}")
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