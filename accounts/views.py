from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth import login, logout, authenticate,get_backends
from django.contrib.auth.decorators import login_required
from listings.models import Property, PropertyImage
from django.shortcuts import render, redirect
from .forms import SignupForm, CustomLoginForm, ProfilePhotoForm
from django.utils import timezone
from datetime import timedelta

def signup_view(request):
    if request.method == 'POST':
        form = SignupForm(request.POST)
        if form.is_valid():
            user = form.save(commit=False)
            user.username = f"{user.first_name} {user.last_name}"
            user.save()

            # Set backend explicitly
            user.backend = 'accounts.backends.EmailOrPhoneBackend'

            login(request, user)

            if user.user_type == 'host':
                return redirect('host_dashboard')
            else:
                return redirect('home')
    else:
        form = SignupForm()

    return render(request, 'accounts/signup.html', {'form': form})



def login_view(request):
    form = CustomLoginForm(request.POST or None)
    error = None

    if request.method == 'POST' and form.is_valid():
        identifier = form.cleaned_data['identifier']
        password = form.cleaned_data['password']

        user = authenticate(request, username=identifier, password=password)
        if user is not None:
            login(request, user)
            if user.user_type == 'host':
                return redirect('host_dashboard')
            return redirect('home')
        else:
            error = "Invalid login credentials."

    return render(request, 'accounts/login.html', {'form': form, 'error': error})

#this section will handle logout
def logout_view(request):
    logout(request)
    return redirect('home')

def home_view(request):
    two_weeks_ago = timezone.now() - timedelta(days=14)

    # Recent Listings: added within last 14 days
    recent_listings = Property.objects.filter(created_at__gte=two_weeks_ago).order_by('-created_at')[:8]

    # Featured Listings: priority first, fallback to normal
    priority_listings = list(Property.objects.filter(listing_type='priority').order_by('-created_at')[:8])
    if len(priority_listings) < 8:
        normal_fallback = Property.objects.filter(listing_type='normal').order_by('-created_at')[:8 - len(priority_listings)]
        featured_listings = priority_listings + list(normal_fallback)
    else:
        featured_listings = priority_listings

    context = {
        'recent_listings': recent_listings,
        'featured_listings': featured_listings,
    }

    return render(request, 'accounts/home.html', context)

#this is the host dashboard and it will show all the of the hosts' lisitings and CRUD operations
@login_required()
def host_dashboard(request):
    if request.user.user_type != 'host':
        return redirect('home')  # you missed return here

    user = request.user
    my_properties = Property.objects.filter(owner=user)

    if request.method == 'POST':
        form = ProfilePhotoForm(request.POST, request.FILES, instance=user)
        if form.is_valid():
            form.save()
            return redirect('host_dashboard')
    else:
        form = ProfilePhotoForm(instance=user)

    return render(request, 'accounts/host_dashboard.html', {
        'properties': my_properties,
        'form': form
    })
