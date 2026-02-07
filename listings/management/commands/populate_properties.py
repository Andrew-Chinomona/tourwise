"""
Django management command to populate database with 30 sample properties
Run with: python manage.py populate_properties
"""
from django.core.management.base import BaseCommand
from django.contrib.gis.geos import Point
from decimal import Decimal
from listings.models import Property, PropertyImage, Currency, Amenity
from accounts.models import CustomUser


class Command(BaseCommand):
    help = 'Populate database with 30 sample properties in Harare, Zimbabwe'

    # Harare suburbs and locations with coordinates
    HARARE_LOCATIONS = [
        {'suburb': 'Borrowdale', 'street': '15 Borrowdale Road', 'coords': (-17.7842, 31.0894)},
        {'suburb': 'Mount Pleasant', 'street': '23 Mount Pleasant Drive', 'coords': (-17.7975, 31.0609)},
        {'suburb': 'Avondale', 'street': '8 King George Road', 'coords': (-17.8037, 31.0429)},
        {'suburb': 'Highlands', 'street': '42 Enterprise Road', 'coords': (-17.7865, 31.0363)},
        {'suburb': 'Greendale', 'street': '67 Greendale Avenue', 'coords': (-17.8156, 31.0815)},
        {'suburb': 'Greystone Park', 'street': '12 Greystone Drive', 'coords': (-17.8250, 31.0750)},
        {'suburb': 'Marlborough', 'street': '34 Marlborough Road', 'coords': (-17.7500, 31.1050)},
        {'suburb': 'Gunhill', 'street': '89 Gunhill Road', 'coords': (-17.7688, 31.0688)},
        {'suburb': 'Alexandra Park', 'street': '56 Park Lane', 'coords': (-17.8193, 31.0507)},
        {'suburb': 'Newlands', 'street': '78 Enterprise Road', 'coords': (-17.8350, 31.0950)},
        {'suburb': 'Chisipite', 'street': '45 Chisipite Road', 'coords': (-17.7750, 31.0850)},
        {'suburb': 'Ballantyne Park', 'street': '90 Ballantyne Avenue', 'coords': (-17.7925, 31.0725)},
        {'suburb': 'Glen Lorne', 'street': '123 Glen Lorne Drive', 'coords': (-17.7500, 31.0500)},
        {'suburb': 'Borrowdale Brooke', 'street': '67 Brooke Avenue', 'coords': (-17.7700, 31.1000)},
        {'suburb': 'Pomona', 'street': '34 Pomona Road', 'coords': (-17.8450, 31.0200)},
        {'suburb': 'Hatfield', 'street': '88 Hatfield Drive', 'coords': (-17.7600, 31.0300)},
        {'suburb': 'Msasa', 'street': '45 Industrial Road', 'coords': (-17.8100, 31.1200)},
        {'suburb': 'Belvedere', 'street': '29 Belvedere Avenue', 'coords': (-17.8300, 31.0600)},
        {'suburb': 'Mabelreign', 'street': '71 Mabelreign Road', 'coords': (-17.8150, 31.0350)},
        {'suburb': 'Westgate', 'street': '102 Westgate Drive', 'coords': (-17.8200, 31.0200)},
        {'suburb': 'Glen View', 'street': '55 Glen View Avenue', 'coords': (-17.9000, 30.9800)},
        {'suburb': 'Warren Park', 'street': '83 Warren Park Drive', 'coords': (-17.8400, 30.9900)},
        {'suburb': 'Mbare', 'street': '12 Mbare Road', 'coords': (-17.8700, 31.0400)},
        {'suburb': 'Milton Park', 'street': '48 Milton Drive', 'coords': (-17.8250, 31.0450)},
        {'suburb': 'Strathaven', 'street': '91 Strathaven Road', 'coords': (-17.7400, 31.0700)},
        {'suburb': 'Kambuzuma', 'street': '23 Kambuzuma Street', 'coords': (-17.8800, 30.9700)},
        {'suburb': 'Ardbennie', 'street': '76 Ardbennie Avenue', 'coords': (-17.8600, 31.0100)},
        {'suburb': 'Waterfalls', 'street': '39 Waterfalls Road', 'coords': (-17.9200, 31.0700)},
        {'suburb': 'Tynwald', 'street': '64 Tynwald Drive', 'coords': (-17.7800, 31.0250)},
        {'suburb': 'Ashdown Park', 'street': '17 Ashdown Road', 'coords': (-17.7650, 31.0400)},
    ]

    PROPERTY_TYPES = ['house', 'apartment', 'airbnb', 'guesthouse']

    PROPERTY_DESCRIPTIONS = [
        "Modern and spacious property with excellent natural lighting. Perfect for families looking for comfort and style.",
        "Beautifully designed home with contemporary finishes. Features open-plan living spaces and a private garden.",
        "Elegant property in a prime location. Offers privacy, security, and easy access to amenities.",
        "Luxurious residence with high-end fixtures and fittings. Ideal for executive living.",
        "Charming property with a warm atmosphere. Well-maintained and move-in ready.",
        "Stunning home featuring modern architecture and premium materials throughout.",
        "Comfortable living space with generous room sizes. Perfect for entertaining guests.",
        "Newly renovated property with state-of-the-art facilities. Eco-friendly and sustainable design.",
        "Spacious family home in a quiet, established neighborhood. Close to schools and shopping centers.",
        "Contemporary design meets functionality in this beautiful property. Features smart home technology.",
    ]

    # Only use these interior images (front.png will be the main image)
    INTERIOR_IMAGE_FILES = [
        'lounge.png',
        'kitchen.png',
        'garage.png',
        'bedroom.png',
        'bathroom.png',
        'backyard.png'
    ]

    def handle(self, *args, **options):
        self.stdout.write("Starting property population script...")
        self.stdout.write("=" * 60)
        
        # Get or create a host user
        try:
            host_user = CustomUser.objects.filter(user_type='host').first()
            if not host_user:
                self.stdout.write(self.style.WARNING("No host user found. Creating a sample host..."))
                host_user = CustomUser.objects.create_user(
                    email='samplehost@tourwise.com',
                    password='password123',
                    user_type='host',
                    first_name='Sample',
                    last_name='Host',
                    phone_number='+263771234567'
                )
                self.stdout.write(self.style.SUCCESS(f"Created host user: {host_user.email}"))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"Error getting/creating host user: {e}"))
            return
        
        # Get USD currency
        try:
            usd_currency = Currency.objects.get(code='USD')
        except Currency.DoesNotExist:
            self.stdout.write(self.style.WARNING("USD currency not found. Creating it..."))
            usd_currency = Currency.objects.create(code='USD', name='US Dollar', symbol='$')
        
        # Get some amenities
        amenities_list = list(Amenity.objects.all()[:8])
        
        self.stdout.write(f"Starting to create 30 properties in Harare...")
        properties_created = 0
        
        for i in range(30):
            try:
                location_data = self.HARARE_LOCATIONS[i]
                property_type = self.PROPERTY_TYPES[i % len(self.PROPERTY_TYPES)]
                
                # Create property
                property_obj = Property.objects.create(
                    owner=host_user,
                    property_type=property_type,
                    title=f"{property_type.title()} in {location_data['suburb']}",
                    description=self.PROPERTY_DESCRIPTIONS[i % len(self.PROPERTY_DESCRIPTIONS)],
                    street_address=location_data['street'],
                    suburb=location_data['suburb'],
                    city='Harare',
                    state_or_region='Harare Province',
                    country='Zimbabwe',
                    location=Point(location_data['coords'][1], location_data['coords'][0]),  # longitude, latitude
                    bedrooms=(i % 5) + 1,  # 1-5 bedrooms
                    bathrooms=(i % 3) + 1,  # 1-3 bathrooms
                    area=80 + (i * 10),  # 80-370 sqm
                    price=Decimal(str(500 + (i * 50))),  # $500-$1950
                    currency=usd_currency,
                    contact_phone='+263771234567',
                    contact_email='info@tourwise.co.zw',
                    listing_type='priority' if i % 5 == 0 else 'normal',
                    is_paid=True
                )
                
                # Add amenities (4-6 random amenities per property)
                if amenities_list:
                    num_amenities = 4 + (i % 3)  # 4-6 amenities
                    property_obj.amenities.add(*amenities_list[:num_amenities])
                
                # Set main image (always use front.png)
                property_obj.main_image = 'property_images/front.png'
                property_obj.save()
                
                # Add interior images (all 6 interior images for each property)
                for image_file in self.INTERIOR_IMAGE_FILES:
                    PropertyImage.objects.create(
                        property=property_obj,
                        image=f'property_images/{image_file}'
                    )
                
                properties_created += 1
                self.stdout.write(self.style.SUCCESS(f"Created property {properties_created}: {property_obj.title}"))
                
            except Exception as e:
                self.stdout.write(self.style.ERROR(f"Error creating property {i + 1}: {e}"))
                continue
        
        self.stdout.write("\n" + "=" * 60)
        self.stdout.write(self.style.SUCCESS(f"Successfully created {properties_created} out of 30 properties!"))
        self.stdout.write("=" * 60)
