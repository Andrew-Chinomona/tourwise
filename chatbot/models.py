from django.db import models
from django.conf import settings
from django.utils import timezone
from django.db.models.signals import post_save
from django.dispatch import receiver
from datetime import timedelta
import uuid


class ChatSession(models.Model):
    """Represents a chat session that can contain multiple messages"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, null=True, blank=True)
    session_id = models.CharField(max_length=255, unique=True, null=True, blank=True)
    title = models.CharField(max_length=255, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_active = models.BooleanField(default=True)
    has_ai_response = models.BooleanField(default=False)  # Track if AI has responded

    class Meta:
        ordering = ['-updated_at']

    def __str__(self):
        if self.title:
            return f"{self.title} ({self.created_at.strftime('%Y-%m-%d %H:%M')})"
        return f"Chat {self.id} ({self.created_at.strftime('%Y-%m-%d %H:%M')})"

    def get_message_count(self):
        return self.messages.count()

    def get_last_message(self):
        return self.messages.last()

    def generate_title(self):
        """Generate a title based on the first user message"""
        first_user_message = self.messages.filter(sender='user').first()
        if first_user_message:
            # Truncate to 50 characters and add ellipsis if needed
            title = first_user_message.content[:50]
            if len(first_user_message.content) > 50:
                title += "..."
            self.title = title
            self.save()

    def is_expired(self):
        """Check if session is older than 24 hours"""
        return timezone.now() - self.created_at > timedelta(hours=24)

    @classmethod
    def cleanup_expired_sessions(cls):
        """Delete sessions older than 24 hours"""
        cutoff_time = timezone.now() - timedelta(hours=24)
        expired_sessions = cls.objects.filter(created_at__lt=cutoff_time)
        count = expired_sessions.count()
        expired_sessions.delete()
        return count

    @classmethod
    def enforce_session_limit(cls, user):
        """Enforce maximum 10 sessions per user by deleting oldest ones"""
        if not user or not user.is_authenticated:
            return 0

        user_sessions = cls.objects.filter(user=user, is_active=True).order_by('-updated_at')
        if user_sessions.count() > 10:
            sessions_to_delete = user_sessions[10:]  # Keep only the 10 most recent
            count = sessions_to_delete.count()
            sessions_to_delete.delete()
            return count
        return 0


class ChatMessage(models.Model):
    """Represents individual messages within a chat session"""
    SENDER_CHOICES = [
        ('user', 'User'),
        ('bot', 'Bot'),
        ('system', 'System'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    session = models.ForeignKey(ChatSession, on_delete=models.CASCADE, related_name='messages')
    sender = models.CharField(max_length=10, choices=SENDER_CHOICES)
    content = models.TextField()
    message_type = models.CharField(max_length=20, default='text')  # text, property_results, etc.
    metadata = models.JSONField(default=dict, blank=True)  # Store additional data like property results
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['created_at']

    def __str__(self):
        return f"{self.sender}: {self.content[:50]}..."

    @property
    def is_user_message(self):
        return self.sender == 'user'

    @property
    def is_bot_message(self):
        return self.sender == 'bot'

    @property
    def is_system_message(self):
        return self.sender == 'system'


# Signal handlers for automatic cleanup and session management
@receiver(post_save, sender=ChatMessage)
def handle_message_save(sender, instance, created, **kwargs):
    """Handle automatic session management when messages are saved"""
    if created:
        session = instance.session

        # Mark session as having AI response if bot message is saved
        if instance.sender == 'bot' and not session.has_ai_response:
            session.has_ai_response = True
            session.save(update_fields=['has_ai_response'])

        # Generate title if this is the first user message
        if instance.sender == 'user' and not session.title:
            session.generate_title()

        # Update session timestamp
        session.save(update_fields=['updated_at'])


class CBDLocation(models.Model):
    """Stores CBD/location data for Zimbabwean cities"""
    name = models.CharField(max_length=100, unique=True)
    city = models.CharField(max_length=100)
    latitude = models.FloatField()
    longitude = models.FloatField()
    description = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['name']

    def __str__(self):
        return f"{self.name} ({self.city})"


class ConversationState(models.Model):
    """Tracks conversation state for follow-up questions"""
    session = models.OneToOneField(ChatSession, on_delete=models.CASCADE, related_name='conversation_state')
    waiting_for_location = models.BooleanField(default=False)
    waiting_for_cbd_clarification = models.BooleanField(default=False)
    pending_search_query = models.TextField(blank=True)
    suggested_cbds = models.JSONField(default=list, blank=True)  # Store suggested CBDs
    selected_cbd = models.ForeignKey(CBDLocation, on_delete=models.SET_NULL, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"State for {self.session}"

    def reset_state(self):
        """Reset all waiting flags"""
        self.waiting_for_location = False
        self.waiting_for_cbd_clarification = False
        self.pending_search_query = ""
        self.suggested_cbds = []
        self.selected_cbd = None
        self.save()