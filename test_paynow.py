#!/usr/bin/env python
"""
Test script for Paynow integration
Run this to test your Paynow setup without going through the full Django app
"""

import os
import sys
import django
from django.conf import settings

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'tourwise_website.settings')
django.setup()

from payments.services import paynow_service
from payments.models import Payment
from listings.models import Property
from accounts.models import CustomUser


def test_paynow_connection():
    """Test basic Paynow connection"""
    print("🔍 Testing Paynow Connection...")

    try:
        # Test Paynow initialization
        paynow = paynow_service.paynow
        print(f"✅ Paynow initialized successfully")
        print(f"   Integration ID: {settings.PAYNOW_INTEGRATION_ID}")
        print(f"   Mode: {settings.PAYNOW_MODE}")
        print(f"   Return URL: {settings.PAYNOW_RETURN_URL}")
        print(f"   Result URL: {settings.PAYNOW_RESULT_URL}")
        return True
    except Exception as e:
        print(f"❌ Paynow initialization failed: {e}")
        return False


def test_phone_number_formatting():
    """Test phone number formatting"""
    print("\n📱 Testing Phone Number Formatting...")

    test_numbers = [
        "0772123456",
        "+263772123456",
        "263772123456",
        "772123456",
        "0772 123 456",
        "+263 772 123 456"
    ]

    for number in test_numbers:
        formatted = paynow_service._format_phone_number(number)
        print(f"   {number} -> {formatted}")

    return True


def test_mock_payment():
    """Test mock payment creation"""
    print("\n🧪 Testing Mock Payment Creation...")

    try:
        # Create test user
        user, created = CustomUser.objects.get_or_create(
            email='test@example.com',
            defaults={
                'first_name': 'Test',
                'last_name': 'User',
                'phone_number': '0772123456',
                'user_type': 'host'
            }
        )

        # Create test property
        property_obj, created = Property.objects.get_or_create(
            title='Test Property',
            owner=user,
            defaults={
                'listing_type': 'normal',
                'is_paid': False
            }
        )

        # Test payment creation
        response = paynow_service.create_payment(property_obj, user)

        if response and response.success:
            print(f"✅ Mock payment created successfully")
            print(f"   Reference: {property_obj.payment.reference}")
            print(f"   Amount: ${property_obj.payment.amount}")
            print(f"   Status: {property_obj.payment.status}")
            print(f"   Poll URL: {response.poll_url}")
            return True
        else:
            print(f"❌ Mock payment creation failed")
            return False

    except Exception as e:
        print(f"❌ Mock payment test failed: {e}")
        return False


def test_payment_status_check():
    """Test payment status checking"""
    print("\n🔍 Testing Payment Status Check...")

    try:
        # Get the test payment
        payment = Payment.objects.filter(property__title='Test Property').first()
        if not payment:
            print("❌ No test payment found")
            return False

        # Test status check
        result = paynow_service.check_payment_status(payment)
        print(f"   Status check result: {result}")
        print(f"   Payment status: {payment.status}")
        print(f"   Property is_paid: {payment.property.is_paid}")

        return True

    except Exception as e:
        print(f"❌ Payment status check failed: {e}")
        return False


def cleanup_test_data():
    """Clean up test data"""
    print("\n🧹 Cleaning up test data...")

    try:
        # Delete test property and related data
        Property.objects.filter(title='Test Property').delete()
        CustomUser.objects.filter(email='test@example.com').delete()
        print("✅ Test data cleaned up")
    except Exception as e:
        print(f"❌ Cleanup failed: {e}")


def main():
    """Run all tests"""
    print("🚀 Starting Paynow Integration Tests...\n")

    tests = [
        test_paynow_connection,
        test_phone_number_formatting,
        test_mock_payment,
        test_payment_status_check
    ]

    results = []
    for test in tests:
        try:
            result = test()
            results.append(result)
        except Exception as e:
            print(f"❌ Test failed with exception: {e}")
            results.append(False)

    # Summary
    print("\n" + "=" * 50)
    print("📊 TEST RESULTS SUMMARY")
    print("=" * 50)

    passed = sum(results)
    total = len(results)

    print(f"✅ Passed: {passed}/{total}")
    print(f"❌ Failed: {total - passed}/{total}")

    if passed == total:
        print("\n🎉 All tests passed! Your Paynow integration is working correctly.")
    else:
        print("\n⚠️  Some tests failed. Check the output above for details.")

    # Cleanup
    cleanup_test_data()

    return passed == total


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)