#!/usr/bin/env python
"""
Test script for your specific phone number: +263789915032
"""

import os
import sys
import django
from django.conf import settings

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'Tourwise_Website.settings')
django.setup()

from payments.services import paynow_service
from payments.models import Payment
from listings.models import Property
from accounts.models import CustomUser


def test_your_phone_number():
    """Test your specific phone number formatting"""
    print("📱 Testing Your Phone Number: +263789915032")

    # Test different formats of your number
    test_numbers = [
        "+263789915032",
        "263789915032",
        "0789915032",
        "789915032",
        "+263 789 915 032"
    ]

    print("\nPhone number formatting results:")
    for number in test_numbers:
        formatted = paynow_service._format_phone_number(number)
        print(f"   {number} -> {formatted}")

    # Determine mobile provider
    formatted = paynow_service._format_phone_number("+263789915032")
    if formatted.startswith('26378'):
        provider = 'onemoney'  # OneMoney
    elif formatted.startswith('26377'):
        provider = 'ecocash'  # EcoCash
    else:
        provider = 'unknown'

    print(f"\n📱 Mobile Provider: {provider}")
    print(f"📱 Formatted Number: {formatted}")

    return formatted


def test_payment_with_your_number():
    """Test payment creation with your phone number"""
    print("\n🧪 Testing Payment Creation with Your Number...")

    try:
        # Create test user with your phone number
        user, created = CustomUser.objects.get_or_create(
            email='test@example.com',
            defaults={
                'first_name': 'Test',
                'last_name': 'User',
                'phone_number': '+263789915032',
                'user_type': 'host'
            }
        )

        # Update phone number if user already exists
        if not created:
            user.phone_number = '+263789915032'
            user.save()

        # Create test property
        property_obj, created = Property.objects.get_or_create(
            title='Test Property - Your Number',
            owner=user,
            defaults={
                'listing_type': 'normal',
                'is_paid': False,
                'city': 'Harare',
                'suburb': 'Test Area'
            }
        )

        print(f"✅ Test user created: {user.email}")
        print(f"✅ Phone number: {user.phone_number}")
        print(f"✅ Test property: {property_obj.title}")

        # Test payment creation
        print("\n🔄 Creating payment...")
        response = paynow_service.create_payment(property_obj, user)

        if response and response.success:
            print(f"✅ Payment created successfully!")
            print(f"   Reference: {property_obj.payment.reference}")
            print(f"   Amount: ${property_obj.payment.amount}")
            print(f"   Status: {property_obj.payment.status}")
            print(f"   Poll URL: {response.poll_url}")

            # Test status check
            print("\n🔄 Testing payment status check...")
            result = paynow_service.check_payment_status(property_obj.payment)
            print(f"   Status check result: {result}")
            print(f"   Final payment status: {property_obj.payment.status}")
            print(f"   Property is_paid: {property_obj.is_paid}")

            return True
        else:
            print(f"❌ Payment creation failed")
            return False

    except Exception as e:
        print(f"❌ Payment test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def cleanup():
    """Clean up test data"""
    print("\n🧹 Cleaning up test data...")
    try:
        Property.objects.filter(title='Test Property - Your Number').delete()
        CustomUser.objects.filter(email='test@example.com').delete()
        print("✅ Test data cleaned up")
    except Exception as e:
        print(f"❌ Cleanup failed: {e}")


def main():
    """Run tests with your phone number"""
    print("🚀 Testing Paynow Integration with Your Phone Number")
    print("=" * 60)

    # Test phone number formatting
    formatted_number = test_your_phone_number()

    # Test payment creation
    payment_success = test_payment_with_your_number()

    # Summary
    print("\n" + "=" * 60)
    print("📊 TEST RESULTS")
    print("=" * 60)

    if formatted_number and payment_success:
        print("🎉 SUCCESS! Your phone number works perfectly with the payment system.")
        print("\n📋 Next Steps:")
        print("1. Start your Django server: python manage.py runserver")
        print("2. Go to: http://localhost:8000")
        print("3. Create a listing and test the payment flow")
        print("4. You'll see 'DEVELOPMENT TEST MODE' for testing")
    else:
        print("❌ Some tests failed. Check the output above for details.")

    # Cleanup
    cleanup()

    return formatted_number and payment_success


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)