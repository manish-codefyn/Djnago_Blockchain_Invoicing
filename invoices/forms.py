from django import forms
from django.forms import inlineformset_factory
from .models import Invoice, InvoiceItem, InvoicePayment
from django.db.models import Sum

class InvoiceForm(forms.ModelForm):
    def clean_payment_details(self):
        pd = self.cleaned_data.get('payment_details')
        if pd and not isinstance(pd, (dict, str)):
            try:
                return dict(pd)
            except (TypeError, ValueError):
                raise forms.ValidationError("Payment details must be a dictionary or JSON string")
        return pd
    class Meta:
        model = Invoice
        fields = [
            'client', 'date_issued', 'due_date', 'status', 
            'payment_method', 'currency', 'notes', 'terms',
            'tax', 'discount'
        ]
        widgets = {
            'date_issued': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'due_date': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'notes': forms.Textarea(attrs={'rows': 3, 'class': 'form-control'}),
            'terms': forms.Textarea(attrs={'rows': 3, 'class': 'form-control'}),
            'discount': forms.NumberInput(attrs={'class': 'form-control'}),
            'tax': forms.NumberInput(attrs={'class': 'form-control'}),
        }
    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user', None)
        super(InvoiceForm, self).__init__(*args, **kwargs)
        
        # Limit clients to those associated with the user if they lack the permission
        if self.user and not self.user.has_perm('invoices.can_view_all_invoices'):
            self.fields['client'].queryset = self.fields['client'].queryset.filter(
                user=self.user
            )
        
        # Set initial status to 'draft' for new invoices
        if not self.instance.pk:
            self.initial['status'] = 'draft'
        
        # Apply 'form-control' class to all fields for Bootstrap styling
        for field in self.fields.values():
            field.widget.attrs.update({'class': 'form-control'})
    
    def clean(self):
        cleaned_data = super().clean()
        date_issued = cleaned_data.get('date_issued')
        due_date = cleaned_data.get('due_date')
        
        if date_issued and due_date and due_date < date_issued:
            self.add_error('due_date', "Due date cannot be before the issue date.")
        
        return cleaned_data

class InvoiceItemForm(forms.ModelForm):
    class Meta:
        model = InvoiceItem
        fields = ['description', 'quantity', 'unit_price', 'tax', 'tax_included']
        widgets = {
            'description': forms.TextInput(attrs={'placeholder': 'Item description'}),
            'quantity': forms.NumberInput(attrs={'step': '0.01', 'min': '0'}),
            'unit_price': forms.NumberInput(attrs={'step': '0.01', 'min': '0'}),
            'tax': forms.NumberInput(attrs={'step': '0.01', 'min': '0'}),
        }

InvoiceItemFormSet = inlineformset_factory(
    Invoice,
    InvoiceItem,
    form=InvoiceItemForm,
    extra=1,
    can_delete=True,
    can_order=False
)

from django import forms
from .models import InvoicePayment

class InvoicePaymentForm(forms.ModelForm):
    class Meta:
        model = InvoicePayment
        fields = ['amount', 'payment_date', 'payment_method', 'transaction_id', 'notes']
        widgets = {
            'payment_date': forms.DateInput(attrs={'type': 'date'}),
            'notes': forms.Textarea(attrs={'rows': 3}),
        }

    def __init__(self, *args, **kwargs):
        self.invoice = kwargs.pop('invoice', None)
        self.user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        
    def save(self, commit=True):
        instance = super().save(commit=False)
        instance.invoice = self.invoice
        instance.created_by = self.user
        if commit:
            instance.save()
        return instance