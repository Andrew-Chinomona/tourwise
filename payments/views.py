from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.views.decorators.csrf import csrf_exempt
from django.http import HttpResponse
from .services import paynow_service
from .models import Payment
from listings.models import Property


@login_required
def initiate_payment(request, property_id):
    property_obj = Property.objects.get(id=property_id)
    service = paynow_service

    response = service.create_payment(property_obj, request.user)

    if response and response.success:
        return render(request, 'payments/payment_instructions.html', {
            'poll_url': response.poll_url,
            'instructions': response.instructions
        })

    return render(request, 'payments/payment_error.html')


@login_required
def payment_complete(request):
    reference = request.GET.get('reference')
    if reference:
        payment = Payment.objects.get(reference=reference)
        service = paynow_service

        if service.check_payment_status(payment):
            payment.property.is_paid = True
            payment.property.save()
            return render(request, 'payments/payment_success.html')

    return render(request, 'payments/payment_failed.html')


@csrf_exempt
def payment_update(request):
    # Handle Paynow webhook
    if request.method == 'POST':
        reference = request.POST.get('reference')
        if reference:
            payment = Payment.objects.get(reference=reference)
            service = paynow_service
            service.check_payment_status(payment)
    return HttpResponse(status=200)