from django.db.models.signals import post_save
from django.dispatch import receiver
from invoices.models import Invoice, InvoicePayment
from .services import NotificationService

@receiver(post_save, sender=Invoice)
def send_invoice_created_notification(sender, instance, created, **kwargs):
    if created:
        NotificationService.notify_invoice_created(instance)

@receiver(post_save, sender=InvoicePayment)
def send_invoice_paid_notification(sender, instance, created, **kwargs):
    if created:
        invoice = instance.invoice
        invoice.status = 'paid'
        invoice.payment_received = True
        invoice.save()
        NotificationService.notify_invoice_paid(invoice, instance)