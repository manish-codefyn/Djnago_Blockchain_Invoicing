
from django.db import models
from django.core.validators import EmailValidator, RegexValidator
from django.db.models import Sum, F, ExpressionWrapper, DecimalField
import uuid 
from django.conf import settings
User = settings.AUTH_USER_MODEL

class Client(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=100)
    email = models.EmailField(
        validators=[EmailValidator(message="Enter a valid email address.")]
    )
    phone = models.CharField(
        max_length=20,
        validators=[
            RegexValidator(
                regex=r'^\+?1?\d{9,15}$',
                message="Phone number must be entered in the format: '+9199999999'. Up to 15 digits allowed."
            )
        ]
    )
    address = models.TextField(blank=True, null=True)
    company = models.CharField(max_length=100, blank=True, null=True)
    user = models.ForeignKey(User, related_name='clients', on_delete=models.CASCADE)
    tax_id = models.CharField(max_length=50, blank=True)
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ['name']
        verbose_name = 'Client'
        verbose_name_plural = 'Clients'

    def __str__(self):
        return self.name
    
    @property
    def invoice_count(self):
        return self.invoice_set.count()
    
    @property
    def total_revenue(self):
        from django.db.models import Q

        return self.invoice_set.filter(status='paid').annotate(
            revenue=Sum(
                ExpressionWrapper(
                    F('items__quantity') * F('items__unit_price'),
                    output_field=DecimalField()
                )
            )
        ).aggregate(total=Sum('revenue'))['total'] or 0

    def __str__(self):
        return self.name

    class Meta:
        ordering = ['-created_at']