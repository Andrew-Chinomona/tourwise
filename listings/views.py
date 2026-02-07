from django.contrib import messages
from django.shortcuts import render, redirect, get_object_or_404
from .forms import ChoosePaymentForm, PropertyListingForm, EditPropertyForm
from .models import Property, PropertyImage
from payments.models import Payment
from django.contrib.auth.decorators import login_required
from django.utils import timezone
from datetime import timedelta
from django.conf import settings
from django.http import JsonResponse
from django.db.models import Q
from django.contrib.gis.geos import Point
from django.db import transaction


# ==================== UNIFIED SINGLE-PAGE FORM ====================

@login_required
def add_property_listing(request):
    """
    Unified single-page property listing form.
    Replaces the 10-step wizard with a streamlined single-page experience.
    """
    if request.method == 'POST':
        form = PropertyListingForm(request.POST, request.FILES, user=request.user)
        
        if form.is_valid():
            try:
                with transaction.atomic():
                    # Create property instance
                    property_obj = form.save(commit=False)
                    property_obj.owner = request.user
                    property_obj.is_paid = False  # Draft until payment
                    
                    # Generate title based on property type and location
                    if property_obj.property_type and form.cleaned_data.get('suburb'):
                        property_obj.title = f"{property_obj.property_type.title()} in {form.cleaned_data['suburb'].title()}"
                        if form.cleaned_data.get('city'):
                            property_obj.title += f" ({form.cleaned_data['city'].title()})"
                    
                    property_obj.save()
                    
                    # Handle interior images
                    interior_images = request.FILES.getlist('interior_images')
                    for image_file in interior_images:
                        PropertyImage.objects.create(
                            property=property_obj,
                            image=image_file
                        )
                    
                    # Save many-to-many relationships
                    form.save_m2m()
                    
                    # Store property ID in session for payment
                    request.session['editing_property_id'] = property_obj.id
                    
                    messages.success(request, 'Property listing created successfully! Please choose your listing type.')
                    return redirect('choose_payment')
                    
            except Exception as e:
                messages.error(request, f'Error creating listing: {str(e)}')
        else:
            messages.error(request, 'Please correct the errors below.')
    else:
        form = PropertyListingForm(user=request.user)
    
    context = {
        'form': form,
    }
    return render(request, 'listings/add_property_listing.html', context)


@login_required
def edit_draft_listing(request, property_id):
    """
    Edit an unpaid draft listing.
    Allows users to modify their draft properties before payment.
    """
    property_obj = get_object_or_404(
        Property, 
        id=property_id, 
        owner=request.user,
        is_paid=False  # Only allow editing unpaid drafts
    )
    
    if request.method == 'POST':
        form = PropertyListingForm(
            request.POST, 
            request.FILES, 
            instance=property_obj,
            user=request.user
        )
        
        if form.is_valid():
            try:
                with transaction.atomic():
                    property_obj = form.save(commit=False)
                    
                    # Update title if needed
                    if property_obj.property_type and form.cleaned_data.get('suburb'):
                        property_obj.title = f"{property_obj.property_type.title()} in {form.cleaned_data['suburb'].title()}"
                        if form.cleaned_data.get('city'):
                            property_obj.title += f" ({form.cleaned_data['city'].title()})"
                    
                    property_obj.save()
                    
                    # Handle new interior images (don't delete old ones)
                    interior_images = request.FILES.getlist('interior_images')
                    for image_file in interior_images:
                        PropertyImage.objects.create(
                            property=property_obj,
                            image=image_file
                        )
                    
                    # Save many-to-many relationships
                    form.save_m2m()
                    
                    # Store property ID in session for payment
                    request.session['editing_property_id'] = property_obj.id
                    
                    messages.success(request, 'Draft updated successfully! Please choose your listing type.')
                    return redirect('choose_payment')
                    
            except Exception as e:
                messages.error(request, f'Error updating listing: {str(e)}')
        else:
            messages.error(request, 'Please correct the errors below.')
    else:
        # Pre-populate form with existing data
        initial_data = {
            'city_suburb': f"{property_obj.suburb}, {property_obj.city}" if property_obj.suburb and property_obj.city else property_obj.suburb or property_obj.city,
            'latitude': property_obj.location.y if property_obj.location else None,
            'longitude': property_obj.location.x if property_obj.location else None,
        }
        form = PropertyListingForm(
            instance=property_obj,
            initial=initial_data,
            user=request.user
        )
    
    context = {
        'form': form,
        'editing': True,
        'property': property_obj,
    }
    return render(request, 'listings/add_property_listing.html', context)


# ==================== LEGACY REDIRECT VIEW ====================

@login_required()
def start_property_listing(request):
    """Redirect old multi-step form URL to new single-page form"""
    return redirect('add_property_listing')

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

            return redirect('initiate_payment', property_id=property_obj.id)
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
    property_obj = get_object_or_404(Property, pk=pk, is_paid=True)  # Only show paid listings

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
    featured_properties = list(Property.objects.filter(is_paid=True, listing_type='priority').order_by('-created_at'))

    if len(featured_properties) < 10:
        fallback = Property.objects.filter(is_paid=True, listing_type='normal').order_by('-created_at')[:10 - len(featured_properties)]
        featured_properties += list(fallback)

    return render(request, 'listings/featured_listings.html', {'properties': featured_properties, 'title': 'Featured Listings'})

def location_suggestions(request):
    """
    Enhanced location autocomplete with Zimbabwe priority
    Returns structured JSON with location details after minimum 2 characters
    """
    query = request.GET.get('q', '').strip()

    # Require minimum 2 characters
    if len(query) < 2:
        return JsonResponse({'suggestions': []})

    # Query database for Zimbabwe properties first (high priority)
    zim_matches = Property.objects.filter(
        Q(city__icontains=query) | Q(suburb__icontains=query),
        country__iexact='Zimbabwe',
        is_paid=True
    ).values('city', 'suburb', 'country').distinct()

    # Build suggestions with Zimbabwe priority
    suggestions = []
    seen = set()

    for match in zim_matches:
        city = match.get('city', '').strip()
        suburb = match.get('suburb', '').strip()
        
        # Create unique location strings
        if suburb and city:
            display = f"{suburb}, {city}, Zimbabwe"
        elif city:
            display = f"{city}, Zimbabwe"
        else:
            continue
        
        if display not in seen:
            suggestions.append({
                'display_name': display,
                'city': city,
                'suburb': suburb if suburb else '',
                'country': 'Zimbabwe',
                'priority': 1
            })
            seen.add(display)

    # Limit to top 10 suggestions
    return JsonResponse({'suggestions': suggestions[:10]})


@login_required
def delete_draft_listing(request, property_id):
    property_obj = get_object_or_404(Property, id=property_id, owner=request.user, is_paid=False)

    if request.method == 'POST':
        property_obj.delete()
        messages.success(request, "Draft listing deleted.")
        return redirect('host_dashboard')

    return render(request, 'listings/delete_draft_confirm.html', {'property': property_obj})


