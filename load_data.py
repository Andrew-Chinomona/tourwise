"""
Script to load currencies and amenities into the database
Run with: python load_data.py
"""
import os
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'tourwise_website.settings')
django.setup()

from listings.models import Currency, Amenity

def load_currencies():
    """Load currency data"""
    print("Loading currencies...")
    
    # Clear existing currencies (optional)
    Currency.objects.all().delete()
    
    currencies = [
        {'code': 'ZWL', 'name': 'Zimbabwean Dollar', 'symbol': 'Z$'},
        {'code': 'USD', 'name': 'US Dollar', 'symbol': '$'},
        {'code': 'EUR', 'name': 'Euro', 'symbol': '€'},
        {'code': 'GBP', 'name': 'British Pound', 'symbol': '£'},
        {'code': 'ZAR', 'name': 'South African Rand', 'symbol': 'R'},
    ]
    
    for curr_data in currencies:
        curr = Currency.objects.create(**curr_data)
        print(f'  ✓ Created: {curr.code} - {curr.name} ({curr.symbol})')
    
    print(f"✅ Loaded {Currency.objects.count()} currencies\n")

def load_amenities():
    """Load amenity data"""
    print("Loading amenities...")
    
    # Clear existing amenities (optional)
    Amenity.objects.all().delete()
    
    amenities = [
        {'name': 'WiFi', 'icon': 'wifi'},
        {'name': 'Air Conditioning', 'icon': 'snowflake'},
        {'name': 'Parking', 'icon': 'car'},
        {'name': 'Swimming Pool', 'icon': 'swimming-pool'},
        {'name': 'Garden', 'icon': 'tree'},
        {'name': 'Security', 'icon': 'shield-alt'},
        {'name': 'Gym/Fitness Center', 'icon': 'dumbbell'},
        {'name': 'Laundry', 'icon': 'tshirt'},
        {'name': 'Furnished', 'icon': 'couch'},
        {'name': 'Kitchen', 'icon': 'utensils'},
        {'name': 'Balcony/Terrace', 'icon': 'home'},
        {'name': 'Pet Friendly', 'icon': 'paw'},
        {'name': 'Heating', 'icon': 'fire'},
        {'name': 'TV/Cable', 'icon': 'tv'},
        {'name': 'Generator/Backup Power', 'icon': 'bolt'},
        {'name': 'Water Tank', 'icon': 'tint'},
        {'name': 'Borehole', 'icon': 'water'},
        {'name': 'Solar Power', 'icon': 'sun'},
        {'name': 'Dishwasher', 'icon': 'sink'},
        {'name': 'Microwave', 'icon': 'microwave'},
        {'name': 'Washing Machine', 'icon': 'tshirt'},
        {'name': 'Dryer', 'icon': 'wind'},
        {'name': 'Alarm System', 'icon': 'bell'},
        {'name': 'CCTV', 'icon': 'video'},
        {'name': 'Electric Fence', 'icon': 'fence'},
    ]
    
    for amenity_data in amenities:
        amenity = Amenity.objects.create(**amenity_data)
        print(f'  ✓ Created: {amenity.name}')
    
    print(f"✅ Loaded {Amenity.objects.count()} amenities\n")

if __name__ == '__main__':
    print("\n" + "="*60)
    print("  LOADING CURRENCIES AND AMENITIES")
    print("="*60 + "\n")
    
    try:
        load_currencies()
        load_amenities()
        
        print("="*60)
        print("  ✅ ALL DATA LOADED SUCCESSFULLY!")
        print("="*60)
        print(f"\nSummary:")
        print(f"  - Currencies: {Currency.objects.count()}")
        print(f"  - Amenities: {Amenity.objects.count()}")
        print()
        
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
