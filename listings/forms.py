from django import forms
from listings.models import Property

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
