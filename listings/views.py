from django.shortcuts import render, redirect
from .forms import  PropertyStep1Form, PropertyStep2Form, PropertyStep3Form, PropertyStep4Form, PropertyStep5Form, PropertyStep6Form

def add_property_step1(request):
    if request.method == 'POST':
        form = PropertyStep1Form(request.POST)
        if form.is_valid():
            request.session['property_type'] = form.cleaned_data['property_type']
            return redirect('add_property_step2')
    else:
        form = PropertyStep1Form()

    return render(request, 'listings/add_property_step1.html',{'form':'Form'})

# Step 2: Property description view
def add_property_step2(request):
    if request.method == 'POST':
        form = PropertyStep2Form(request.POST)

        if form.is_valid():
            request.session['description'] = form.cleaned_data['description']

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
    if request.method == 'POST':
        # Bind POST and FILES to the form
        form = PropertyStep5Form(request.POST, request.FILES)

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

# Step 6: Final confirmation and save
def add_property_step6(request):
    if request.method == 'POST':
        form = PropertyStep6Form(request.POST)

        if form.is_valid():
            # Collect all data from session
            user = request.user
            title = "Listing by " + user.username  # Default title, can improve later
            property_type = request.session.get('property_type')
            description = request.session.get('description')
            facilities = request.session.get('facilities')
            services = request.session.get('services', '')
            notes = form.cleaned_data['additional_notes']
            price = 0  # default or update in dashboard later
            location = "Unknown"  # placeholder, refine later
            contact_info = user.phone_number if hasattr(user, 'phone_number') else "Not provided"

            # Create the Property
            property_obj = Property.objects.create(
                owner=user,
                title=title,
                property_type=property_type,
                description=description,
                facilities=facilities,
                services=services,
                additional_notes=notes,
                price=price,
                location=location,
                contact_info=contact_info,
            )

            # Attach the main image
            if 'main_image_name' in request.session:
                main_img = request.FILES.get('main_image')
                if main_img:
                    property_obj.main_image = main_img
                    property_obj.save()

            # Save interior photos
            for img in request.FILES.getlist('images'):
                PropertyImage.objects.create(
                    property=property_obj,
                    image=img
                )

            # ✅ Redirect to a confirmation or dashboard page
            return redirect('host_dashboard')  # update route if needed

    else:
        form = PropertyStep6Form()

    return render(request, 'listings/add_property_step6.html', {'form': form})
