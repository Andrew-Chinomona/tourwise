from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.decorators import login_required
from listings.models import Property, PropertyImage
from django.shortcuts import render, redirect
from .forms import SignupForm, CustomLoginForm, ProfilePhotoForm
from django.utils import timezone
from datetime import timedelta
from django.db.models import Value, CharField, Q
from django.db.models.functions import Concat
from django.urls import reverse
from django.conf import settings


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


# this section will handle logout
def logout_view(request):
    logout(request)
    return redirect('home')


def home_view(request):
    two_weeks_ago = timezone.now() - timedelta(days=14)

    # Get recent listings
    recent_listings = Property.objects.filter(is_paid=True, created_at__gte=two_weeks_ago).order_by('-created_at')[:8]

    # Get featured listings
    priority_listings = list(Property.objects.filter(is_paid=True, listing_type='priority').order_by('-created_at')[:8])
    if len(priority_listings) < 8:
        fallback = Property.objects.filter(is_paid=True, listing_type='normal').order_by('-created_at')[
                   :8 - len(priority_listings)]
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
        'locations': locations,
        'GOOGLE_API_KEY': settings.GOOGLE_API_KEY,
    }

    return render(request, 'accounts/home.html', context)


# this is the host dashboard and it will show all the of the hosts' lisitings and CRUD operations
@login_required()
def host_dashboard(request):
    if request.user.user_type != 'host':
        return redirect('home')

    user = request.user
    my_properties = Property.objects.filter(owner=user, is_paid=True)
    drafts = Property.objects.filter(owner=user, is_paid=False)

    # Get payment status for drafts
    draft_payments = {}
    for draft in drafts:
        try:
            payment = draft.payment
            draft_payments[draft.id] = payment
        except:
            draft_payments[draft.id] = None

    if request.method == 'POST':
        form = ProfilePhotoForm(request.POST, request.FILES, instance=user)
        if form.is_valid():
            form.save()
            return redirect('host_dashboard')
    else:
        form = ProfilePhotoForm(instance=user)

    return render(request, 'accounts/host_dashboard.html', {
        'properties': my_properties,
        'drafts': drafts,
        'draft_payments': draft_payments,
        'form': form
    })


def search_results_view(request):
    query = request.GET.get('location')
    property_type = request.GET.get('property_type')
    max_price = request.GET.get('max_price')

    properties = Property.objects.filter(is_paid=True)  # Only show paid listings

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


def step_search_view(request):
    """Step-by-step search flow"""
    step = request.GET.get('step', '1')

    if request.method == 'POST':
        if step == '1':
            # Step 1: Location
            location = request.POST.get('location')
            if location:
                request.session['search_location'] = location
                return redirect(f'{reverse("step_search")}?step=2')
        elif step == '2':
            # Step 2: Property Type
            property_type = request.POST.get('property_type')
            if property_type:
                request.session['search_property_type'] = property_type
                return redirect(f'{reverse("step_search")}?step=3')
        elif step == '3':
            # Step 3: Max Price (optional)
            max_price = request.POST.get('max_price')
            location = request.session.get('search_location', '')
            property_type = request.session.get('search_property_type', '')

            # Build search URL
            search_url = reverse('search_results') + f'?location={location}'
            if property_type:
                search_url += f'&property_type={property_type}'
            if max_price:
                search_url += f'&max_price={max_price}'

            # Clear session
            request.session.pop('search_location', None)
            request.session.pop('search_property_type', None)

            return redirect(search_url)

    # Get saved values from session
    saved_location = request.session.get('search_location', '')
    saved_property_type = request.session.get('search_property_type', '')

    context = {
        'step': step,
        'saved_location': saved_location,
        'saved_property_type': saved_property_type,
        'GOOGLE_API_KEY': settings.GOOGLE_API_KEY,
    }

    return render(request, 'accounts/step_search.html', context)
