from django.core.management.base import BaseCommand
from django.utils import timezone
from chatbot.models import ChatSession, ChatMessage
from django.contrib.auth import get_user_model
from datetime import timedelta

User = get_user_model()


class Command(BaseCommand):
    help = 'Clean up expired chat sessions and enforce session limits'

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show what would be deleted without actually deleting',
        )
        parser.add_argument(
            '--enforce-limits',
            action='store_true',
            help='Enforce 10 session limit per user',
        )

    def handle(self, *args, **options):
        dry_run = options['dry_run']
        enforce_limits = options['enforce_limits']

        self.stdout.write(
            self.style.SUCCESS('Starting chat history cleanup...')
        )

        # Clean up expired sessions (older than 24 hours)
        cutoff_time = timezone.now() - timedelta(hours=24)
        expired_sessions = ChatSession.objects.filter(created_at__lt=cutoff_time)
        expired_count = expired_sessions.count()

        if dry_run:
            self.stdout.write(
                self.style.WARNING(
                    f'DRY RUN: Would delete {expired_count} expired sessions'
                )
            )
        else:
            expired_sessions.delete()
            self.stdout.write(
                self.style.SUCCESS(f'Deleted {expired_count} expired sessions')
            )

        # Enforce session limits per user
        if enforce_limits:
            total_deleted = 0
            users_with_excess = 0

            for user in User.objects.filter(is_active=True):
                user_sessions = ChatSession.objects.filter(
                    user=user,
                    is_active=True
                ).order_by('-updated_at')

                if user_sessions.count() > 10:
                    users_with_excess += 1
                    sessions_to_delete = user_sessions[10:]  # Keep only 10 most recent
                    count = sessions_to_delete.count()
                    total_deleted += count

                    if dry_run:
                        self.stdout.write(
                            self.style.WARNING(
                                f'DRY RUN: Would delete {count} sessions for user {user.username}'
                            )
                        )
                    else:
                        sessions_to_delete.delete()
                        self.stdout.write(
                            self.style.SUCCESS(
                                f'Deleted {count} sessions for user {user.username}'
                            )
                        )

            if dry_run:
                self.stdout.write(
                    self.style.WARNING(
                        f'DRY RUN: Would affect {users_with_excess} users, total {total_deleted} sessions'
                    )
                )
            else:
                self.stdout.write(
                    self.style.SUCCESS(
                        f'Enforced limits for {users_with_excess} users, deleted {total_deleted} sessions'
                    )
                )

        # Clean up orphaned messages (messages without sessions)
        orphaned_messages = ChatMessage.objects.filter(session__isnull=True)
        orphaned_count = orphaned_messages.count()

        if orphaned_count > 0:
            if dry_run:
                self.stdout.write(
                    self.style.WARNING(
                        f'DRY RUN: Would delete {orphaned_count} orphaned messages'
                    )
                )
            else:
                orphaned_messages.delete()
                self.stdout.write(
                    self.style.SUCCESS(f'Deleted {orphaned_count} orphaned messages')
                )

        self.stdout.write(
            self.style.SUCCESS('Chat history cleanup completed!')
        )