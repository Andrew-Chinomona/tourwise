from django.contrib import messages
from django.shortcuts import render, redirect, get_object_or_404
from .forms import PropertyStep1Form, PropertyStep2Form, PropertyStep3Form, PropertyStep4Form, PropertyStep5Form, PropertyStep6Form, PropertyStep7Form, EditPropertyForm, PropertyStep8Form,PropertyStep9Form, ChoosePaymentForm
from .models import Property, PropertyImage
from payments.models import Payment
from django.contrib.auth.decorators import login_required
from django.utils import timezone
from datetime import timedelta
from django.conf import settings
from django.http import JsonResponse
from django.db.models import Q

@login_required()
def start_property_listing(request):
    # Always start fresh
    property_obj = Property.objects.create(
        owner=request.user,
        title='Untitled',
        is_paid=False,
        current_step=1
    )

    request.session['editing_property_id'] = property_obj.id
    return redirect('add_property_step1')



@login_required
def add_property_step1(request):
    property_id = request.session.get('editing_property_id')
    property_obj = get_object_or_404(Property, id=property_id, owner=request.user)

    if request.method == 'POST':
        form = PropertyStep1Form(request.POST)
        if form.is_valid():
            property_obj.property_type = form.cleaned_data['property_type']
            property_obj.current_step = 1
            property_obj.save()
            return redirect('add_property_step2')
    else:
        form = PropertyStep1Form(initial={'property_type': property_obj.property_type})

    return render(request, 'listings/add_property_step1.html', {
        'form': form,
        'property': property_obj
    })

@login_required()
def add_property_step2(request):
    property_id = request.session.get('editing_property_id')
    property_obj = get_object_or_404(Property, id=property_id, owner=request.user)

    if request.method == 'POST':
        form = PropertyStep2Form(request.POST)
        if form.is_valid():
            property_obj.description = form.cleaned_data['description']
            property_obj.current_step = 2
            property_obj.save()
            return redirect('add_property_step3')
    else:
        form = PropertyStep2Form(initial={'description': property_obj.description})

    return render(request, 'listings/add_property_step2.html', {
        'form': form,
        'property': property_obj
    })

@login_required()
def add_property_step3(request):
    property_id = request.session.get('editing_property_id')
    property_obj = get_object_or_404(Property, id=property_id, owner=request.user)

    if request.method == 'POST':
        form = PropertyStep3Form(request.POST)
        if form.is_valid():
            property_obj.city = form.cleaned_data['city']
            property_obj.suburb = form.cleaned_data['suburb']
            property_obj.street_address = form.cleaned_data['street_address']
            property_obj.latitude = form.cleaned_data.get('latitude')
            property_obj.longitude = form.cleaned_data.get('longitude')
            # property_obj.save()
            property_obj.generate_title()
            property_obj.current_step = 3
            property_obj.save()
            return redirect('add_property_step4')
    else:
        form = PropertyStep3Form(initial={
            'city': property_obj.city,
            'suburb': property_obj.suburb,
            'street_address': property_obj.street_address,
            'latitude': property_obj.latitude,
            'longitude': property_obj.longitude,
        })

    return render(request, 'listings/add_property_step3.html', {
        'form': form,
        'property': property_obj,
        'OPEN_CAGE_API_KEY': settings.OPENCAGE_API_KEY
    })


@login_required()
def add_property_step4(request):
    property_id = request.session.get('editing_property_id')
    property_obj = get_object_or_404(Property, id=property_id, owner=request.user)

    if request.method == 'POST':
        form = PropertyStep4Form(request.POST, request.FILES)
        if form.is_valid():
            property_obj.main_image = form.cleaned_data['main_image']
            property_obj.current_step = 4
            property_obj.save()
            return redirect('add_property_step5')
    else:
        form = PropertyStep4Form()

    return render(request, 'listings/add_property_step4.html', {
        'form': form,
        'property': property_obj
    })
@login_required()
def add_property_step5(request):
    property_id = request.session.get('editing_property_id')
    property_obj = get_object_or_404(Property, id=property_id, owner=request.user)

    if request.method == 'POST':
        form = PropertyStep5Form(request.POST, request.FILES)
        if form.is_valid():
            images = request.FILES.getlist('images')

            if not images:
                form.add_error('images', 'Please upload at least one image.')
            else:
                for image in images:
                    PropertyImage.objects.create(property=property_obj, image=image)
                    property_obj.current_step = 5
                return redirect('add_property_step6')
    else:
        form = PropertyStep5Form()

    return render(request, 'listings/add_property_step5.html', {
        'form': form,
        'property': property_obj
    })

from listings.models import Currency  # Make sure you import this

@login_required
def add_property_step6(request):
    property_id = request.session.get('editing_property_id')
    property_obj = get_object_or_404(Property, id=property_id, owner=request.user)

    if request.method == 'POST':
        form = PropertyStep6Form(request.POST)
        if form.is_valid():
            property_obj.price = form.cleaned_data['price']
            property_obj.currency = form.cleaned_data['currency']
            property_obj.current_step = 6
            property_obj.save()
            return redirect('add_property_step7')
    else:
        form = PropertyStep6Form(initial={
            'price': property_obj.price,
            'currency': property_obj.currency
        })

    return render(request, 'listings/add_property_step6.html', {
        'form': form,
        'property': property_obj
    })



@login_required
def add_property_step7(request):
    property_id = request.session.get('editing_property_id')
    property_obj = get_object_or_404(Property, id=property_id, owner=request.user)

    if request.method == 'POST':
        form = PropertyStep7Form(request.POST)
        if form.is_valid():
            amenities = form.cleaned_data['amenities']
            property_obj.amenities.set(amenities)
            property_obj.current_step = 7
            return redirect('add_property_step8')
    else:
        form = PropertyStep7Form(initial={
            'amenities': property_obj.amenities.all()
        })

    return render(request, 'listings/add_property_step7.html', {'form': form})

@login_required
def add_property_step8(request):
    property_id = request.session.get('editing_property_id')
    property_obj = get_object_or_404(Property, id=property_id, owner=request.user)

    if request.method == 'POST':
        form = PropertyStep8Form(request.POST, request.FILES, user=request.user, property_obj=property_obj)
        if form.is_valid():
            property_obj.contact_name = form.cleaned_data['contact_name']
            property_obj.contact_phone = form.cleaned_data['contact_phone']
            property_obj.contact_email = form.cleaned_data['contact_email']
            property_obj.current_step = 8
            property_obj.save()
            return redirect('add_property_step9')
    else:
        form = PropertyStep8Form(user=request.user, property_obj=property_obj)

    return render(request, 'listings/add_property_step8.html', {
        'form': form,
        'property': property_obj
    })


@login_required
def add_property_step9(request):
    property_id = request.session.get('editing_property_id')
    property_obj = get_object_or_404(Property, id=property_id, owner=request.user)

    if request.method == 'POST':
        form = PropertyStep9Form(request.POST)
        if form.is_valid():
            property_obj.bedrooms = form.cleaned_data['bedrooms']
            property_obj.bathrooms = form.cleaned_data['bathrooms']
            property_obj.area = form.cleaned_data['area']
            property_obj.current_step = 9
            property_obj.save()
            return redirect('choose_payment')
    else:
        form = PropertyStep9Form(initial={
            'bedrooms': property_obj.bedrooms,
            'bathrooms': property_obj.bathrooms,
            'area': property_obj.area
        })

    return render(request, 'listings/add_property_step9.html', {
        'form': form,
        'property': property_obj
    })

from payments.services import paynow_service

@login_required
def choose_payment(request):
    property_id = request.session.get('editing_property_id')
    property_obj = get_object_or_404(Property, id=property_id, owner=request.user)

    if request.method == 'POST':
        form = ChoosePaymentForm(request.POST)
        if form.is_valid():
            listing_type = form.cleaned_data['listing_type']

            # Save listing type (without setting is_paid)
            property_obj.listing_type = listing_type
            property_obj.save()

            # Create Paynow payment
            service = paynow_service
            response = service.create_payment(property_obj, request.user)

            if response and response.success:
                return render(request, 'payments/payment_instructions.html', {
                    'poll_url': response.poll_url,
                    'instructions': response.instructions
                })

            return render(request, 'payments/payment_error.html')

    else:
        form = ChoosePaymentForm(initial={'listing_type': property_obj.listing_type})
        property_obj.current_step = 10
        property_obj.save()

    return render(request, 'listings/choose_payment.html', {
        'form': form,
        'property': property_obj,
        'latitude': property_obj.latitude,
        'longitude': property_obj.longitude,
    })


@login_required()
def edit_listing(request, property_id):
    property_obj = get_object_or_404(Property, id=property_id, owner=request.user)
    if request.method == 'POST':
        form = EditPropertyForm(request.POST, request.FILES, instance=property_obj)
        if form.is_valid():
            form.save()
            # messages.success(request, "Listing updated successfully.")
            return redirect('host_dashboard')
    else:
        form = EditPropertyForm(instance=property_obj)
    return render(request, 'listings/edit_listing.html', {'form': form, 'property': property_obj})

@login_required()
def delete_listing(request, property_id):
    property_obj = get_object_or_404(Property, id=property_id, owner=request.user)
    if request.method == 'POST':
        property_obj.delete()
        messages.success(request, "Listing deleted successfully.")
        return redirect('host_dashboard')
    return render(request, 'listings/delete_listing.html', {'property': property_obj})

@login_required
def delete_property_image(request, image_id):
    image = get_object_or_404(PropertyImage, id=image_id, property__owner=request.user)
    image.delete()
    return redirect('edit_listing', property_id=image.property.id)

@login_required
def upload_property_images(request, property_id):
    property_obj = get_object_or_404(Property, id=property_id, owner=request.user)
    if request.method == 'POST':
        for img in request.FILES.getlist('images'):
            PropertyImage.objects.create(property=property_obj, image=img)
    return redirect('edit_listing', property_id=property_id)

@login_required
def upload_main_image(request, property_id):
    property_obj = get_object_or_404(Property, id=property_id, owner=request.user)
    if request.method == 'POST' and 'main_image' in request.FILES:
        property_obj.main_image = request.FILES['main_image']
        property_obj.save()
    return redirect('edit_listing', property_id=property_id)

@login_required
def upload_profile_photo(request, property_id):
    property_obj = get_object_or_404(Property, id=property_id, owner=request.user)
    if request.method == 'POST' and 'profile_photo' in request.FILES:
        property_obj.profile_photo = request.FILES['profile_photo']
        property_obj.save()
    return redirect('edit_listing', property_id=property_id)

def property_detail(request, pk):
    property_obj = get_object_or_404(Property, pk=pk)

    interior_images = PropertyImage.objects.filter(property=property_obj)
    amenities = property_obj.amenities.all()

    return render(request, 'listings/property_detail.html', {
        'property': property_obj,
        'interior_images': interior_images,
        'amenities': amenities,
        'latitude': property_obj.latitude,
        'longitude': property_obj.longitude,
    })

def recent_listings_view(request):
    two_weeks_ago = timezone.now() - timedelta(weeks=2)
    recent_properties =  Property.objects.filter(is_paid=True,created_at__gte=two_weeks_ago).order_by('-created_at')
    return render(request, 'listings/recent_listings.html', {'properties': recent_properties, 'title': 'Recent Listings'})


def featured_listings_view(request):
    featured_properties =list(Property.objects.filter(is_paid=True,  listing_type = 'priority').order_by('-created_at'))

    if len(featured_properties) < 10:
        fallback = Property.objects.filter(listing_type = 'normal').order_by('-created_at')[:10 - len(featured_properties)]
        featured_properties += list(fallback)

    return render(request, 'listings/featured_listings.html', {'properties': featured_properties, 'title': 'Featured Listings'})

def location_suggestions(request):
    query = request.GET.get('q', '').strip()

    if not query:
        return JsonResponse([], safe=False)

    matches = Property.objects.filter(
        Q(city__icontains=query) | Q(suburb__icontains=query)
    ).values_list('city', 'suburb')

    # Use a set to avoid duplicate strings
    suggestions = set()
    for city, suburb in matches:
        if query.lower() in city.lower():
            suggestions.add(city.strip())
        if suburb and query.lower() in suburb.lower():
            suggestions.add(suburb.strip())

    return JsonResponse(sorted(suggestions), safe=False)


@login_required
def resume_listing(request, property_id):
    property_obj = get_object_or_404(Property, id=property_id, owner=request.user, is_paid=False)

    request.session['editing_property_id'] = property_id
    step = property_obj.current_step

    step_redirects = {
        1: 'add_property_step1',
        2: 'add_property_step2',
        3: 'add_property_step3',
        4: 'add_property_step4',
        5: 'add_property_step5',
        6: 'add_property_step6',
        7: 'add_property_step7',
        8: 'add_property_step8',
        9: 'add_property_step9',
        10: 'choose_payment',
    }

    return redirect(step_redirects.get(step, 'add_property_step1'))

@login_required
def delete_draft_listing(request, property_id):
    property_obj = get_object_or_404(Property, id=property_id, owner=request.user, is_paid=False)

    if request.method == 'POST':
        property_obj.delete()
        messages.success(request, "Draft listing deleted.")
        return redirect('host_dashboard')

    return render(request, 'listings/delete_draft_confirm.html', {'property': property_obj})


