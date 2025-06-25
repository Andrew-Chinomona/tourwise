from django.contrib import messages
from django.shortcuts import render, redirect, get_object_or_404
from .forms import PropertyStep1Form, PropertyStep2Form, PropertyStep3Form, PropertyStep4Form, PropertyStep5Form, PropertyStep6Form, PropertyStep7Form, EditPropertyForm, PropertyStep8Form,PropertyStep9Form, ChoosePaymentForm
from .models import Property, PropertyImage
from payments.models import Payment
from django.contrib.auth.decorators import login_required

@login_required()   #create a blank property object and store ID in session
def start_property_listing(request):
    property_obj = Property.objects.create(
        owner=request.user,
        title='Untitled',
        is_paid=False
    )

    request.session['editing_property_id'] = property_obj.id

    return redirect('add_property_step1')

@login_required #select property type
def add_property_step1(request):
    property_id = request.session.get('editing_property_id')
    property_obj = get_object_or_404(Property, id=property_id, owner=request.user)

    if request.method == 'POST':
        form = PropertyStep1Form(request.POST)
        if form.is_valid():
            property_obj.property_type = form.cleaned_data['property_type']
            property_obj.save()
            return redirect('add_property_step2')
    else:
        form = PropertyStep1Form(initial={'property_type': property_obj.property_type})

    return render(request, 'listings/add_property_step1.html', {'form': form})

@login_required()   #add description
def add_property_step2(request):
    property_id = request.session.get('editing_property_id')
    property_obj = get_object_or_404(Property, id=property_id, owner=request.user)

    if request.method == 'POST':
        form = PropertyStep2Form(request.POST)
        if form.is_valid():
            property_obj.description = form.cleaned_data['description']
            property_obj.save()
            return redirect('add_property_step3')
    else:
        form = PropertyStep2Form(initial={'description': property_obj.description})

    return render(request, 'listings/add_property_step2.html', {'form': form})

@login_required()   #create city, suburb, street and call generate-title
def add_property_step3(request):
    property_id = request.session.get('editing_property_id')
    property_obj = get_object_or_404(Property, id=property_id, owner=request.user)

    if request.method == 'POST':
        form = PropertyStep3Form(request.POST)
        if form.is_valid():
            property_obj.city = form.cleaned_data['city']
            property_obj.suburb = form.cleaned_data['suburb']
            property_obj.street_address = form.cleaned_data['street_address']
            property_obj.save()
            property_obj.generate_title()

            return redirect('add_property_step4')
    else:
        #this will allow the user to resume and to see the current data saved in the DB
        form = PropertyStep3Form(initial={
            'city': property_obj.city,
            'suburb': property_obj.suburb,
            'street_address': property_obj.street_address
        })

    return render(request, 'listings/add_property_step3.html', {'form': form})

@login_required() #upload main image
def add_property_step4(request):
    property_id = request.session.get('editing_property_id')
    property_obj = get_object_or_404(Property, id=property_id, owner=request.user)

    if request.method == 'POST':
        form = PropertyStep4Form(request.POST, request.FILES)
        if form.is_valid():
            property_obj.main_image = form.cleaned_data['main_image']
            property_obj.save()
            return redirect('add_property_step5')  # Next step
    else:
        form = PropertyStep4Form()

    return render(request, 'listings/add_property_step4.html', {'form': form})

# @login_required()   #upload other images
# def add_property_step5(request):
#     property_id = request.session.get('editing_property_id')
#     property_obj = get_object_or_404(Property, id=property_id, owner=request.user)
#
#     if request.method == 'POST':
#         form = PropertyStep5Form(request.POST, request.FILES)
#         if form.is_valid():
#             images = request.FILES.getlist('images')
#
#             for image in images:
#                 PropertyImage.objects.create(property=property_obj, image=image)
#
#             return redirect('add_property_step6')  # Next step
#     else:
#         form = PropertyStep5Form()
#
#     return render(request, 'listings/add_property_step5.html', {'form': form})
@login_required()
def add_property_step5(request):
    property_id = request.session.get('editing_property_id')
    property_obj = get_object_or_404(Property, id=property_id, owner=request.user)

    if request.method == 'POST':
        form = PropertyStep5Form(request.POST, request.FILES)
        if form.is_valid():
            images = form.cleaned_data.get('images') or []

            # If images is a single file, wrap it in a list
            if not isinstance(images, list):
                images = [images]

            for image in images:
                PropertyImage.objects.create(property=property_obj, image=image)

            return redirect('add_property_step6')
    else:
        form = PropertyStep5Form()

    return render(request, 'listings/add_property_step5.html', {'form': form})


@login_required()   #set the price
def add_property_step6(request):
    property_id = request.session.get('editing_property_id')
    property_obj = get_object_or_404(Property, id=property_id, owner=request.user)

    if request.method == 'POST':
        form = PropertyStep6Form(request.POST)
        if form.is_valid():
            property_obj.price = form.cleaned_data['price']
            property_obj.save()
            return redirect('add_property_step7')
    else:
        form = PropertyStep6Form(initial={'price': property_obj.price})

    return render(request, 'listings/add_property_step6.html', {'form': form})


@login_required
def add_property_step7(request):
    property_id = request.session.get('editing_property_id')
    property_obj = get_object_or_404(Property, id=property_id, owner=request.user)

    if request.method == 'POST':
        form = PropertyStep7Form(request.POST)
        if form.is_valid():
            amenities = form.cleaned_data['amenities']
            property_obj.amenities.set(amenities)
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
        form = PropertyStep8Form(request.POST, request.FILES)
        if form.is_valid():
            property_obj.contact_info = form.cleaned_data['contact_name']
            property_obj.contact_phone = form.cleaned_data['contact_phone']
            property_obj.contact_email = form.cleaned_data['contact_email']

            if form.cleaned_data.get('profile_photo'):
                property_obj.profile_photo = form.cleaned_data['profile_photo']

            property_obj.save()
            return redirect('add_property_step9')  # Step 9: Features (bed/bath/area)
    else:
        form = PropertyStep8Form(initial={
            'contact_name': request.user.get_full_name() or request.user.username,
            'contact_phone': property_obj.contact_phone,
            'contact_email': property_obj.contact_email
        })

    return render(request, 'listings/add_property_step8.html', {'form': form})

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
            property_obj.save()
            return redirect('choose_payment')
    else:
        form = PropertyStep9Form(initial={
            'bedrooms': property_obj.bedrooms,
            'bathrooms': property_obj.bathrooms,
            'area': property_obj.area
        })

    return render(request, 'listings/add_property_step9.html', {'form': form})

@login_required
def choose_payment(request):
    property_id = request.session.get('editing_property_id')
    property_obj = get_object_or_404(Property, id=property_id, owner=request.user)

    if request.method == 'POST':
        form = ChoosePaymentForm(request.POST)
        if form.is_valid():
            listing_type = form.cleaned_data['listing_type']
            property_obj.listing_type = listing_type
            property_obj.is_paid = True
            property_obj.save()

            Payment.objects.create(
                property=property_obj,
                user=request.user,
                listing_type=listing_type,
                amount=20.00 if listing_type == 'priority' else 10.00,
                is_complete=True
            )

            request.session.pop('editing_property_id', None)
            return redirect('host_dashboard')

    else:
        form = ChoosePaymentForm(initial={'listing_type': property_obj.listing_type})

    return render(request, 'listings/choose_payment.html', {
        'form': form,
        'property': property_obj,
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
