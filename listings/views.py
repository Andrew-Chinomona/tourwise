from django.shortcuts import render, redirect
from .forms import  PropertyStep1Form

def add_property_step1(request):
    if request.method == 'POST':
        form = PropertyStep1Form(request.POST)
        if form.is_valid():
            request.session['property_type'] = form.cleaned_data['property_type']
            return redirect('add_property_step2')
    else:
        form = PropertyStep1Form()

    return render(request, 'listings/add_property_step1.html',{'form':'Form'})

# Create your views here.
