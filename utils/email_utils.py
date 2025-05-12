from django.core.mail import EmailMessage
from django.template.loader import render_to_string
from django.conf import settings

def send_invoice_email(invoice, recipient_email):
    subject = f"Invoice #{invoice.invoice_number}"
    message = render_to_string('email/invoice_email.html', {'invoice': invoice})
    email = EmailMessage(subject, message, settings.DEFAULT_FROM_EMAIL, [recipient_email])
    email.content_subtype = 'html'
    email.send()
