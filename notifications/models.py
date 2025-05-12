from django.db import models
from django.contrib.auth import get_user_model
from django.urls import reverse
from django.template.loader import render_to_string
from django.core.mail import send_mail
from django.conf import settings
import uuid
from django.utils import timezone
from django.utils.html import strip_tags
import logging
logger = logging.getLogger(__name__)
User = get_user_model()

class NotificationTemplate(models.Model):
    NOTIFICATION_TYPES = [
        ('invoice_created', 'Invoice Created'),
        ('invoice_paid', 'Invoice Paid'),
        ('invoice_overdue', 'Invoice Overdue'),
        ('payment_received', 'Payment Received'),
        ('client_welcome', 'Client Welcome'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=100)
    notification_type = models.CharField(max_length=50, choices=NOTIFICATION_TYPES, unique=True)
    subject = models.CharField(max_length=200)
    template = models.TextField(help_text="HTML template for the notification")
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.name} ({self.get_notification_type_display()})"

class Notification(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    recipient = models.ForeignKey(User, on_delete=models.CASCADE, related_name='notifications')
    template = models.ForeignKey(NotificationTemplate, on_delete=models.PROTECT)
    context = models.JSONField(default=dict)
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    read_at = models.DateTimeField(null=True, blank=True)
    sent_via_email = models.BooleanField(default=False)
    email_sent_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"Notification for {self.recipient} - {self.template.name}"

    def mark_as_read(self):
        if not self.is_read:
            self.is_read = True
            self.read_at = timezone.now()
            self.save()
            
    def get_absolute_url(self):
        if 'invoice_id' in self.context:
            return reverse('invoices:invoice-detail', kwargs={'pk': self.context['invoice_id']})
        return reverse('notifications:notifications_list')
    
    def render_content(self):
        return render_to_string(
            f"notifications/{self.template.notification_type}.html",
            self.context
        )

    def send_email(self):
        if not settings.DEFAULT_FROM_EMAIL:
            return False

        try:
            html_content = self.render_content()
            send_mail(
                subject=self.template.subject,
                message=strip_tags(html_content),  # Plain text version
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[self.recipient.email],
                html_message=html_content,
                fail_silently=False,
            )
            self.sent_via_email = True
            self.email_sent_at = timezone.now()
            self.save()
            return True
        except Exception as e:
            logger.error(f"Failed to send notification email: {e}")
            return False