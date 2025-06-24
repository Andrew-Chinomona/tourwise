from django.contrib import messages
from django.shortcuts import render, redirect, get_object_or_404
from .forms import PropertyStep1Form, PropertyStep2Form, PropertyStep3Form, PropertyStep4Form, PropertyStep5Form, PropertyStep6Form
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

@login_required()   #upload other images
def add_property_step5(request):
    property_id = request.session.get('editing_property_id')
    property_obj = get_object_or_404(Property, id=property_id, owner=request.user)

    if request.method == 'POST':
        form = PropertyStep5Form(request.POST, request.FILES)
        if form.is_valid():
            images = request.FILES.getlist('images')

            for image in images:
                PropertyImage.objects.create(property=property_obj, image=image)

            return redirect('add_property_step6')  # Next step
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


# @login_required()
# def edit_listing(request, property_id):
#     property_obj = get_object_or_404(Property, id=property_id, owner=request.user)
#     if request.method == 'POST':
#         form = EditPropertyForm(request.POST, request.FILES, instance=property_obj)
#         if form.is_valid():
#             form.save()
#             messages.success(request, "Listing updated successfully.")
#             return redirect('host_dashboard')
#     else:
#         form = EditPropertyForm(instance=property_obj)
#     return render(request, 'listings/edit_listing.html', {'form': form, 'property': property_obj})

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
