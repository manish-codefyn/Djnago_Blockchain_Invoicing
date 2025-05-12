import uuid
from django.db import models
from django.contrib.auth import get_user_model
from django.core.validators import MinValueValidator
from django.utils import timezone
from django.db.models import Sum, F, ExpressionWrapper, DecimalField
from django.core.exceptions import ValidationError
from django.conf import settings
from django.urls import reverse
from cryptography.fernet import Fernet
from blockchain import Blockchain
from clients.models import Client
from core.models import SiteSetting
import hashlib
import json
import logging
logger = logging.getLogger(__name__)
from hashlib import sha256
User = settings.AUTH_USER_MODEL

class Invoice(models.Model):
    STATUS_CHOICES = [
        ('draft', 'Draft'),
        ('sent', 'Sent'),
        ('paid', 'Paid'),
        ('overdue', 'Overdue'),
        ('cancelled', 'Cancelled'),
        ('disputed', 'Disputed'),
    ]
    
    PAYMENT_METHOD_CHOICES = [
        ('bank', 'Bank Transfer'),
        ('credit_card', 'Credit Card'),
        ('paypal', 'PayPal'),
        ('crypto', 'Cryptocurrency'),
        ('other', 'Other'),
        ('online', 'Online'),  
        ('check', 'By Check (Bank Transfer)'), 
        ('cash', 'Cash'), 
    ]
    
    CURRENCY_CHOICES = [
        ('USD', 'US Dollar ($)'),
        ('EUR', 'Euro (€)'),
        ('GBP', 'British Pound (£)'),
        ('JPY', 'Japanese Yen (¥)'),
        ('BTC', 'Bitcoin (BTC)'),
        ('ETH', 'Ethereum (ETH)'),
        ('INR', 'Indian Rupee (₹)'), 
    ]
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    invoice_number = models.CharField(max_length=50, unique=True)
    client = models.ForeignKey(Client, on_delete=models.PROTECT)
    user = models.ForeignKey(User, on_delete=models.PROTECT)
    date_issued = models.DateField(default=timezone.now)
    due_date = models.DateField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='draft')
    payment_method = models.CharField(max_length=20, choices=PAYMENT_METHOD_CHOICES, blank=True, null=True)
    currency = models.CharField(max_length=3, choices=CURRENCY_CHOICES, default='INR')
    notes = models.TextField(blank=True)
    terms = models.TextField(blank=True)
    tax = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    discount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    blockchain_hash = models.CharField(max_length=64, blank=True, null=True)
    payment_received = models.BooleanField(default=False)
    payment_date = models.DateField(blank=True, null=True)
    payment_details = models.JSONField(blank=True, null=True)  # Encrypted payment details
    is_archived = models.BooleanField(default=False)
    last_reminder_sent = models.DateTimeField(blank=True, null=True)

    class Meta:
        ordering = ['-date_issued']
        verbose_name = 'Invoice'
        verbose_name_plural = 'Invoices'
        permissions = [
            ('can_generate_reports', 'Can generate invoice reports'),
            ('can_export_invoices', 'Can export invoices'),
            ('can_view_all_invoices', 'Can view all invoices (not just own)'),
        ]

    def __str__(self):
        return f"Invoice #{self.invoice_number}"

    def clean(self):
        if self.due_date < self.date_issued:
            raise ValidationError("Due date cannot be before the issue date.")
        
        if self.status == 'paid' and not self.payment_date:
            raise ValidationError("Payment date is required for paid invoices.")

    def save(self, *args, **kwargs):
        if not self.invoice_number:
            setting = SiteSetting.objects.first()
            invoice_prefix = setting.invoice_prefix if setting and setting.invoice_prefix else "INV"
            unique_part = uuid.uuid4().hex[:6].upper()
            self.invoice_number = f"{invoice_prefix}-{timezone.now().year}-{unique_part}"
        
        # Convert payment_details to dict if it's not None
        if self.payment_details is not None and not isinstance(self.payment_details, (dict, str)):
            try:
                self.payment_details = dict(self.payment_details)
            except (TypeError, ValueError):
                self.payment_details = {'raw_data': str(self.payment_details)}
        
        # Only encrypt if payment_details exists and isn't already encrypted
        if self.payment_details and not (isinstance(self.payment_details, str) and self.payment_details.startswith('gAAAA')):
            self.payment_details = self.encrypt_data(self.payment_details)
        
        super().save(*args, **kwargs)

    def encrypt_data(self, data):
        """Encrypt sensitive data using Fernet symmetric encryption"""
        cipher_suite = Fernet(settings.ENCRYPTION_KEY)
        try:
            if isinstance(data, dict):
                data_str = json.dumps(data, default=str)
            elif hasattr(data, '__dict__'):
                data_str = json.dumps(data.__dict__, default=str)
            else:
                data_str = str(data)
            encrypted_data = cipher_suite.encrypt(data_str.encode())
            return encrypted_data.decode()
        except Exception as e:
            logger.error(f"Encryption failed: {e}")
            return None

    def decrypt_data(self, encrypted_data):
        """Decrypt data that was encrypted with encrypt_data"""
        if not encrypted_data:
            return None
        cipher_suite = Fernet(settings.ENCRYPTION_KEY)
        try:
            decrypted_data = cipher_suite.decrypt(encrypted_data.encode()).decode()
            try:
                return json.loads(decrypted_data)
            except json.JSONDecodeError:
                return decrypted_data
        except Exception as e:
            logger.error(f"Decryption failed: {e}")
            return None

    def add_to_blockchain(self):
        try:
            blockchain = Blockchain()
            index = blockchain.new_transaction(
                invoice_id=str(self.id),
                sender=str(self.client.id),
                recipient=str(self.user.id),
                amount=str(self.total_amount)
            )
            proof = blockchain.proof_of_work(blockchain.last_block['proof'])
            block = blockchain.new_block(proof)
            self.blockchain_hash = blockchain.hash(block)
            self.save(update_fields=['blockchain_hash'])
        except Exception as e:
            logger.error(f"Failed to add invoice {self.id} to blockchain: {e}")
            # Implement fallback or retry logic here

    def to_dict(self, request=None):
        """Convert invoice to a JSON-serializable dictionary"""
        base_url = request.build_absolute_uri('/')[:-1] if request else ''
        
        return {
            'id': str(self.id),
            'invoice_number': self.invoice_number,
            'client': {
                'id': str(self.client.id),
                'name': self.client.name
            },
            'user': str(self.user),
            'date_issued': self.date_issued.isoformat(),
            'due_date': self.due_date.isoformat(),
            'status': self.status,
            'status_display': self.get_status_display(),
            'payment_method': self.payment_method,
            'payment_method_display': self.get_payment_method_display() if self.payment_method else None,
            'currency': self.currency,
            'currency_display': self.get_currency_display(),
            'subtotal': float(self.subtotal),
            'tax_amount': float(self.tax_amount),
            'discount': float(self.discount),
            'total_amount': float(self.total_amount),
            'formatted_total': self.formatted_total,
            'is_overdue': self.is_overdue,
            'days_overdue': self.days_overdue,
            'payment_url': base_url + self.payment_url,
            'verification_url': base_url + self.verification_url,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat(),
            'items': [{
                'description': item.description,
                'quantity': float(item.quantity),
                'unit_price': float(item.unit_price),
                'total': float(item.total),
                'tax': float(item.tax),
                'tax_included': item.tax_included
            } for item in self.items.all()],
            'payments': [{
                'amount': float(payment.amount),
                'payment_date': payment.payment_date.isoformat(),
                'payment_method': payment.payment_method,
                'transaction_id': payment.transaction_id,
                'is_verified': payment.is_verified
            } for payment in self.payments.all()]
        }


    @property
    def subtotal(self):
        return sum(item.total for item in self.items.all())

    @property
    def tax_amount(self):
        return self.subtotal * (self.tax / 100)

    @property
    def total_amount(self):
        return self.subtotal + self.tax_amount - self.discount
    
    @property
    def formatted_total(self):
        return f"{self.currency} {'{:,.2f}'.format(self.total_amount)}"
    
    @property
    def is_overdue(self):
        return self.due_date < timezone.now().date() and self.status not in ('paid', 'cancelled')
    
    @property
    def days_overdue(self):
        if self.is_overdue:
            return (timezone.now().date() - self.due_date).days
        return 0
    
    @property
    def payment_url(self):
        return reverse('invoice_payment', kwargs={'invoice_id': str(self.id)})
    
    @property
    def verification_url(self):
        return reverse('verify_invoice', kwargs={'invoice_id': str(self.id)})
    @property
    def total_paid(self):
        return sum(payment.amount for payment in self.payments.all())

    @property
    def balance_due(self):
        return self.total_amount - self.total_paid

    @property
    def payment_status(self):
        if self.total_paid >= self.total_amount:
            return 'Paid in Full'
        elif self.total_paid > 0:
            return 'Partially Paid'
        return 'Unpaid'
    
    def send_email_notification(self):
        # Implement email sending logic
        pass
    
    def generate_pdf(self):
        # Implement PDF generation logic
        pass
    
    def log_activity(self, action, user, details=None):
        InvoiceActivityLog.objects.create(
            invoice=self,
            user=user,
            action=action,
            details=details or {}
        )

class InvoiceItem(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    invoice = models.ForeignKey(Invoice, related_name='items', on_delete=models.CASCADE)
    description = models.CharField(max_length=200)
    quantity = models.DecimalField(max_digits=10, decimal_places=2, validators=[MinValueValidator(0)])
    unit_price = models.DecimalField(max_digits=10, decimal_places=2, validators=[MinValueValidator(0)])
    tax = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    tax_included = models.BooleanField(default=True)

    class Meta:
        verbose_name = 'Invoice Item'
        verbose_name_plural = 'Invoice Items'

    def __str__(self):
        return f"{self.description} ({self.quantity} x {self.unit_price})"

    @property
    def total(self):
        return self.quantity * self.unit_price

    @property
    def total_with_tax(self):
        if self.tax_included:
            return self.total
        return self.total * (1 + (self.tax / 100))

class InvoicePayment(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    invoice = models.ForeignKey(Invoice, related_name='payments', on_delete=models.CASCADE)
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    payment_date = models.DateField(default=timezone.now)
    payment_method = models.CharField(max_length=20, choices=Invoice.PAYMENT_METHOD_CHOICES)
    transaction_id = models.CharField(max_length=100, blank=True, null=True)
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    created_by = models.ForeignKey(User, on_delete=models.PROTECT)
    is_verified = models.BooleanField(default=False)
    verification_hash = models.CharField(max_length=64, blank=True, null=True)

    class Meta:
        ordering = ['-payment_date']
        verbose_name = 'Invoice Payment'
        verbose_name_plural = 'Invoice Payments'

    def save(self, *args, **kwargs):
        if not self.verification_hash and self.is_verified:
            self.verification_hash = hashlib.sha256(
                f"{self.invoice.id}{self.amount}{self.payment_date}{settings.SECRET_KEY}".encode()
            ).hexdigest()
        super().save(*args, **kwargs)

class InvoiceActivityLog(models.Model):
    ACTION_CHOICES = [
        ('create', 'Created'),
        ('update', 'Updated'),
        ('status_change', 'Status Changed'),
        ('payment', 'Payment Recorded'),
        ('email_sent', 'Email Sent'),
        ('reminder_sent', 'Reminder Sent'),
        ('viewed', 'Viewed by Client'),
        ('download', 'Downloaded'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    invoice = models.ForeignKey(Invoice, related_name='activity_logs', on_delete=models.CASCADE)
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    action = models.CharField(max_length=20, choices=ACTION_CHOICES)
    details = models.JSONField(default=dict)
    ip_address = models.GenericIPAddressField(blank=True, null=True)
    user_agent = models.CharField(max_length=255, blank=True, null=True)
    timestamp = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-timestamp']
        verbose_name = 'Invoice Activity Log'
        verbose_name_plural = 'Invoice Activity Logs'

    def __str__(self):
        return f"{self.get_action_display()} on {self.invoice.invoice_number} at {self.timestamp}"