from django import forms
from listings.models import Property
from django.forms.widgets import FileInput, ClearableFileInput

class MultiFileInput(ClearableFileInput):
    allow_multiple_selected = True

class PropertyStep1Form(forms.Form):
    property_type = forms.ChoiceField(
        choices=Property.PROPERTY_TYPE_CHOICES,
        widget=forms.RadioSelect,
        label = "what type of property are you listing?"
    )


# Step 2: Property description form
class PropertyStep2Form(forms.Form):
        description = forms.CharField(
        widget=forms.Textarea(attrs={'rows': 5}),
        label="Describe the property in detail"
    )


# Step 3: Facilities form (checkboxes for common amenities)
class PropertyStep3Form(forms.Form):
    # Define available facility options
    FACILITY_CHOICES = [
        ('parking', 'Parking'),
        ('wifi', 'WiFi'),
        ('security', 'Security'),
        ('furnished', 'Furnished'),
        ('solar', 'Solar Power'),
        ('borehole', 'Borehole'),
    ]

    # Allow multiple selections using checkboxes
    facilities = forms.MultipleChoiceField(
        choices=FACILITY_CHOICES,
        widget=forms.CheckboxSelectMultiple,
        label="Select facilities available at the property"
    )

# Step 4: Prompt host to upload the main image only
class PropertyStep4Form(forms.Form):
    # One required image upload
    main_image = forms.ImageField(
        required=True,
        label="Upload the MAIN image for your listing (e.g., front of house)"
    )

class PropertyStep5Form(forms.Form):
    # Multiple file input for additional photos
    images = forms.FileField(
        widget=MultiFileInput(attrs={'multiple': True}),
        required=False,
        label="Upload interior photos (e.g. lounge, kitchen, bedrooms)"
    )


class PropertyStep6Form(forms.Form):
    additional_notes = forms.CharField(
        widget=forms.Textarea(attrs={'rows': 4}),
        required=False,
        label="Any final notes or extra details?"
    )

class PropertyStep7Form(forms.Form):
    price = forms.DecimalField(
        label="Monthly Rent (USD)",
        min_value= 1.00,
        max_digits=10,
        decimal_places=2,
        widget= forms.NumberInput(attrs={'placeholder': 'e.g. 350'}),
    )

class PropertyStep8Form(forms.Form):
    street_address = forms.CharField(
        label="Street Address",
        max_length=100,
        widget=forms.TextInput(attrs={'placeholder': 'e.g. 123 Causeway'}),
    )
    suburb=forms.CharField(
        label="Suburb/Area",
        max_length=100,
        widget= forms.TextInput(attrs={'placeholder': 'e.g. Chisipite'}),
    )
    city=forms.CharField(
        label="City/Town",
        max_length=100,
        widget= forms.TextInput(attrs={'placeholder': 'e.g. Harare'}),
    )