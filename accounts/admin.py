from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.core.exceptions import PermissionDenied
from .models import CustomUser


class CustomUserAdmin(UserAdmin):
    model = CustomUser

    # Fields to show in the list view
    list_display = ['username', 'email', 'phone_number', 'user_type', 'is_superuser', 'is_staff']

    # Fields shown when editing a user in admin
    fieldsets = UserAdmin.fieldsets + (
        (None, {'fields': ('phone_number', 'user_type')}),
    )

    # Fields shown when creating a user in admin
    add_fieldsets = UserAdmin.add_fieldsets + (
        (None, {'fields': ('phone_number', 'user_type')}),
    )

    # Prevent deletion of superusers via the admin panel
    def delete_model(self, request, obj):
        if obj.is_superuser:
            raise PermissionDenied("You cannot delete a superuser from the admin panel.")
        super().delete_model(request, obj)

    # Prevent bulk deletion of superusers via the admin actions dropdown
    def delete_queryset(self, request, queryset):
        if queryset.filter(is_superuser=True).exists():
            raise PermissionDenied("You cannot delete one or more superusers.")
        super().delete_queryset(request, queryset)


admin.site.register(CustomUser, CustomUserAdmin)
