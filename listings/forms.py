from django import forms
from django.forms.widgets import ClearableFileInput
from .models import Amenity, Property, Currency
from django.contrib.gis.geos import Point


# ---------- Utility Widgets ----------

class MultipleFileInput(forms.ClearableFileInput):
    allow_multiple_selected = True


class MultipleFileField(forms.FileField):
    def __init__(self, *args, **kwargs):
        kwargs.setdefault("widget", MultipleFileInput())
        super().__init__(*args, **kwargs)

    def clean(self, data, initial=None):
        single_file_clean = super().clean
        if isinstance(data, (list, tuple)):
            return [single_file_clean(d, initial) for d in data]
        return single_file_clean(data, initial)


class ChoosePaymentForm(forms.Form):
    listing_type = forms.ChoiceField(
        choices=Property.LISTING_TYPE_CHOICES,
        widget=forms.RadioSelect,
        label="Choose your listing type"
    )


# ---------- Unified Single-Page Form ----------

class PropertyListingForm(forms.ModelForm):
    """
    Unified form that combines all 10 step forms into a single-page form.
    This replaces the multi-step wizard with a more streamlined user experience.
    """
    # Step 1: Property Type
    property_type = forms.ChoiceField(
        choices=Property.PROPERTY_TYPE_CHOICES,
        widget=forms.Select(attrs={'class': 'form-select'}),
        label="Property Type",
        required=True
    )
    
    # Step 2: Description
    description = forms.CharField(
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'rows': 5,
            'placeholder': 'Describe your property...',
            'maxlength': '1000'
        }),
        label='Property Description',
        max_length=1000,
        required=True
    )
    
    # Step 3: Location
    city_suburb = forms.CharField(
        max_length=200,
        label="City & Suburb",
        widget=forms.TextInput(attrs={
            'placeholder': 'e.g. Ashdown Park, Harare',
            'class': 'form-control',
            'id': 'city_suburb'
        }),
        required=True
    )
    street_address = forms.CharField(
        max_length=255,
        label="Street Address",
        widget=forms.TextInput(attrs={
            'placeholder': 'e.g. 123 Smart Street',
            'class': 'form-control',
            'id': 'street_address'
        }),
        required=True
    )
    latitude = forms.FloatField(
        widget=forms.HiddenInput(attrs={'id': 'latitude'}),
        required=False
    )
    longitude = forms.FloatField(
        widget=forms.HiddenInput(attrs={'id': 'longitude'}),
        required=False
    )
    
    # Step 4: Main Image
    main_image = forms.ImageField(
        required=True,
        label="Main Property Image",
        widget=forms.FileInput(attrs={
            'class': 'form-control',
            'accept': 'image/*',
        }),
        help_text="Upload the main image (e.g., front of house) - Max 10MB",
        error_messages={
            'required': 'Please upload a main image for your property',
            'invalid_image': 'Please upload a valid image file (JPEG, PNG, etc.)'
        }
    )
    
    # Step 5: Interior Images
    interior_images = MultipleFileField(
        label="Interior Images",
        required=False,
        widget=MultipleFileInput(attrs={
            'class': 'form-control',
            'multiple': True,
            'accept': 'image/*'
        }),
        help_text="Upload interior images (lounge, kitchen, bedrooms, etc.) - Max 10MB each"
    )
    
    # Step 6: Price & Currency
    price = forms.DecimalField(
        max_digits=10,
        decimal_places=2,
        label="Property Price",
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'placeholder': 'e.g. 450.00',
            'step': '0.01',
            'min': '0'
        }),
        required=True
    )
    
    currency = forms.ModelChoiceField(
        queryset=Currency.objects.all(),
        empty_label=None,
        label="Currency",
        widget=forms.Select(attrs={
            'class': 'form-select'
        }),
        required=True
    )
    
    # Step 7: Amenities
    amenities = forms.ModelMultipleChoiceField(
        queryset=Amenity.objects.all(),
        widget=forms.CheckboxSelectMultiple,
        required=False,
        label="Amenities"
    )
    
    # Step 8: Contact Information
    contact_name = forms.CharField(
        label="Contact Name",
        max_length=100,
        widget=forms.TextInput(attrs={
            'placeholder': 'e.g. John Doe',
            'class': 'form-control'
        }),
        required=True
    )
    contact_phone = forms.CharField(
        label="Phone Number",
        max_length=20,
        widget=forms.TextInput(attrs={
            'placeholder': 'e.g. +263 777 123 456',
            'class': 'form-control'
        }),
        required=True
    )
    contact_email = forms.EmailField(
        label="Email Address",
        widget=forms.EmailInput(attrs={
            'placeholder': 'e.g. john@example.com',
            'class': 'form-control'
        }),
        required=True
    )
    
    # Step 9: Property Details
    bedrooms = forms.IntegerField(
        label="Number of Bedrooms",
        min_value=0,
        widget=forms.NumberInput(attrs={
            'placeholder': 'e.g. 3',
            'class': 'form-control'
        }),
        required=True
    )
    bathrooms = forms.IntegerField(
        label="Number of Bathrooms",
        min_value=0,
        widget=forms.NumberInput(attrs={
            'placeholder': 'e.g. 2',
            'class': 'form-control'
        }),
        required=True
    )
    area = forms.IntegerField(
        label="Total Area (sq meters)",
        min_value=0,
        widget=forms.NumberInput(attrs={
            'placeholder': 'e.g. 120',
            'class': 'form-control'
        }),
        required=True
    )
    
    class Meta:
        model = Property
        fields = [
            'property_type', 'description', 'price', 'currency',
            'street_address', 'suburb', 'city', 'location',
            'bedrooms', 'bathrooms', 'area', 'main_image',
            'contact_phone', 'contact_email', 'amenities'
        ]
    
    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        
        # Set currency queryset and default to USD
        self.fields['currency'].queryset = Currency.objects.all().order_by('code')
        if not self.is_bound and not self.initial.get('currency'):
            usd = Currency.objects.filter(code__iexact='USD').first()
            if usd:
                self.initial['currency'] = usd
        
        # Pre-populate contact information from user if available
        if self.user and self.user.is_authenticated and not self.instance.pk:
            self.fields['contact_name'].initial = (
                f"{self.user.first_name} {self.user.last_name}".strip()
                if (self.user.first_name or self.user.last_name)
                else self.user.username
            )
            self.fields['contact_email'].initial = self.user.email
            
            if hasattr(self.user, 'phone_number') and self.user.phone_number:
                self.fields['contact_phone'].initial = self.user.phone_number
    
    def clean_main_image(self):
        """Validate main image file size and type"""
        image = self.cleaned_data.get('main_image')
        if image:
            if image.size > 10 * 1024 * 1024:
                raise forms.ValidationError("Image file too large (max 10MB)")
            if not image.content_type.startswith('image/'):
                raise forms.ValidationError("File is not an image")
        return image
    
    def clean_interior_images(self):
        """Validate interior images - at least one required"""
        files = self.files.getlist('interior_images')
        if files:
            for f in files:
                if not f.content_type.startswith('image/'):
                    raise forms.ValidationError(f"{f.name} is not an image file.")
                if f.size > 10 * 1024 * 1024:
                    raise forms.ValidationError(f"{f.name} is too large (max 10MB).")
        return files
    
    def clean(self):
        """Additional validation and processing"""
        cleaned_data = super().clean()
        
        # Parse city_suburb into city and suburb
        city_suburb = cleaned_data.get('city_suburb', '')
        if city_suburb and ',' in city_suburb:
            parts = [p.strip() for p in city_suburb.split(',')]
            if len(parts) >= 2:
                cleaned_data['suburb'] = parts[0]
                cleaned_data['city'] = parts[1]
        elif city_suburb:
            # If no comma, treat entire value as suburb
            cleaned_data['suburb'] = city_suburb
            cleaned_data['city'] = ''
        
        # Validate that coordinates are provided
        lat = cleaned_data.get('latitude')
        lng = cleaned_data.get('longitude')
        if not lat or not lng:
            raise forms.ValidationError(
                "Please select a location from the map to set coordinates."
            )
        
        return cleaned_data
    
    def save(self, commit=True):
        """Save property with location point and handle images/amenities"""
        from django.db import transaction
        
        instance = super().save(commit=False)
        
        # Create Point from latitude and longitude
        lat = self.cleaned_data.get('latitude')
        lng = self.cleaned_data.get('longitude')
        if lat is not None and lng is not None:
            instance.location = Point(lng, lat)
        
        # Set contact_name (not in model, stored separately or derived)
        contact_name = self.cleaned_data.get('contact_name')
        # Note: contact_name field doesn't exist in Property model
        # You may want to add it or handle it differently
        
        if commit:
            with transaction.atomic():
                instance.save()
                
                # Save many-to-many amenities
                self.save_m2m()
        
        return instance


# ---------- Edit Form ----------

class EditPropertyForm(forms.ModelForm):
    latitude = forms.FloatField(widget=forms.HiddenInput(), required=False)
    longitude = forms.FloatField(widget=forms.HiddenInput(), required=False)

    class Meta:
        model = Property
        fields = [
            'property_type',
            'title',
            'description',
            'street_address',
            'suburb',
            'city',
            'state_or_region',
            'country',
            'bedrooms',
            'bathrooms',
            'area',
            'price',
            'contact_phone',
            'contact_email',
            'listing_type',
            'amenities',
            'currency',
        ]
        widgets = {
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 4}),
            'listing_type': forms.RadioSelect(),
            'amenities': forms.CheckboxSelectMultiple(),
        }

    def save(self, commit=True):
        instance = super().save(commit=False)
        lat = self.cleaned_data.get('latitude')
        lng = self.cleaned_data.get('longitude')
        if lat is not None and lng is not None:
            instance.location = Point(lng, lat)
        if commit:
            instance.save()
            self.save_m2m()
        return instance
