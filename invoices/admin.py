from django.contrib import admin
from .models import Invoice, InvoiceItem, InvoicePayment, InvoiceActivityLog

@admin.register(InvoiceItem)
class InvoiceItemAdmin(admin.ModelAdmin):
    list_display = ('description', 'invoice', 'quantity', 'unit_price', 'tax', 'tax_included')
    search_fields = ('description',)
    list_filter = ('tax_included',)
    raw_id_fields = ('invoice',)

@admin.register(InvoicePayment)
class InvoicePaymentAdmin(admin.ModelAdmin):
    list_display = ('invoice', 'amount', 'payment_method', 'payment_date', 'is_verified')
    list_filter = ('payment_method', 'is_verified')
    search_fields = ('transaction_id',)
    raw_id_fields = ('invoice', 'created_by')

@admin.register(InvoiceActivityLog)
class InvoiceActivityLogAdmin(admin.ModelAdmin):
    list_display = ('invoice', 'action', 'user', 'timestamp', 'ip_address')
    list_filter = ('action', 'timestamp')
    search_fields = ('invoice__invoice_number', 'user__username')
    raw_id_fields = ('invoice', 'user')

@admin.register(Invoice)
class InvoiceAdmin(admin.ModelAdmin):
    list_display = ('invoice_number', 'client', 'user', 'status', 'date_issued', 'due_date', 'total_amount', 'currency', 'is_overdue')
    list_filter = ('status', 'currency', 'payment_method', 'date_issued')
    search_fields = ('invoice_number', 'client__name', 'user__username')
    date_hierarchy = 'date_issued'
    readonly_fields = ('invoice_number', 'blockchain_hash', 'created_at', 'updated_at')
    raw_id_fields = ('client', 'user')
    ordering = ('-date_issued',)

    def total_amount(self, obj):
        return obj.formatted_total
    total_amount.short_description = 'Total'
