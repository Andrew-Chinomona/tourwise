from django.db import models
from django.contrib.auth.models import AbstractUser #import abstarctuser from djangos built in auth system

class CustomUser(AbstractUser): #custom user model, which inherits everything from AbstractUser.
    USER_TYPE_CHOICES = (
    ('host', 'Host'),
    ('tenant', 'Tenant'),
    )

    user_type = models.CharField(max_length = 10, choices = USER_TYPE_CHOICES, default='tenant')
    phone_number = models.CharField(max_length = 20, blank = True, null = True)

    def __str__(self):
        return self.username