from django import forms
from .models import CustomUser
from django.contrib.auth.forms import UserCreationForm

class SignupForm(UserCreationForm):
    USER_TYPE_CHOICES = (
    ('host','Host'),
    ('tenant','Tenant'),
    )

    email =  forms.EmailField(required=True)
    phone_number = forms.CharField(max_length=20, required=True)
    user_type = forms.ChoiceField(choices=USER_TYPE_CHOICES, widget=forms.RadioSelect)

    class Meta:
        model= CustomUser
        fields = ['username','email','phone_number','user_type','password1','password2']