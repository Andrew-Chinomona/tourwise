from django.core.management.base import BaseCommand
from chatbot.models import CBDLocation


class Command(BaseCommand):
    help = 'Populate CBD location data for Zimbabwean cities'

    def handle(self, *args, **options):
        # CBD data for major Zimbabwean cities
        cbd_data = [
            {
                'name': 'Harare CBD',
                'city': 'Harare',
                'latitude': -17.8252,
                'longitude': 31.0335,
                'description': 'Central Business District of Harare, the capital city'
            },
            {
                'name': 'Bulawayo CBD',
                'city': 'Bulawayo',
                'latitude': -20.1325,
                'longitude': 28.6264,
                'description': 'Central Business District of Bulawayo'
            },
            {
                'name': 'Mutare CBD',
                'city': 'Mutare',
                'latitude': -18.9726,
                'longitude': 32.6706,
                'description': 'Central Business District of Mutare'
            },
            {
                'name': 'Gweru CBD',
                'city': 'Gweru',
                'latitude': -19.4500,
                'longitude': 29.8167,
                'description': 'Central Business District of Gweru'
            },
            {
                'name': 'Kwekwe CBD',
                'city': 'Kwekwe',
                'latitude': -18.9167,
                'longitude': 29.8167,
                'description': 'Central Business District of Kwekwe'
            },
            {
                'name': 'Masvingo CBD',
                'city': 'Masvingo',
                'latitude': -20.0667,
                'longitude': 30.8333,
                'description': 'Central Business District of Masvingo'
            },
            {
                'name': 'Chitungwiza CBD',
                'city': 'Chitungwiza',
                'latitude': -18.0000,
                'longitude': 31.0500,
                'description': 'Central Business District of Chitungwiza'
            },
            {
                'name': 'Epworth CBD',
                'city': 'Epworth',
                'latitude': -17.8833,
                'longitude': 31.1500,
                'description': 'Central Business District of Epworth'
            },
            {
                'name': 'Ruwa CBD',
                'city': 'Ruwa',
                'latitude': -17.8833,
                'longitude': 31.2333,
                'description': 'Central Business District of Ruwa'
            },
            {
                'name': 'Chegutu CBD',
                'city': 'Chegutu',
                'latitude': -18.1333,
                'longitude': 30.1500,
                'description': 'Central Business District of Chegutu'
            },
            {
                'name': 'Kadoma CBD',
                'city': 'Kadoma',
                'latitude': -18.3333,
                'longitude': 29.9167,
                'description': 'Central Business District of Kadoma'
            },
            {
                'name': 'Marondera CBD',
                'city': 'Marondera',
                'latitude': -18.1833,
                'longitude': 31.5500,
                'description': 'Central Business District of Marondera'
            }
        ]

        created_count = 0
        updated_count = 0

        for cbd_info in cbd_data:
            cbd, created = CBDLocation.objects.get_or_create(
                name=cbd_info['name'],
                defaults={
                    'city': cbd_info['city'],
                    'latitude': cbd_info['latitude'],
                    'longitude': cbd_info['longitude'],
                    'description': cbd_info['description'],
                    'is_active': True
                }
            )

            if created:
                created_count += 1
                self.stdout.write(
                    self.style.SUCCESS(f'Created CBD: {cbd.name}')
                )
            else:
                # Update existing record
                cbd.city = cbd_info['city']
                cbd.latitude = cbd_info['latitude']
                cbd.longitude = cbd_info['longitude']
                cbd.description = cbd_info['description']
                cbd.is_active = True
                cbd.save()
                updated_count += 1
                self.stdout.write(
                    self.style.WARNING(f'Updated CBD: {cbd.name}')
                )

        self.stdout.write(
            self.style.SUCCESS(
                f'Successfully processed CBD data. Created: {created_count}, Updated: {updated_count}'
            )
        )