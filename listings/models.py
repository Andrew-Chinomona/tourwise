from django.db import models
from django.conf import settings

class Property(models.Model):
    LISTING_TYPE_CHOICES = [
        ('normal', 'Normal'),
        ('priority', 'Priority'),
    ]

    PROPERTY_TYPE_CHOICES = [
        ('house', 'House'),
        ('apartment', 'Apartment'),
        ('airbnb', 'Airbnb'),
    ]

    property_type = models.CharField(max_length=20, choices=PROPERTY_TYPE_CHOICES, blank=True, null=True)
    title = models.CharField(max_length=200)
    #description = models.TextField()
    facilities = models.CharField(max_length=255, default='Not specified')
    image = models.ImageField(upload_to='property_images/', blank=True, null=True)
    services = models.CharField(max_length=255,  default='Not specified')
    description = models.TextField(blank=True, null=True)
    location = models.CharField(max_length=100)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    contact_info = models.CharField(max_length=100)
    listing_type = models.CharField(max_length=10, choices=LISTING_TYPE_CHOICES, default='normal')
    is_paid = models.BooleanField(default=False)
    owner = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='properties')
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.title

class PropertyImage(models.Model):
    property = models.ForeignKey(Property, on_delete=models.CASCADE, related_name='images')

    image = models.ImageField(
        upload_to='property_images/',
        blank=True,
        null=True
    )

    def __str__(self):
        return f"Image for {self.property.title}"