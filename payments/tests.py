from django.test import TestCase, RequestFactory, override_settings
from django.contrib.auth import get_user_model
from django.http import HttpResponse
from django.urls import reverse
from unittest.mock import patch
from listings.models import Property
from payments.models import Payment
from payments.views import payment_complete, payment_update

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

    @patch("payments.views.render", return_value=HttpResponse("ok"))
    def test_invalid_reference_returns_failed(self, mock_render):
        request = self.factory.get(reverse("payment_complete"), {"reference": "BAD"})
        request.user = self.user
        response = payment_complete(request)

        self.assertEqual(response.status_code, 200)
        mock_render.assert_called_once_with(request, "payments/payment_failed.html")

@override_settings(
        DATABASES={"default": {"ENGINE": "django.db.backends.sqlite3", "NAME": ":memory:"}}
    )
class PaymentUpdateTests(TestCase):
        def setUp(self):
            self.factory = RequestFactory()
            self.user = get_user_model().objects.create_user(
                username="user2",
                email="user2@example.com",
                password="password",
            )

            self.property = Property.objects.create(owner=self.user)
            self.payment = Payment.objects.create(
                property=self.property,
                user=self.user,
                listing_type="normal",
                reference="UPD123",
            )

        @patch("payments.views.paynow_service.check_payment_status")
        def test_invalid_reference_returns_404(self, mock_check):
            request = self.factory.post(reverse("payment_update"), {"reference": "BAD"})
            response = payment_update(request)

            self.assertEqual(response.status_code, 404)
            mock_check.assert_not_called()
