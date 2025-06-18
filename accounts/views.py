from django.contrib.auth.forms import AuthenticationForm
from django.shortcuts import render, redirect
from django.contrib.auth import login, logout, authenticate
from .forms import SignupForm # Import your custom signup form

# Define the view for user signup
def signup_view(request):
    # If this is a POST request, it means the form was submitted
    if request.method == 'POST':
        form = SignupForm(request.POST)
        if form.is_valid():
            # Save the new user object to the database
            user = form.save()
            login(request, user)

            #redirect based on user type
            if user.user_type == 'host':
                return redirect('host_dashboard')
            else:
                return redirect('home')

    else:
        # If GET request (first time visiting), show an empty signup form
        form = SignupForm()

    # Render the signup page with the form (both GET and POST cases)
    return render(request, 'accounts/signup.html', {'form': form})


#This section will handle user login
def login_view(request):
    if request.method == 'POST':
        form = AuthenticationForm(data=request.POST)
        if form.is_valid():
            user = form.get_user()
            login(request, user)

            #this part will redirect the user based on their user type
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


from django.http import HttpResponse

def home_view(request):
    return HttpResponse("<h1>Welcome to Tourwsie</h1><p>This is the homepage placeholder.</p>")

def host_dashboard(request):
    return HttpResponse("Welcome to the Host Dashboard!")
