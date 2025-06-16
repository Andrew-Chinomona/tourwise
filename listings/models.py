from django.db import models
from django.conf import settings

class Property(models.Model):
    LISTING_TYPE_CHOICES = [
        ('normal', 'Normal'),
        ('priority', 'Priority'),
    ]

    title = models.CharField(max_length=200)
    description = models.TextField()
    location = models.CharField(max_length=100)
    price = models.DecimalField(decimal_places=2, max_digits=10)
    contact_info = models.CharField(max_length=100)
    listing_type = models.CharField(max_length=10, choices=LISTING_TYPE_CHOICES, default='normal')
    image = models.ImageField(upload_to='property_images/', null=True, blank=True)
    is_paid = models.BooleanField(default=False)
    owner = models.ForeignKey(settings.AUTH_USER_MODEL, related_name='properties', on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.title
