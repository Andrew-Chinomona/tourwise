from django.db import models
from django.conf import settings
from django.contrib.gis.db import models as gis_models

class Currency(models.Model):
    code = models.CharField(max_length=10, unique=True)
    name = models.CharField(max_length=100)
    symbol = models.CharField(max_length=10)

    def __str__(self):
        return f"({self.code}) {self.symbol}"


class Amenity(models.Model):
    name = models.CharField(max_length=100)
    icon = models.CharField(max_length=50, default='check',
                            help_text="Font Awesome icon name (e.g. 'wifi', 'tv', 'swimming-pool')")

    def __str__(self):
        return self.name


class Property(models.Model):
    LISTING_TYPE_CHOICES = [
        ('normal', 'Normal Listing ($10)'),
        ('priority', 'Priority Listing ($20)'),
    ]

    PROPERTY_TYPE_CHOICES = [
        ('house', 'House'),
        ('apartment', 'Apartment'),
        ('airbnb', 'Airbnb'),
        ('room', 'Room'),
        ('guesthouse', 'Guesthouse'),
    ]

    #Ownership and classification
    owner = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='properties')
    property_type = models.CharField(max_length=20, choices=PROPERTY_TYPE_CHOICES, blank=True, null=True)
    title = models.CharField(max_length=100, default='Untitled')
    description = models.TextField(blank=True, null=True)
    # current_step = models.IntegerField(default=1)  # Removed - no longer using multi-step form

    #Location
    street_address = models.CharField(max_length=255, blank=True)
    suburb = models.CharField(max_length=255, blank=True)
    city = models.CharField(max_length=100, blank=True)
    state_or_region = models.CharField(max_length=100, blank=True)  # NEW: for region/state
    country = models.CharField(max_length=100, blank=True)          # NEW: for country
    # ---
    # The following fields are deprecated and will be removed after migration:
    latitude = models.FloatField(blank=True, null=True)   # DEPRECATED: use location PointField
    longitude = models.FloatField(blank=True, null=True)  # DEPRECATED: use location PointField
    # ---
    # To enable geospatial queries, install PostGIS and add the following field:

    location = gis_models.PointField(geography=True, blank=True, null=True)
    #
    # PostGIS Setup Instructions:
    # 1. Install PostGIS in your PostgreSQL database (see https://postgis.net/install/)
    # 2. In settings.py, set 'ENGINE': 'django.contrib.gis.db.backends.postgis' for your DATABASES config
    # 3. Uncomment the import and the location field above
    # 4. Run: python manage.py makemigrations listings
    # 5. Run: python manage.py migrate
    # 6. You can now store and query geospatial data in the location field
    # ---
    google_maps_url = models.URLField(blank=True, null=True, help_text="Google Maps link for confirmed location")

    #Media
    main_image = models.ImageField(upload_to='property_main_images/', null=True, blank=True)
    profile_photo = models.ImageField(upload_to='host_photos/', null=True, blank=True)

    #Features
    bedrooms = models.PositiveIntegerField(default=0)
    bathrooms = models.PositiveIntegerField(default=0)
    area = models.PositiveIntegerField(default=0)

    #Amenities
    amenities = models.ManyToManyField(Amenity, blank=True)

    #Pricing
    price = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    currency = models.ForeignKey(Currency, on_delete=models.SET_NULL, null=True, blank=True)
    # #Contact info
    contact_phone = models.CharField(max_length=20, blank=True)
    contact_email = models.EmailField(blank=True)
    # contact_name = models.CharField(max_length=100, blank=True)

    # Add `listing_type` field and the other necessary fields here
    listing_type = models.CharField(
        max_length=10,
        choices=LISTING_TYPE_CHOICES,
        default='normal',
        help_text="Type of listing for this property"
    )

    # Listing type & status
    is_paid = models.BooleanField(default=False)

    #Metadata
    created_at = models.DateTimeField(auto_now_add=True)

    @property
    def google_maps_directions_url(self):
        if self.location:
            return f"https://www.google.com/maps/dir/?api=1&destination={self.location.y},{self.location.x}"
        return None

    @staticmethod
    def get_listing_price(listing_type):
        if listing_type == 'priority':
            return 20.00
        return 10.00

    def __str__(self):
        return f"{self.title} ({self.city})"

    def generate_title(self):
        if self.property_type and self.suburb:
            title = f"{self.property_type.title()} in {self.suburb.title()}"
            if hasattr(self, 'city') and self.city:
                title += f" ({self.city.title()})"
            self.title = title
            self.save()


#Interior Images (related to Property)
class PropertyImage(models.Model):
    property = models.ForeignKey(Property, on_delete=models.CASCADE, related_name='images')
    image = models.ImageField(upload_to='property_images/',blank = True, null = True)

    def __str__(self):
        return f"Image for {self.property.title}"