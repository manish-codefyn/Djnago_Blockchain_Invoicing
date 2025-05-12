from django.template.loader import render_to_string
from django.core.mail import send_mail
from django.conf import settings
from django.urls import reverse
from .models import Notification, NotificationTemplate
from clients.models import Client
from invoices.models import Invoice
import logging

logger = logging.getLogger(__name__)

class NotificationService:
    @staticmethod
    def get_template(notification_type):
        try:
            return NotificationTemplate.objects.get(
                notification_type=notification_type,
                is_active=True
            )
        except NotificationTemplate.DoesNotExist:
            logger.error(f"Notification template for {notification_type} not found")
            return None

    @staticmethod
    def create_notification(recipient, notification_type, context=None, send_email=False):
        template = NotificationService.get_template(notification_type)
        if not template:
            return None

        # Sanitize context: ensure it's JSON serializable
        clean_context = NotificationService.sanitize_context(context or {})

        notification = Notification.objects.create(
            recipient=recipient,
            template=template,
            context=clean_context
        )

        if send_email:
            notification.send_email()

        return notification

    @staticmethod
    def sanitize_context(context):
        """Sanitize context by converting model instances and non-serializable objects."""
        def serialize(obj):
            if hasattr(obj, "id"):
                return str(obj.id)
            if hasattr(obj, "__str__"):
                return str(obj)
            return None

        serialized = {}
        for key, value in context.items():
            if isinstance(value, (Invoice, Client)):
                serialized[key] = {
                    'id': str(value.id),
                    'name': str(value),
                }
            elif hasattr(value, 'isoformat'):  # For datetime/date
                serialized[key] = value.isoformat()
            elif isinstance(value, (int, float, str, bool, type(None))):
                serialized[key] = value
            else:
                serialized[key] = serialize(value)
        return serialized

    @staticmethod
    def notify_invoice_created(invoice, request=None):
        context = {
            'invoice_id': str(invoice.id),
            'invoice_number': invoice.invoice_number,
            'client_name': str(invoice.client),
            'total_amount': float(invoice.total_amount),
            'due_date': invoice.due_date,
            'invoice_url': request.build_absolute_uri(
                reverse('invoices:invoice_detail', kwargs={'invoice_id': str(invoice.id)})
            ) if request else '',
        }

        if invoice.client.user:
            NotificationService.create_notification(
                recipient=invoice.client.user,
                notification_type='invoice_created',
                context=context,
                send_email=True
            )

        NotificationService.create_notification(
            recipient=invoice.user,
            notification_type='invoice_created',
            context=context
        )

    @staticmethod
    def notify_invoice_paid(invoice, payment, request=None):
        context = {
            'invoice_id': str(invoice.id),
            'invoice_number': invoice.invoice_number,
            'client_name': str(invoice.client),
            'amount_paid': float(payment.amount),
            'payment_method': payment.payment_method,
            'payment_date': payment.payment_date,
            'invoice_url': request.build_absolute_uri(
                reverse('invoices:invoice_detail', kwargs={'invoice_id': str(invoice.id)})
            ) if request else '',
            'payment_url': request.build_absolute_uri(
                reverse('invoices:payment_detail', kwargs={'payment_id': str(payment.id)})
            ) if request else '',
        }

        if invoice.client.user:
            NotificationService.create_notification(
                recipient=invoice.client.user,
                notification_type='invoice_paid',
                context=context,
                send_email=True
            )

        NotificationService.create_notification(
            recipient=invoice.user,
            notification_type='payment_received',
            context=context,
            send_email=True
        )

    @staticmethod
    def notify_invoice_overdue(invoice, request=None):
        context = {
            'invoice_id': str(invoice.id),
            'invoice_number': invoice.invoice_number,
            'client_name': str(invoice.client),
            'total_amount': float(invoice.total_amount),
            'due_date': invoice.due_date,
            'days_overdue': invoice.days_overdue,
            'invoice_url': request.build_absolute_uri(
                reverse('invoices:invoice_detail', kwargs={'invoice_id': str(invoice.id)})
            ) if request else '',
        }

        if invoice.client.user:
            NotificationService.create_notification(
                recipient=invoice.client.user,
                notification_type='invoice_overdue',
                context=context,
                send_email=True
            )

        NotificationService.create_notification(
            recipient=invoice.user,
            notification_type='invoice_overdue',
            context=context,
            send_email=True
        )

@staticmethod
def send_client_welcome(client, request=None):
    # Ensure the client has an associated user
    if not hasattr(client, 'user') or not client.user:
        return

    # Build context for notification
    context = {
        'client_name': str(client),
        'client_portal_url': (
            request.build_absolute_uri(reverse('client_portal'))
            if request else ''
        ),
    }

    # Trigger the notification creation
    NotificationService.create_notification(
        recipient=client.user,
        notification_type='client_welcome',
        context=context,
        send_email=True
    )