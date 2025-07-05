from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.views.decorators.csrf import csrf_exempt
from django.http import HttpResponse, HttpResponseForbidden, Http404, JsonResponse
from .services import paynow_service
from .models import Payment
from listings.models import Property
from django.conf import settings
import logging

logger = logging.getLogger(__name__)


@login_required
def initiate_payment(request, property_id):
    property_obj = get_object_or_404(Property, id=property_id, owner=request.user)
    if property_obj.owner != request.user:
        return HttpResponseForbidden()

    # Check if user has phone number
    if not hasattr(request.user, 'phone_number') or not request.user.phone_number:
        return render(request, 'payments/payment_error.html', {
            'error_message': 'Phone number is required for payment. Please update your profile.'
        })

    service = paynow_service

    try:
        response = service.create_payment(property_obj, request.user)
    except ValueError as e:
        return render(request, 'payments/payment_error.html', {
            'error_message': str(e)
        })
    except Exception as e:
        return render(request, 'payments/payment_error.html', {
            'error_message': 'Payment initiation failed. Please try again.'
        })

    if response and response.success:
        # Get the payment object to pass to template
        payment = Payment.objects.get(property=property_obj)
        return render(request, 'payments/payment_instructions.html', {
            'poll_url': response.poll_url,
            'instructions': response.instructions,
            'payment': payment
        })

    return render(request, 'payments/payment_error.html', {
        'error_message': 'Payment initiation failed. Please try again.'
    })


@login_required
def payment_complete(request):
    reference = request.GET.get('reference')
    if reference:
        try:
            payment = Payment.objects.get(reference=reference)

            # Check if payment is already paid (from simulation or real payment)
            if payment.status == Payment.PAID:
                # Ensure property is marked as paid
                if not payment.property.is_paid:
                    payment.property.is_paid = True
                    payment.property.save()
                    logger.info(f"Payment complete: Property {payment.property.id} marked as paid")

                return render(request, 'payments/payment_success.html')

            # If not paid, check with Paynow service
            service = paynow_service
            if service.check_payment_status(payment):
                return render(request, 'payments/payment_success.html')

        except Payment.DoesNotExist:
            return render(request, 'payments/payment_failed.html')

    return render(request, 'payments/payment_failed.html')


@csrf_exempt
def payment_update(request):
    # Handle Paynow webhook
    if request.method == 'POST':
        reference = request.POST.get('reference')
        if reference:
            try:
                payment = Payment.objects.get(reference=reference)
            except Payment.DoesNotExist:
                return HttpResponse(status=404)
            service = paynow_service
            service.check_payment_status(payment)
    return HttpResponse(status=200)


@csrf_exempt
def payment_status(request, reference):
    """API endpoint to check payment status for frontend polling"""
    try:
        payment = Payment.objects.get(reference=reference)
        service = paynow_service

        if service.check_payment_status(payment):
            return JsonResponse({'status': 'paid', 'paid': True})
        else:
            return JsonResponse({'status': 'pending', 'paid': False})
    except Payment.DoesNotExist:
        return JsonResponse({'status': 'not_found', 'paid': False}, status=404)
    except Exception as e:
        return JsonResponse({'status': 'error', 'paid': False}, status=500)


@csrf_exempt
def simulate_payment_success(request, reference):
    """Development endpoint to simulate successful payment"""
    if not settings.DEBUG:
        return JsonResponse({'error': 'Simulation only available in development mode'}, status=403)

    try:
        payment = Payment.objects.get(reference=reference)

        # Update payment status
        payment.status = Payment.PAID
        payment.save()

        # Update property status
        property_obj = payment.property
        property_obj.is_paid = True
        property_obj.save()

        logger.info(f"DEVELOPMENT: Simulated successful payment for {reference}")

        return JsonResponse({
            'status': 'success',
            'message': 'Payment simulated successfully',
            'payment_status': 'paid',
            'property_paid': True
        })

    except Payment.DoesNotExist:
        return JsonResponse({'error': 'Payment not found'}, status=404)
    except Exception as e:
        logger.error(f"Error simulating payment: {e}")
        return JsonResponse({'error': 'Simulation failed'}, status=500)

