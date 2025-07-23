from django.db import models
from django.conf import settings
from django.utils import timezone
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


class ChatMessage(models.Model):
    """Represents individual messages within a chat session"""
    SENDER_CHOICES = [
        ('user', 'User'),
        ('bot', 'Bot'),
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