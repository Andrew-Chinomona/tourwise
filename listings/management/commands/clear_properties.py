"""
Django management command to delete all properties from the database
Run with: python manage.py clear_properties
"""
from django.core.management.base import BaseCommand
from listings.models import Property, PropertyImage


class Command(BaseCommand):
    help = 'Delete all properties from the database'

    def handle(self, *args, **options):
        self.stdout.write("Starting to delete all properties...")
        self.stdout.write("=" * 60)
        
        # Count properties before deletion
        property_count = Property.objects.count()
        image_count = PropertyImage.objects.count()
        
        if property_count == 0:
            self.stdout.write(self.style.WARNING("No properties found in the database."))
            return
        
        self.stdout.write(f"Found {property_count} properties and {image_count} property images.")
        
        try:
            # Delete all property images first
            PropertyImage.objects.all().delete()
            self.stdout.write(self.style.SUCCESS(f"Deleted {image_count} property images"))
            
            # Delete all properties
            Property.objects.all().delete()
            self.stdout.write(self.style.SUCCESS(f"Deleted {property_count} properties"))
            
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"Error deleting properties: {e}"))
            return
        
        self.stdout.write("\n" + "=" * 60)
        self.stdout.write(self.style.SUCCESS("All properties deleted successfully!"))
        self.stdout.write("=" * 60)
