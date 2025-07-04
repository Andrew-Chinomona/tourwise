from django.db import models
from django.conf import settings
from listings.models import Property

class Payment(models.Model):
    amount = models.DecimalField(max_digits=6, decimal_places=2, help_text="Amount in USD",)

    LISTING_TYPE_CHOICES = Property.LISTING_TYPE_CHOICES
    listing_type = models.CharField(
        max_length=10,
        choices=LISTING_TYPE_CHOICES,
        default='normal',
    )

    PENDING = 'pending'
    PAID = 'paid'
    FAILED = 'failed'
    REFUNDED = 'refunded'

    STATUS_CHOICES = [
        (PENDING, 'Pending'),
        (PAID, 'Paid'),
        (FAILED, 'Failed'),
        (REFUNDED, 'Refunded'),
    ]

    PAYMENT_METHOD_CHOICES = [
        ('card', 'Credit Card'),
        ('mobile', 'Mobile Money'),
        ('bank', 'Bank Transfer'),
    ]

    property = models.OneToOneField(
        Property,
        on_delete=models.CASCADE,
        related_name='payment'
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='payments'
    )
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default=PENDING
    )
    payment_method = models.CharField(
        max_length=10,
        choices=PAYMENT_METHOD_CHOICES,
        blank=True,
        null=True
    )
    reference = models.CharField(
        max_length=255,
        unique=True,
        blank=True,
        null=True,
        help_text="Payment reference from payment gateway"
    )
    poll_url = models.URLField(
        blank=True,
        null=True,
        help_text="URL to poll for payment status updates"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Payment'
        verbose_name_plural = 'Payments'

    def __str__(self):
        return f"Payment #{self.id} - {self.property.title} ({self.get_status_display()})"

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)

