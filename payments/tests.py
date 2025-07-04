from django.test import TestCase, RequestFactory, override_settings
from django.contrib.auth import get_user_model
from django.http import HttpResponse
from django.urls import reverse
from unittest.mock import patch

from Tourwise_Website.settings import DATABASES
from listings.models import Property
from payments.models import Payment
from payments.views import payment_complete

@override_settings(
    DATABASES={"default": {"ENGINE": "django.db.backends.sqlite3", "NAME": ":memory:"}}
)

class PaymentCompleteTests(TestCase):
    def setUp(self):
        self.factory = RequestFactory()
        self.user = get_user_model().objects.create_user(
            username='testuser',
            email='test@example.com',
            password="password"
        )
        self.property = Property.objects.create(owner=self.user)
        self.payment = Payment.objects.create(
            property=self.property,
            user=self.user,
            listing_type="normal",
            reference="REF123",
        )

    @patch("payments.views.render", return_value=HttpResponse("ok"))
    @patch("payments.views.paynow_service.check_payment_status", return_value=True)
    def test_property_marked_paid_after_successful_payment(self, mock_check, mock_render):
        request = self.factory.get(reverse("payment_complete"),{"reference": self.payment.reference})
        request.user = self.user
        response = payment_complete(request)

        self.assertEqual(response.status_code, 200)
        self.property.refresh_from_db()
        self.assertTrue(self.property.is_paid)
        mock_check.assert_called_once_with(self.payment)