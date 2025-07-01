from django.contrib import admin
from .models import Property

# admin.site.register(Property)  #registering the model in django admin
# listings/admin.py
from django.contrib import admin
from .models import Property, PropertyImage

class PropertyImageInline(admin.TabularInline):  # or use StackedInline
    model = PropertyImage
    extra = 3  # Number of blank image fields shown by default
    max_num = 10  # Optional: Limit number of images
    fields = ['image',]
    verbose_name_plural = 'Interior Photos'

@admin.register(Property)
class PropertyAdmin(admin.ModelAdmin):
    list_display = ['title']  # Adjust based on your fields
    inlines = [PropertyImageInline]


