from django import forms
from listings.models import Property
from django.forms.widgets import FileInput
from django.forms.widgets import ClearableFileInput
from .models import Amenity

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
        widget=forms.Textarea(attrs={'rows': 5, 'placeholder': 'Describe your property...'}),
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

# class PropertyStep5Form(forms.Form):
#     images = forms.FileField(
#         widget=forms.ClearableFileInput(attrs={'multiple': True}),
#         required=False,
#         label="Upload additional interior images (e.g. lounge, kitchen, bedrooms)"
#     )

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

# class PropertyStep7Form(forms.Form):
#     amenities = forms.ModelMultipleChoiceField(
#         queryset=Amenity.objects.all(),
#         widget=forms.CheckboxSelectMultiple,
#         required=False,
#         label="Select Amenities"
#     )
