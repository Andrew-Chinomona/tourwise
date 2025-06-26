from django import forms
from listings.models import Property
from django.forms.widgets import FileInput
from django.forms.widgets import ClearableFileInput
from .models import Amenity

# class MultipleFileInput(forms.ClearableFileInput):
#     allow_multiple_selected = True
#
#     def value_from_datadict(self, data, files, name):
#         if hasattr(files, 'getlist'):
#             return files.getlist(name)
#         return None
class MultipleFileInput(forms.ClearableFileInput):
    allow_multiple_selected = True

class PropertyStep1Form(forms.Form):
    property_type = forms.ChoiceField(
        choices=Property.PROPERTY_TYPE_CHOICES,
        widget=forms.RadioSelect,
        label = "what type of property are you listing?"
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
        widget=forms.TextInput(attrs={'placeholder': 'e.g. Harare'})
    )
    suburb = forms.CharField(
        max_length=100,
        label="Suburb",
        required=False,
        widget=forms.TextInput(attrs={'placeholder': 'e.g. Avondale'})
    )
    street_address = forms.CharField(
        max_length=255,
        label="Street Address",
        widget=forms.TextInput(attrs={'placeholder': 'e.g. 123 Smart Street'})
    )

class PropertyStep4Form(forms.Form):
    main_image = forms.ImageField(
        required=True,
        label="Upload the MAIN image (e.g., front of house)"
    )

class PropertyStep5Form(forms.Form):
    images = forms.FileField(
        widget=MultipleFileInput(attrs={'multiple': True}),
        required=False,
        label="Upload interior images (e.g. lounge, kitchen, bedrooms)"
    )

    def clean_images(self):
        files = self.files.getlist('images')

        if not files:
            return []

        for f in files:
            if not f.content_type.startswith('image/'):
                raise forms.ValidationError(f"{f.name} is not an image.")
        return files

class PropertyStep6Form(forms.Form):
    price = forms.DecimalField(
        max_digits=10,
        decimal_places=2,
        label="Set Property Price (USD)",
        widget=forms.NumberInput(attrs={'placeholder': 'e.g. 450.00'})
    )

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
            widget=forms.TextInput(attrs={'placeholder': 'e.g. John Doe'})
        )
        contact_phone = forms.CharField(
            label="Phone Number",
            max_length=20,
            widget=forms.TextInput(attrs={'placeholder': 'e.g. +263 777 123 456'})
        )
        contact_email = forms.EmailField(
            label="Email Address",
            widget=forms.EmailInput(attrs={'placeholder': 'e.g. john@example.com'})
        )
        profile_photo = forms.ImageField(
            label="Host Profile Photo (optional)",
            required=False
        )

class PropertyStep9Form(forms.Form):
    bedrooms = forms.IntegerField(
        label="Number of Bedrooms",
        min_value=0,
        widget=forms.NumberInput(attrs={'placeholder': 'e.g. 3'})
    )
    bathrooms = forms.IntegerField(
        label="Number of Bathrooms",
        min_value=0,
        widget=forms.NumberInput(attrs={'placeholder': 'e.g. 2'})
    )
    area = forms.IntegerField(
        label="Total Area (in sq meters)",
        min_value=0,
        widget=forms.NumberInput(attrs={'placeholder': 'e.g. 120'})
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
