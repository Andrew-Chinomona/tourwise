from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.decorators import login_required
from listings.models import Property, PropertyImage
from django.shortcuts import render, redirect
from .forms import SignupForm, CustomLoginForm

def signup_view(request):
    if request.method == 'POST':
        form = SignupForm(request.POST)
        if form.is_valid():
            user = form.save(commit=False)  # Don't save to DB yet
            user.username = f"{user.first_name} {user.last_name}"
            user.save()  # Now save to DB
            login(request, user)

            # Redirect based on user type
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
    return render(request, 'accounts/home.html')

#this is the host dashboard and it will show all the of the hosts' lisitings and CRUD operations
@login_required()
def host_dashboard(request):
    if request.user.user_type != 'host':
        redirect('home')

    my_properties = Property.objects.filter(owner=request.user)
    return render(request, 'accounts/host_dashboard.html', {'properties': my_properties})
