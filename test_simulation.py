#!/usr/bin/env python
"""
Test script to verify payment simulation properly updates is_paid status
"""

import os
import sys
import django
from django.conf import settings

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'Tourwise_Website.settings')
django.setup()

from payments.models import Payment
from listings.models import Property
from accounts.models import CustomUser
from payments.views import simulate_payment_success
from django.test import RequestFactory
from django.contrib.auth.models import AnonymousUser


def test_simulation_endpoint():
    """Test the simulation endpoint directly"""
    print("🧪 Testing Payment Simulation Endpoint...")

    try:
        # Create test user
        user, created = CustomUser.objects.get_or_create(
            email='simulation_test@example.com',
            defaults={
                'first_name': 'Simulation',
                'last_name': 'Test',
                'phone_number': '+263789915032',
                'user_type': 'host'
            }
        )

        # Create test property
        property_obj, created = Property.objects.get_or_create(
            title='Simulation Test Property',
            owner=user,
            defaults={
                'listing_type': 'normal',
                'is_paid': False
            }
        )

        # Create test payment
        payment, created = Payment.objects.get_or_create(
            property=property_obj,
            defaults={
                'user': user,
                'listing_type': 'normal',
                'amount': 10.00,
                'reference': f'SIM-TEST-{property_obj.id}',
                'status': Payment.PENDING
            }
        )

        print(f"✅ Test setup complete:")
        print(f"   Property ID: {property_obj.id}")
        print(f"   Property is_paid: {property_obj.is_paid}")
        print(f"   Payment reference: {payment.reference}")
        print(f"   Payment status: {payment.status}")

        # Test simulation
        print(f"\n🔄 Testing simulation...")

        # Create a mock request
        factory = RequestFactory()
        request = factory.post(f'/payments/simulate/{payment.reference}/')
        request.user = AnonymousUser()

        # Call simulation endpoint
        from django.http import JsonResponse
        response = simulate_payment_success(request, payment.reference)

        # Check response
        if response.status_code == 200:
            print(f"✅ Simulation endpoint returned success")

            # Refresh objects from database
            payment.refresh_from_db()
            property_obj.refresh_from_db()

            print(f"✅ After simulation:")
            print(f"   Payment status: {payment.status}")
            print(f"   Property is_paid: {property_obj.is_paid}")

            if payment.status == Payment.PAID and property_obj.is_paid:
                print(f"🎉 SUCCESS! Property is_paid status correctly updated to True")
                return True
            else:
                print(f"❌ FAILED! Property is_paid status not updated correctly")
                return False
        else:
            print(f"❌ Simulation endpoint failed with status {response.status_code}")
            return False

    except Exception as e:
        print(f"❌ Test failed with exception: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_payment_complete_flow():
    """Test the complete payment flow after simulation"""
    print("\n🔄 Testing Complete Payment Flow...")

    try:
        # Get the test payment
        payment = Payment.objects.filter(reference__startswith='SIM-TEST-').first()
        if not payment:
            print("❌ No test payment found")
            return False

        property_obj = payment.property

        print(f"✅ Before payment complete:")
        print(f"   Payment status: {payment.status}")
        print(f"   Property is_paid: {property_obj.is_paid}")

        # Simulate payment complete request
        from django.test import RequestFactory
        from django.contrib.auth.models import AnonymousUser

        factory = RequestFactory()
        request = factory.get(f'/payments/complete/?reference={payment.reference}')
        request.user = AnonymousUser()

        # Import and call payment_complete view
        from payments.views import payment_complete
        response = payment_complete(request)

        # Refresh objects
        payment.refresh_from_db()
        property_obj.refresh_from_db()

        print(f"✅ After payment complete:")
        print(f"   Payment status: {payment.status}")
        print(f"   Property is_paid: {property_obj.is_paid}")
        print(f"   Response status: {response.status_code}")

        if property_obj.is_paid:
            print(f"🎉 SUCCESS! Payment complete flow works correctly")
            return True
        else:
            print(f"❌ FAILED! Payment complete flow didn't update property status")
            return False

    except Exception as e:
        print(f"❌ Payment complete test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def cleanup():
    """Clean up test data"""
    print("\n🧹 Cleaning up test data...")
    try:
        Property.objects.filter(title='Simulation Test Property').delete()
        CustomUser.objects.filter(email='simulation_test@example.com').delete()
        Payment.objects.filter(reference__startswith='SIM-TEST-').delete()
        print("✅ Test data cleaned up")
    except Exception as e:
        print(f"❌ Cleanup failed: {e}")


def main():
    """Run all simulation tests"""
    print("🚀 Testing Payment Simulation Flow")
    print("=" * 50)

    # Test simulation endpoint
    simulation_success = test_simulation_endpoint()

    # Test complete flow
    complete_success = test_payment_complete_flow()

    # Summary
    print("\n" + "=" * 50)
    print("📊 SIMULATION TEST RESULTS")
    print("=" * 50)

    if simulation_success and complete_success:
        print("🎉 SUCCESS! Payment simulation works perfectly.")
        print("✅ Property is_paid status is correctly updated to True")
        print("✅ Payment complete flow works correctly")
        print("\n📋 What happens when you click 'Simulate Success':")
        print("1. Payment status → PAID")
        print("2. Property is_paid → True")
        print("3. Redirect to success page")
        print("4. Listing becomes public")
    else:
        print("❌ Some tests failed. Check the output above for details.")

    # Cleanup
    cleanup()

    return simulation_success and complete_success


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)