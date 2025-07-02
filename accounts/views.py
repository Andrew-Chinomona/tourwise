from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth import login, logout, authenticate,get_backends
from django.contrib.auth.decorators import login_required
from listings.models import Property, PropertyImage
from django.shortcuts import render, redirect
from .forms import SignupForm, CustomLoginForm, ProfilePhotoForm
from django.utils import timezone
from datetime import timedelta
from django.db.models import F, Value, CharField, Q
from django.db.models.functions import Concat


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

    # Get recent listings
    recent_listings = Property.objects.filter(is_paid=True ,created_at__gte=two_weeks_ago).order_by('-created_at')[:8]

    # Get featured listings
    priority_listings = list(Property.objects.filter(listing_type='priority', is_paid =True).order_by('-created_at')[:8])
    if len(priority_listings) < 8:
        fallback = Property.objects.filter(listing_type='normal').order_by('-created_at')[:8 - len(priority_listings)]
        featured_listings = priority_listings + list(fallback)
    else:
        featured_listings = priority_listings

    # Prepare list of unique city-suburb combinations
    locations = Property.objects.annotate(
        loc_string=Concat('city', Value(' - '), 'suburb', output_field=CharField())
    ).values('city', 'suburb').distinct()

    context = {
        'recent_listings': recent_listings,
        'featured_listings': featured_listings,
        'locations': locations
    }

    return render(request, 'accounts/home.html', context)


#this is the host dashboard and it will show all the of the hosts' lisitings and CRUD operations
@login_required()
def host_dashboard(request):
    if request.user.user_type != 'host':
        return redirect('home')  # you missed return here

    user = request.user
    my_properties = Property.objects.filter(owner=user, is_paid =True)
    drafts = Property.objects.filter(owner=user, is_paid=False)

    if request.method == 'POST':
        form = ProfilePhotoForm(request.POST, request.FILES, instance=user)
        if form.is_valid():
            form.save()
            return redirect('host_dashboard')
    else:
        form = ProfilePhotoForm(instance=user)

    return render(request, 'accounts/host_dashboard.html', {
        'properties': my_properties,
        'drafts' : drafts,
        'form': form
    })

def search_results_view(request):
    query = request.GET.get('location')
    property_type = request.GET.get('property_type')
    max_price = request.GET.get('max_price')

    properties = Property.objects.all()

    # Filter by location (city or suburb)
    if query:
        if '|' in query:
            city, suburb = query.split('|')
            properties = properties.filter(city__iexact=city.strip(), suburb__iexact=suburb.strip())
        else:
            properties = properties.filter(Q(city__icontains=query) | Q(suburb__icontains=query))

    # Filter by type
    if property_type:
        properties = properties.filter(property_type__iexact=property_type)

    # Filter by price
    if max_price:
        try:
            properties = properties.filter(price__lte=int(max_price))
        except ValueError:
            pass  # ignore invalid price input

    return render(request, 'accounts/search_results.html', {
        'properties': properties,
        'query': query,
        'property_type': property_type,
        'max_price': max_price
    })

from django.contrib.auth import login
from django.shortcuts import render, redirect
from .forms import SignupForm
from .models import CustomUser

def become_host_view(request):
    if request.user.is_authenticated:
        # Prefill for existing user
        initial_data = {
            'first_name': request.user.first_name,
            'last_name': request.user.last_name,
            'email': request.user.email,
            'phone_number': request.user.phone_number,
            'user_type': 'host'
        }
        form = SignupForm(initial=initial_data)
        return render(request, 'accounts/become_host.html', {'form': form, 'is_editing': True})

    else:
        if request.method == 'POST':
            form = SignupForm(request.POST)
            if form.is_valid():
                user = form.save(commit=False)
                user.username = f"{user.first_name} {user.last_name}"
                user.save()

                user.backend = 'accounts.backends.EmailOrPhoneBackend'
                login(request, user)

                return redirect('host_dashboard')
        else:
            form = SignupForm(initial={'user_type': 'host'})

        return render(request, 'accounts/become_host.html', {'form': form, 'is_editing': False})
