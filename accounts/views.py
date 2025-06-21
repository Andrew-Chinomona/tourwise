from django.contrib.auth.forms import AuthenticationForm
from django.db.models.fields import return_None
from django.shortcuts import render, redirect
from django.contrib.auth import login, logout, authenticate

from listings.models import PropertyImage
from .forms import SignupForm
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse
from listings.models import Property, PropertyImage

#this will create the signup view and will save the user in the database and will redirectr the user depending on
#which type of user they are
def signup_view(request):
    if request.method == 'POST':
        form = SignupForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)

            if user.user_type == 'host':
                return redirect('host_dashboard')
            else:
                return redirect('home')

    else:
        form = SignupForm()

    # Render the signup page with the form
    #basically combining the template and the form
    return render(request, 'accounts/signup.html', {'form': form})


#This section will handle user login
def login_view(request):
    if request.method == 'POST':
        form = AuthenticationForm(data=request.POST)
        if form.is_valid():
            user = form.get_user()
            login(request, user)

            if user.user_type == 'host':
                return redirect('host_dashboard')
            else:
                return redirect('home')
    else:
        form = AuthenticationForm()

    return render(request, 'accounts/login.html', {'form': form})


#this section will handle logout
def logout_view(request):
    logout(request)
    return redirect('home')

def home_view(request):
    return render(request, 'accounts/home.html')

#this is the host dashboard and it will show all the of the hosts' lisitings and CRUD operations
@login_required()
def host_dashboard(request):
    if request.user.user_type != 'host':
        redirect('home')

    my_properties = Property.objects.filter(owner=request.user)
    return render(request, 'accounts/host_dashboard.html', {'properties': my_properties})
