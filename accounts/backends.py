from django.contrib.auth.backends import ModelBackend
from django.contrib.auth import get_user_model
from django.db import models

User = get_user_model()

class EmailOrPhoneBackend(ModelBackend):
    def authenticate(self, request, username=None, password=None, **kwargs):
        try:
            user = User.objects.get(
                models.Q(email__iexact=username) |
                models.Q(phone_number__iexact=username)
            )
        except User.DoesNotExist:
            return None

        if user.check_password(password):
            return user
        return None
