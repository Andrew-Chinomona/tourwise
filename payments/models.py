from django.db import models
from django.conf import settings
from listings.models import Property
# Create your models here.
class Payment(models.Model):
    LISTING_TYPE_CHOICES = (
    ('normal', 'Normal'),
    ('priority', 'Priority'),
    )

    property = models.OneToOneField(Property, on_delete=models.CASCADE)
    user =models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    listing_type = models.CharField(max_length=10, choices=LISTING_TYPE_CHOICES)
    amount = models.DecimalField(decimal_places=2, max_digits=6)
    is_complete = models.BooleanField(default=False)
    timestamp = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.property.title} - {self.listing_type} - ${self.amount}"

