from django.views.generic import CreateView,ListView,DetailView,View
from django.contrib.auth.mixins import LoginRequiredMixin
from django.urls import reverse
from django.contrib import messages
from .models import Invoice, InvoicePayment
from .forms import InvoicePaymentForm
from django.shortcuts import get_object_or_404, redirect
import hashlib
from django.http import HttpResponse
import csv
from django.http import HttpResponse
from io import StringIO

class PaymentCSVExportView(LoginRequiredMixin, View):
    def get(self, request):
        # Get filtered payments
        payments = InvoicePayment.objects.all()
        if not request.user.is_superuser:
            payments = payments.filter(created_by=request.user)
            
        # Apply filters from query parameters
        if 'status' in request.GET:
            payments = payments.filter(is_verified=request.GET['status'] == 'verified')
        if 'date_from' in request.GET:
            payments = payments.filter(payment_date__gte=request.GET['date_from'])
        if 'date_to' in request.GET:
            payments = payments.filter(payment_date__lte=request.GET['date_to'])
            
        payments = payments.select_related('invoice', 'created_by').order_by('-payment_date')

        # Create CSV response
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = 'attachment; filename="payments_export.csv"'
        
        # Create CSV writer
        writer = csv.writer(response)
        
        # Write header row
        writer.writerow([
            'Payment Date',
            'Invoice Number',
            'Client',
            'Amount',
            'Currency',
            'Payment Method',
            'Transaction ID',
            'Status',
            'Verified',
            'Created By',
            'Created At',
            'Verification Hash'
        ])
        
        # Write data rows
        for payment in payments:
            writer.writerow([
                payment.payment_date.strftime('%Y-%m-%d'),
                payment.invoice.invoice_number,
                payment.invoice.client.name,
                str(payment.amount),
                payment.invoice.currency,
                payment.get_payment_method_display(),
                payment.transaction_id or '',
                'Paid',
                'Yes' if payment.is_verified else 'No',
                payment.created_by.get_full_name(),
                payment.created_at.strftime('%Y-%m-%d %H:%M'),
                payment.verification_hash or ''
            ])
        
        return response

class VerifyPaymentView(LoginRequiredMixin, View):
    def get(self, request, pk):
        payment = get_object_or_404(InvoicePayment, pk=pk)
        if not payment.is_verified:
            payment.is_verified = True
            payment.save()
            messages.success(request, 'Payment has been verified successfully.')
        return redirect('invoices:payment-detail', pk=payment.id)
    

class PaymentListView(LoginRequiredMixin, ListView):
    model = InvoicePayment
    template_name = 'payments/payment_list.html'
    context_object_name = 'payments'
    paginate_by = 20

    def get_queryset(self):
        queryset = super().get_queryset()
        if not self.request.user.is_superuser:
            queryset = queryset.filter(created_by=self.request.user)
        return queryset.select_related('invoice', 'created_by').order_by('-payment_date')

class PaymentDetailView(LoginRequiredMixin, DetailView):
    model = InvoicePayment
    template_name = 'payments/payment_detail.html'
    context_object_name = 'payment'

    def get_queryset(self):
        queryset = super().get_queryset()
        if not self.request.user.is_superuser:
            queryset = queryset.filter(created_by=self.request.user)
        return queryset.select_related('invoice', 'created_by')


class InvoicePaymentCreateView(LoginRequiredMixin, CreateView):
    model = InvoicePayment
    form_class = InvoicePaymentForm
    template_name = 'invoices/invoice_payment_form.html'

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['invoice'] = self.get_invoice()
        kwargs['user'] = self.request.user
        return kwargs

    def get_success_url(self):
        return reverse('invoices:invoice-detail', kwargs={'pk': self.object.invoice.id})

    def get_invoice(self):
        return Invoice.objects.get(pk=self.kwargs['pk'])

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['invoice'] = self.get_invoice()
        return context

    def form_valid(self, form):
        response = super().form_valid(form)
        messages.success(self.request, 'Payment added successfully.')
        
        # Update invoice status if fully paid
        invoice = self.object.invoice
        total_paid = sum(p.amount for p in invoice.payments.all())
        if total_paid >= invoice.total_amount:
            invoice.status = 'paid'
            invoice.payment_received = True
            invoice.payment_date = self.object.payment_date
            invoice.save()
        
        return response