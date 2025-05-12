# models.py

import uuid
from django.db import models
from django.conf import settings

User = settings.AUTH_USER_MODEL


class SiteLegal(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    terms_of_service = models.TextField()
    privacy_policy = models.TextField()
    updated_at = models.DateTimeField(auto_now=True)
    updated_by = models.ForeignKey(
        User,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name='legal_updates'
    )

    class Meta:
        verbose_name_plural = "Site Legal Content"  # Removes 's' from admin
    
    def save(self, *args, **kwargs):
        """Ensure only one instance exists"""
        if not self.pk and SiteLegal.objects.exists():
            # Prevent creation if one already exists
            raise ValueError("Only one SiteLegal instance can be created")
        super().save(*args, **kwargs)



    def __str__(self):
        return "Site Legal Content"

class SiteSetting(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    
    # General Site Data
    site_name = models.CharField(max_length=255, default='My Site')
    tagline = models.CharField(max_length=255, blank=True, null=True, help_text="Short slogan or tagline.")
    description = models.TextField(blank=True, null=True, help_text="About your site, used in footers and SEO.")
    
    logo = models.ImageField(upload_to='site/logo/', null=True, blank=True)
    stamp = models.ImageField(upload_to='site/stamp/', null=True, blank=True)
    favicon = models.ImageField(upload_to='site/favicon/', null=True, blank=True)

    # Contact Info
    mobile = models.CharField(max_length=20, blank=True, null=True)
    email = models.EmailField(blank=True, null=True)
    address = models.TextField(blank=True, null=True)

    # Business Info for Invoicing
    gst_number = models.CharField(max_length=50, blank=True, null=True)
    registration_number = models.CharField(max_length=100, blank=True, null=True, help_text="Company registration number")
    invoice_prefix = models.CharField(max_length=20, default="INV", help_text="Prefix for invoice numbers")
    default_currency = models.CharField(max_length=10, default="INR", help_text="Currency code, e.g., INR, USD")
    bank_details = models.TextField(blank=True, null=True, help_text="Bank or UPI info for manual payments")
    invoice_footer_note = models.TextField(blank=True, null=True, help_text="Default note shown in invoice footers")

    # Social Links (Optional)
    facebook = models.URLField(blank=True, null=True)
    instagram = models.URLField(blank=True, null=True)
    linkedin = models.URLField(blank=True, null=True)
    twitter = models.URLField(blank=True, null=True)
    youtube = models.URLField(blank=True, null=True)

    # SEO Basics
    meta_title = models.CharField(max_length=255, blank=True, null=True)
    meta_description = models.TextField(blank=True, null=True)
    meta_keywords = models.TextField(blank=True, null=True)

    updated_at = models.DateTimeField(auto_now=True)



    class Meta:
        verbose_name = 'Site Setting'
        verbose_name_plural = 'Site Settings'

    def __str__(self):
        return self.site_name


class SMTPSetting(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    email_host = models.CharField(max_length=255, default='smtp.gmail.com')
    email_port = models.IntegerField(default=587)
    email_use_tls = models.BooleanField(default=True)
    email_host_user = models.EmailField(blank=True, null=True)
    email_host_password = models.CharField(max_length=255, blank=True, null=True)
    default_from_email = models.EmailField(default='noreply@example.com')

    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "SMTP Setting"
        verbose_name_plural = "SMTP Settings"

    def __str__(self):
        return f"SMTP Settings ({self.default_from_email})"