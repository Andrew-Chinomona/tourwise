from django import forms
from django.contrib.auth.forms import UserCreationForm
from .models import CustomUser
from django.core.exceptions import ValidationError
import re

class SignupForm(UserCreationForm):
    USER_TYPE_CHOICES = (
        ('host', 'Host'),
        ('tenant', 'Tenant'),
    )

    first_name = forms.CharField(max_length=30, required=True)
    last_name = forms.CharField(max_length=30, required=True)
    email = forms.EmailField(required=True)
    phone_number = forms.CharField(
        max_length=20,
        required=True,
        help_text="Required for payment processing (e.g., +263 777 123 456)"
    )
    user_type = forms.ChoiceField(choices=USER_TYPE_CHOICES, widget=forms.RadioSelect)

    def clean_email(self):
        email = self.cleaned_data.get('email')
        if CustomUser.objects.filter(email=email).exists():
            raise ValidationError("An account with this email already exists.")
        return email

    def clean_phone_number(self):
        phone = self.cleaned_data.get('phone_number')
        if phone:
            # Remove spaces and special characters
            phone = re.sub(r'[\s\-\(\)]', '', phone)
            # Ensure it starts with + or country code
            if not phone.startswith('+') and not phone.startswith('263'):
                phone = '+263' + phone.lstrip('0')
            # Validate length
            if len(phone) < 10:
                raise forms.ValidationError("Please enter a valid phone number")
        return phone

    class Meta:
        model = CustomUser
        fields = ['first_name', 'last_name', 'email', 'phone_number', 'user_type', 'password1', 'password2']

class UserProfileEditForm(forms.ModelForm):
    """Form for editing user profile information"""
    first_name = forms.CharField(max_length=30, required=True)
    last_name = forms.CharField(max_length=30, required=True)
    email = forms.EmailField(required=True)
    phone_number = forms.CharField(
        max_length=20,
        required=False,
        help_text="Optional phone number (e.g., +263 777 123 456)"
    )

    class Meta:
        model = CustomUser
        fields = ['first_name', 'last_name', 'email', 'phone_number', 'profile_photo']
        widgets = {
            'first_name': forms.TextInput(attrs={'class': 'form-control'}),
            'last_name': forms.TextInput(attrs={'class': 'form-control'}),
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
            'phone_number': forms.TextInput(attrs={'class': 'form-control'}),
            'profile_photo': forms.FileInput(attrs={'class': 'form-control'})
        }

    def clean_email(self):
        email = self.cleaned_data.get('email')
        if CustomUser.objects.filter(email=email).exclude(pk=self.instance.pk).exists():
            raise ValidationError("An account with this email already exists.")
        return email

    def clean_phone_number(self):
        phone = self.cleaned_data.get('phone_number')
        if phone:
            # Remove spaces and special characters
            phone = re.sub(r'[\s\-\(\)]', '', phone)
            # Ensure it starts with + or country code
            if not phone.startswith('+') and not phone.startswith('263'):
                phone = '+263' + phone.lstrip('0')
            # Validate length
            if len(phone) < 10:
                raise forms.ValidationError("Please enter a valid phone number")
            # Check for uniqueness
            if CustomUser.objects.filter(phone_number=phone).exclude(pk=self.instance.pk).exists():
                raise ValidationError("An account with this phone number already exists.")
        return phone

class AccountDeletionForm(forms.Form):
    """Form for confirming account deletion"""
    confirmation = forms.CharField(
        max_length=10,
        help_text="Type 'DELETE' to confirm account deletion",
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Type DELETE to confirm'
        })
    )
    password = forms.CharField(
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Enter your password'
        }),
        help_text="Enter your current password to confirm deletion"
    )

    def __init__(self, user, *args, **kwargs):
        self.user = user
        super().__init__(*args, **kwargs)

    def clean_confirmation(self):
        confirmation = self.cleaned_data.get('confirmation')
        if confirmation != 'DELETE':
            raise ValidationError("You must type 'DELETE' to confirm account deletion.")
        return confirmation

    def clean_password(self):
        password = self.cleaned_data.get('password')
        if not self.user.check_password(password):
            raise ValidationError("Incorrect password.")
        return password

class CustomLoginForm(forms.Form):
    identifier = forms.CharField(
        label="Email or Phone Number",
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Enter your email or phone number'
        })
    )
    password = forms.CharField(
        label="Password",
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Enter your password'
        })
    )

class ProfilePhotoForm(forms.ModelForm):
    class Meta:
        model = CustomUser
        fields = ['profile_photo']
