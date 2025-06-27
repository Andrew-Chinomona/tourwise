from django.db import models
from django.contrib.auth.models import AbstractUser

class CustomUser(AbstractUser):
    USER_TYPE_CHOICES = (
        ('host', 'Host'),
        ('tenant', 'Tenant'),
    )

    user_type = models.CharField(max_length=10, choices=USER_TYPE_CHOICES, default='tenant')
    phone_number = models.CharField(max_length=20, blank=True, null=True, unique=True)
    email = models.EmailField(unique=True)
    profile_photo = models.ImageField(upload_to='host_photos/', null=True, blank=True)
    def save(self, *args, **kwargs):
        if not self.username:
            self.username = f"{self.first_name} {self.last_name}".strip()
        super().save(*args, **kwargs)

    def __str__(self):
        return self.username
