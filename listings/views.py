from django.shortcuts import render, redirect
from .forms import  PropertyStep1Form, PropertyStep2Form, PropertyStep3Form, PropertyStep4Form

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
