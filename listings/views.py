from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.shortcuts import render, redirect, get_object_or_404
from .forms import PropertyStep1Form, PropertyStep2Form, PropertyStep3Form, PropertyStep4Form, PropertyStep5Form, \
    PropertyStep6Form, PropertyStep7Form, PropertyStep8Form, EditPropertyForm
from .models import Property, PropertyImage
from payments.models import Payment

def add_property_step1(request):
    form = PropertyStep1Form(request.POST or None)
    if request.method == 'POST':
        form = PropertyStep1Form(request.POST)
        if form.is_valid():
            request.session['property_type'] = form.cleaned_data['property_type']
            return redirect('add_property_step2')
    else:
        form = PropertyStep1Form()

    return render(request, 'listings/add_property_step1.html',{'form':form})

# Step 2: Property description view
def add_property_step2(request):
    if request.method == 'POST':
        form = PropertyStep2Form(request.POST)

        if form.is_valid():
            request.session['title'] = form.cleaned_data['title']

            return redirect('add_property_step3')
    else:
        form = PropertyStep2Form()

    # Render the form inside a template
    return render(request, 'listings/add_property_step2.html', {'form': form})

# Step 3: Facilities selection view
def add_property_step3(request):
    if request.method == 'POST':
        form = PropertyStep3Form(request.POST)

        if form.is_valid():
            # Get selected facilities and convert to comma-separated string
            facilities = ', '.join(form.cleaned_data['facilities'])

            # Save to session
            request.session['facilities'] = facilities

            # Redirect to add images
            return redirect('add_property_step4')
    else:
        # If it's a GET request, show a blank form
        form = PropertyStep3Form()

    return render(request, 'listings/add_property_step3.html', {'form': form})

def add_property_step4(request):
    if request.method == 'POST':
        # Include both form data and file uploads
        form = PropertyStep4Form(request.POST, request.FILES)

        if form.is_valid():
            # Save image temporarily in session (we’ll store to DB in final step)
            image = form.cleaned_data['main_image']
            request.session['main_image_name'] = image.name

            # Optional: Store marker for later file handling
            request.session['main_image_uploaded'] = True

            # Redirect to Step 5
            return redirect('add_property_step5')
    else:
        # Display empty form
        form = PropertyStep4Form()

    return render(request, 'listings/add_property_step4.html', {'form': form})


def add_property_step5(request):
    form = PropertyStep5Form()
    if request.method == 'POST':
        print(request.FILES)
        # Bind POST and FILES to the form
        form = PropertyStep5Form(request.FILES)
        if form.is_valid():
            # Store list of uploaded file names in session
            request.session['interior_image_names'] = [
                img.name for img in request.FILES.getlist('images')
            ]

            # Mark that extra images were uploaded
            request.session['interior_images_uploaded'] = True

            # Redirect to final step
            return redirect('add_property_step6')
    else:
        # Show a blank form on GET
        form = PropertyStep5Form()

    return render(request, 'listings/add_property_step5.html', {'form': form})

from .models import Property, PropertyImage

def add_property_step6(request):
    if request.method == 'POST':
        form = PropertyStep6Form(request.POST)

        if form.is_valid():
            request.session['description'] = form.cleaned_data['description']
            return redirect('add_property_step7')
    else:
        form = PropertyStep6Form()

    return render(request, 'listings/add_property_step6.html', {'form': form})

def add_property_step7(request):
    if request.method == 'POST':
        form = PropertyStep7Form(request.POST)
        if form.is_valid():
            request.session['price'] = str(form.cleaned_data['price'])
            return redirect('add_property_step8')
    else:
        form = PropertyStep7Form()

    return render(request, 'listings/add_property_step7.html', {'form': form})

def add_property_step8(request):
    if request.method == 'POST':
        form = PropertyStep8Form(request.POST)
        if form.is_valid():
            full_location = f"{form.cleaned_data['street_address']},{form.cleaned_data['suburb']}, {form.cleaned_data['city']}"
            request.session['location'] = full_location
            return redirect('choose_payment')
    else:
        form = PropertyStep8Form()

    return render(request, 'listings/add_property_step8.html', {'form': form})

def choose_payment(request):
    if request.method == 'POST':
        listing_type = request.POST.get('listing_type')
        if listing_type not in ['normal', 'priority']:
            return render(request, 'listings/choose_payment.html',{'error':'Please choose a valid listing type'})


        user = request.user
        title = request.session.get('title')
        property_type = request.session.get('property_type')
        description = request.session.get('description')
        facilities = request.session.get('facilities')
        #services = request.session.get('services', '')
        #notes = request.session.get('additional_notes')
        price = request.session.get('price')
        location = request.session.get('location')
        contact_info = user.phone_number if hasattr(user, 'phone_number') else "Not provided"

        property_obj = Property.objects.create(
            owner=user,
            #title=f"Listing by {user.username}",
            title = title,
            property_type=property_type,
            description=description,
            facilities=facilities,
            #services=services,
            #additional_notes=notes,
            price=price,
            location=location,
            contact_info=contact_info,
            listing_type=listing_type,
            is_paid=True
        )

        for img in request.FILES.getlist('images'):
            PropertyImage.objects.create(property=property_obj, main_image=img)

        amount = 10.00 if listing_type == 'normal' else 20.00
        Payment.objects.create(
            property=property_obj,
            user=user,
            listing_type=listing_type,
            amount=amount,
            is_complete=True
        )

        return redirect('host_dashboard')

    return render(request, 'listings/choose_payment.html')

@login_required()
def edit_listing(request, property_id):
    property_obj = get_object_or_404(Property, id=property_id, owner=request.user)

    if request.method == 'POST':
        form = EditPropertyForm(request.POST, request.FILES,instance=property_obj)

        if form.is_valid():
            form.save()
            messages.success(request, "Listing updated successfully.")
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
