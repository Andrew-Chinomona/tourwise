from django.shortcuts import render, redirect
from django.contrib.auth import login
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
