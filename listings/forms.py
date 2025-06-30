from django import forms
from django.forms.widgets import FileInput
from django.forms.widgets import ClearableFileInput
from .models import Amenity, Property, Currency
from django.utils.safestring import mark_safe
from listings.models import Currency

class MultipleFileInput(forms.ClearableFileInput):
    allow_multiple_selected = True

class MultipleFileField(forms.FileField):
    def __init__(self, *args, **kwargs):
        kwargs.setdefault("widget", MultipleFileInput())
        super().__init__(*args, **kwargs)

    def clean(self, data, initial=None):
        single_file_clean = super().clean
        if isinstance(data, (list, tuple)):
            result = [single_file_clean(d, initial) for d in data]
        else:
            result = single_file_clean(data, initial)
        return result

class PropertyStep1Form(forms.Form):
    property_type = forms.ChoiceField(
        choices=Property.PROPERTY_TYPE_CHOICES,
        widget=forms.RadioSelect,
        label="What type of property are you listing?"
    )

class PropertyStep2Form(forms.Form):
    description = forms.CharField(
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'rows': 5,
            'placeholder': 'Describe your property...'
        }),
        label='Property Description',
        max_length=1000,
        required=True
    )

class PropertyStep3Form(forms.Form):
    city = forms.CharField(
        max_length=100,
        label="City",
        widget=forms.TextInput(attrs={
            'placeholder': 'e.g. Harare',
            'class': 'form-control'
        })
    )
    suburb = forms.CharField(
        max_length=100,
        label="Suburb",
        required=False,
        widget=forms.TextInput(attrs={
            'placeholder': 'e.g. Avondale',
            'class': 'form-control'
        })
    )
    street_address = forms.CharField(
        max_length=255,
        label="Street Address",
        widget=forms.TextInput(attrs={
            'placeholder': 'e.g. 123 Smart Street',
            'class': 'form-control'
        })
    )

    # Hidden fields for coordinates (populated by JS)
    latitude = forms.FloatField(widget=forms.HiddenInput(), required=False)
    longitude = forms.FloatField(widget=forms.HiddenInput(), required=False)


class PropertyStep4Form(forms.Form):
    main_image = forms.ImageField(
        required=True,
        label="Upload the MAIN image (e.g., front of house)",
        widget=forms.FileInput(attrs={
            'class': 'form-control',
            'accept': 'image/*',
        }),
        error_messages={
            'required': 'Please upload a main image for your property',
            'invalid_image': 'Please upload a valid image file (JPEG, PNG, etc.)'
        }
    )

    def clean_main_image(self):
        image = self.cleaned_data.get('main_image')
        if image:
            if image.size > 5 * 1024 * 1024:  # 5MB limit
                raise forms.ValidationError("Image file too large (max 5MB)")
            if not image.content_type.startswith('image/'):
                raise forms.ValidationError("File is not an image")
        return image

class PropertyStep5Form(forms.Form):
    images = MultipleFileField(
        label="Upload interior images (e.g. lounge, kitchen, bedrooms)",
        required=False,
        widget=MultipleFileInput(attrs={
            'class': 'form-control',
            'multiple': True,
            'accept': 'image/*'
        })
    )

    def clean_images(self):
        files = self.files.getlist('images')
        if not files:
            raise forms.ValidationError("Please upload at least one image.")

        for f in files:
            if not f.content_type.startswith('image/'):
                raise forms.ValidationError(f"{f.name} is not an image file.")
            if f.size > 5 * 1024 * 1024:  # 5MB limit
                raise forms.ValidationError(f"{f.name} is too large (max 5MB).")
        return files


class PropertyStep6Form(forms.Form):
    price = forms.DecimalField(
        max_digits=10,
        decimal_places=2,
        label="Set Property Price",
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'placeholder': 'e.g. 450.00',
            'step': '0.01',
            'min': '0'
        })
    )

    currency = forms.ModelChoiceField(
        queryset=Currency.objects.all(),
        empty_label=None,
        label="Currency",
        widget=forms.Select(attrs={
            'class': 'form-select'
        })
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # Order currencies alphabetically
        self.fields['currency'].queryset = Currency.objects.all().order_by('code')

        # Default to USD if no initial currency
        if not self.initial.get('currency'):
            try:
                usd = Currency.objects.get(code='USD')
                self.initial['currency'] = usd
            except Currency.DoesNotExist:
                pass

class PropertyStep7Form(forms.Form):
    amenities = forms.ModelMultipleChoiceField(
        queryset=Amenity.objects.all(),
        widget=forms.CheckboxSelectMultiple,
        required=False,
        label="Select Amenities"
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Dynamically load all amenities in case they change
        self.fields['amenities'].queryset = Amenity.objects.all()


class PropertyStep8Form(forms.Form):
    contact_name = forms.CharField(
        label="Contact Name",
        max_length=100,
        widget=forms.TextInput(attrs={
            'placeholder': 'e.g. John Doe',
            'class': 'form-control'
        })
    )
    contact_phone = forms.CharField(
        label="Phone Number",
        max_length=20,
        widget=forms.TextInput(attrs={
            'placeholder': 'e.g. +263 777 123 456',
            'class': 'form-control'
        })
    )
    contact_email = forms.EmailField(
        label="Email Address",
        widget=forms.EmailInput(attrs={
            'placeholder': 'e.g. john@example.com',
            'class': 'form-control'
        })
    )

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user', None)
        property_obj = kwargs.pop('property_obj', None)
        super().__init__(*args, **kwargs)

        # Set initial values from user profile if available
        if self.user and self.user.is_authenticated:
            self.fields['contact_name'].initial = (
                f"{self.user.first_name} {self.user.last_name}".strip()
                if (self.user.first_name or self.user.last_name)
                else self.user.username
            )
            self.fields['contact_email'].initial = self.user.email

            # Prefer property's existing contact info if available, otherwise use user's
            if property_obj and property_obj.contact_phone:
                self.fields['contact_phone'].initial = property_obj.contact_phone
            elif hasattr(self.user, 'phone_number') and self.user.phone_number:
                self.fields['contact_phone'].initial = self.user.phone_number

class PropertyStep9Form(forms.Form):
    bedrooms = forms.IntegerField(
        label="Number of Bedrooms",
        min_value=0,
        widget=forms.NumberInput(attrs={
            'placeholder': 'e.g. 3',
            'class': 'form-control'
        })
    )
    bathrooms = forms.IntegerField(
        label="Number of Bathrooms",
        min_value=0,
        widget=forms.NumberInput(attrs={
            'placeholder': 'e.g. 2',
            'class': 'form-control'
        })
    )
    area = forms.IntegerField(
        label="Total Area (in sq meters)",
        min_value=0,
        widget=forms.NumberInput(attrs={
            'placeholder': 'e.g. 120',
            'class': 'form-control'
        })
    )
class ChoosePaymentForm(forms.Form):
    listing_type = forms.ChoiceField(
        choices=Property.LISTING_TYPE_CHOICES,
        widget=forms.RadioSelect,
        label="Choose your listing type"
    )

class EditPropertyForm(forms.ModelForm):
        class Meta:
            model = Property
            fields = [
                'property_type',
                'title',
                'description',
                'street_address',
                'suburb',
                'city',
                #'main_image',
                #'profile_photo',
                'bedrooms',
                'bathrooms',
                'area',
                'price',
                'contact_phone',
                'contact_email',
                'listing_type',
                'amenities',
            ]
            widgets = {
                'description': forms.Textarea(attrs={'class': 'form-control','rows': 4}),
                'listing_type': forms.RadioSelect(),
                'amenities': forms.CheckboxSelectMultiple(),
            }
