from django.core.management.base import BaseCommand
from accounts.models import CustomUser

class Command(BaseCommand):
    help = 'Delete all test users except superusers'

    def handle(self, *args, **kwargs):
        count = CustomUser.objects.filter(is_superuser=False).delete()[0]
        self.stdout.write(self.style.SUCCESS(f'Deleted {count} non-superuser accounts.'))
