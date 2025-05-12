from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView,TemplateView,View
from django.urls import reverse_lazy,reverse
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin
from django.contrib import messages
from django.core.exceptions import PermissionDenied
from django.http import JsonResponse
from django.db import transaction
from django.core.serializers.json import DjangoJSONEncoder
import json
from django.utils import timezone
from .models import Invoice, InvoiceItem, InvoicePayment, InvoiceActivityLog
from .forms import InvoiceForm, InvoiceItemFormSet, InvoicePaymentForm
from notifications.models import Notification
from django.db.models import Count, Sum, Q
import logging
logger = logging.getLogger(__name__)
from rest_framework.renderers import JSONRenderer
from utils.email_utils import send_invoice_email
from core.models import SiteSetting
from django.db.models.functions import TruncMonth
from django.utils import timezone
import calendar
from django.http import HttpResponse
from django.template.loader import get_template
from xhtml2pdf import pisa
from utils.utils import fetch_resources


class DashboardView(LoginRequiredMixin, TemplateView):
    template_name = 'dashboard.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user

        # Invoice metrics
        total_revenue = Invoice.objects.filter(status='paid').aggregate(total=Sum('tax'))['total'] or 0
        
        invoice_counts = Invoice.objects.values('status').annotate(count=Count('id'))
        status_map = {item['status']: item['count'] for item in invoice_counts}
        
        pending_amount = Invoice.objects.filter(status__in=['draft', 'sent']).aggregate(
            total=Sum('tax'))['total'] or 0
        
        overdue_qs = Invoice.objects.filter(status='overdue')
        overdue_count = overdue_qs.count()
        overdue_critical_amount = overdue_qs.aggregate(total=Sum('tax'))['total'] or 0

        critical_overdue_invoices = overdue_qs.filter(
            due_date__lt=timezone.now() - timezone.timedelta(days=7)
        )

        # Recent invoices (latest 10)
        recent_invoices = Invoice.objects.select_related('client').order_by('-created_at')[:10]

        # Monthly invoice volume chart data
        monthly_data = (
            Invoice.objects
            .annotate(month=TruncMonth('created_at'))
            .values('month')
            .annotate(count=Count('id'))
            .order_by('month')
        )

        chart_labels = []
        chart_data = []

        for entry in monthly_data:
            month = entry['month']
            label = month.strftime('%b %Y')  # E.g., "May 2025"
            chart_labels.append(label)
            chart_data.append(entry['count'])

        # Update context
        context.update({
            'total_revenue': total_revenue,
            'invoices_paid': status_map.get('paid', 0),
            'pending_invoices': status_map.get('draft', 0) + status_map.get('sent', 0),
            'pending_amount': pending_amount,
            'overdue_invoices': overdue_count,
            'overdue_critical_amount': overdue_critical_amount,
            'critical_overdue_invoices': critical_overdue_invoices,
            'recent_invoices': recent_invoices,
            'chart_labels': chart_labels,
            'chart_data': chart_data,
        })

        return context

class InvoiceListView(LoginRequiredMixin, ListView):
    model = Invoice
    template_name = 'invoices/list.html'
    context_object_name = 'invoices'
    paginate_by = 20

    def get_queryset(self):
        queryset = super().get_queryset()
        
        # Filter by status if provided
        status = self.request.GET.get('status')
        if status and status in dict(Invoice.STATUS_CHOICES):
            queryset = queryset.filter(status=status)
        
        # Filter by client if provided
        client_id = self.request.GET.get('client')
        if client_id:
            queryset = queryset.filter(client_id=client_id)
        
        # Filter by date range if provided
        date_from = self.request.GET.get('date_from')
        date_to = self.request.GET.get('date_to')
        if date_from:
            queryset = queryset.filter(date_issued__gte=date_from)
        if date_to:
            queryset = queryset.filter(date_issued__lte=date_to)
        
        # Check if user can view all invoices or just their own
        if not self.request.user.has_perm('invoices.can_view_all_invoices'):
            queryset = queryset.filter(user=self.request.user)
        
        return queryset.order_by('-date_issued')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['status_choices'] = Invoice.STATUS_CHOICES
        context['current_status'] = self.request.GET.get('status', '')
        return context


class InvoiceDetailView(LoginRequiredMixin, DetailView):
    model = Invoice
    template_name = 'invoices/detail.html'
    context_object_name = 'invoice'

    def get_queryset(self):
        queryset = super().get_queryset()
        if not self.request.user.has_perm('invoices.can_view_all_invoices'):
            queryset = queryset.filter(user=self.request.user)
        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['items'] = self.object.items.all()
        context['payments'] = self.object.payments.all().order_by('-payment_date')
        context['activity_logs'] = self.object.activity_logs.all().order_by('-timestamp')[:10]
        
        # Add permission checks for template
        context['can_edit'] = self.request.user.has_perm('invoices.change_invoice')
        context['can_delete'] = self.request.user.has_perm('invoices.delete_invoice')
        
        return context

class InvoiceCreateView(LoginRequiredMixin, CreateView):
    model = Invoice
    form_class = InvoiceForm
    template_name = 'invoices/invoice_form.html'
    success_url = reverse_lazy('invoices:invoice-list')

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['user'] = self.request.user
        return kwargs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        if self.request.POST:
            context['items_formset'] = InvoiceItemFormSet(self.request.POST, prefix='items')
        else:
            context['items_formset'] = InvoiceItemFormSet(prefix='items')
        return context

    def form_valid(self, form):
        context = self.get_context_data()
        items_formset = context['items_formset']
        
        with transaction.atomic():
            form.instance.user = self.request.user
            
            # Ensure payment_details is clean before saving
            if 'payment_details' in form.cleaned_data:
                pd = form.cleaned_data['payment_details']
                if pd and not isinstance(pd, (dict, str)):
                    try:
                        form.instance.payment_details = dict(pd)
                    except (TypeError, ValueError):
                        form.instance.payment_details = {'raw': str(pd)}
            
            self.object = form.save()
            
            if items_formset.is_valid():
                items_formset.instance = self.object
                items_formset.save()
            else:
                return self.form_invalid(form)
        
        # Log the creation activity
        self.object.log_activity(
            action='create',
            user=self.request.user,
            details={'fields': form.changed_data}
        )
        
        messages.success(self.request, 'Invoice created successfully.')
        return super().form_valid(form)

    def form_invalid(self, form):
        messages.error(self.request, 'Please correct the errors below.')
        return super().form_invalid(form)

class InvoiceUpdateView(LoginRequiredMixin, UpdateView):
    model = Invoice
    form_class = InvoiceForm
    template_name = 'invoices/invoice_form.html'

    def get_queryset(self):
        queryset = super().get_queryset()
        if not self.request.user.has_perm('invoices.can_view_all_invoices'):
            queryset = queryset.filter(user=self.request.user)
        return queryset

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['user'] = self.request.user
        return kwargs

    def get_success_url(self):
        return reverse_lazy('invoices:invoice-detail', kwargs={'pk': self.object.pk})

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        if self.request.POST:
            context['items_formset'] = InvoiceItemFormSet(
                self.request.POST, 
                instance=self.object, 
                prefix='items'
            )
        else:
            context['items_formset'] = InvoiceItemFormSet(
                instance=self.object, 
                prefix='items'
            )
        return context

    def form_valid(self, form):
        context = self.get_context_data()
        items_formset = context['items_formset']
        
        with transaction.atomic():
            self.object = form.save()
            
            if items_formset.is_valid():
                items_formset.instance = self.object
                items_formset.save()
            else:
                return self.form_invalid(form)
        
        # Log the update activity
        changed_fields = form.changed_data
        if items_formset.has_changed():
            changed_fields.append('items')
            
        self.object.log_activity(
            action='update',
            user=self.request.user,
            details={'fields': changed_fields}
        )
        
        messages.success(self.request, 'Invoice updated successfully.')
        return super().form_valid(form)

    def form_invalid(self, form):
        messages.error(self.request, 'Please correct the errors below.')
        return super().form_invalid(form)

class InvoiceDeleteView(LoginRequiredMixin, PermissionRequiredMixin, DeleteView):
    model = Invoice
    template_name = 'invoices/invoice_confirm_delete.html'
    success_url = reverse_lazy('invoices:invoice-list')
    permission_required = 'invoices.delete_invoice'

    def get_queryset(self):
        queryset = super().get_queryset()
        if not self.request.user.has_perm('invoices.can_view_all_invoices'):
            queryset = queryset.filter(user=self.request.user)
        return queryset

    def delete(self, request, *args, **kwargs):
        invoice = self.get_object()
        
        # Log the deletion activity before actually deleting
        InvoiceActivityLog.objects.create(
            invoice=invoice,
            user=request.user,
            action='delete',
            details={
                'invoice_number': invoice.invoice_number,
                'client': str(invoice.client),
                'total_amount': str(invoice.total_amount)
            }
        )
        
        messages.success(request, f'Invoice #{invoice.invoice_number} has been deleted.')
        return super().delete(request, *args, **kwargs)


# class InvoicePaymentCreateView(LoginRequiredMixin, CreateView):
#     model = InvoicePayment
#     form_class = InvoicePaymentForm
#     template_name = 'invoices/payment_form.html'

#     def dispatch(self, request, *args, **kwargs):
#         self.invoice = get_object_or_404(Invoice, pk=kwargs['invoice_pk'])
#         if not request.user.has_perm('invoices.can_view_all_invoices'):
#             if self.invoice.user != request.user:
#                 raise PermissionDenied
#         return super().dispatch(request, *args, **kwargs)

#     def get_form_kwargs(self):
#         kwargs = super().get_form_kwargs()
#         kwargs['invoice'] = self.invoice
#         return kwargs

#     def get_context_data(self, **kwargs):
#         context = super().get_context_data(**kwargs)
#         context['invoice'] = self.invoice
#         return context

#     def form_valid(self, form):
#         form.instance.invoice = self.invoice
#         form.instance.created_by = self.request.user
        
#         response = super().form_valid(form)
        
#         # Update invoice status if fully paid
#         if self.invoice.total_amount <= self.invoice.payments.aggregate(
#             Sum('amount')
#         )['amount__sum']:
#             self.invoice.status = 'paid'
#             self.invoice.payment_date = timezone.now().date()
#             self.invoice.save()
        
#         # Log the payment activity
#         self.invoice.log_activity(
#             action='payment',
#             user=self.request.user,
#             details={
#                 'amount': str(form.instance.amount),
#                 'payment_method': form.instance.payment_method,
#                 'transaction_id': form.instance.transaction_id
#             }
#         )
        
#         messages.success(self.request, 'Payment recorded successfully.')
#         return response

#     def get_success_url(self):
#         return reverse('invoice-detail', kwargs={'pk': self.invoice.pk})

class InvoiceMarkAsPaidView(LoginRequiredMixin, View):
    def post(self, request, *args, **kwargs):
        invoice = get_object_or_404(Invoice, pk=kwargs['pk'])
        
        if not request.user.has_perm('invoices.can_view_all_invoices'):
            if invoice.user != request.user:
                raise PermissionDenied
        
        if invoice.status != 'paid':
            invoice.status = 'paid'
            invoice.payment_date = timezone.now().date()
            invoice.save()
            
            # Log the status change
            invoice.log_activity(
                action='status_change',
                user=request.user,
                details={
                    'from_status': 'sent',
                    'to_status': 'paid'
                }
            )
            
            messages.success(request, 'Invoice marked as paid.')
        else:
            messages.warning(request, 'Invoice is already marked as paid.')
        
        return redirect('invoice-detail', pk=invoice.pk)

class InvoiceSendView(LoginRequiredMixin, View):
    def post(self, request, *args, **kwargs):
        invoice = get_object_or_404(Invoice, pk=kwargs['pk'])
        
        if not request.user.has_perm('invoices.can_view_all_invoices'):
            if invoice.user != request.user:
                raise PermissionDenied
        
        if invoice.status == 'draft':
            invoice.status = 'sent'
            invoice.save()
            
            # Send email notification
            try:
                invoice.send_email_notification()
            except Exception as e:
                logger.error(f"Failed to send invoice email: {e}")
                messages.warning(request, 'Invoice marked as sent but email notification failed.')
            else:
                messages.success(request, 'Invoice sent successfully.')
            
            # Log the status change
            invoice.log_activity(
                action='status_change',
                user=request.user,
                details={
                    'from_status': 'draft',
                    'to_status': 'sent'
                }
            )
        else:
            messages.warning(request, 'Only draft invoices can be sent.')
        
        return redirect('invoice-detail', pk=invoice.pk)

class InvoiceDownloadPDFView(LoginRequiredMixin, View):
    def get(self, request, *args, **kwargs):
        invoice = get_object_or_404(Invoice, pk=kwargs['pk'])
        
        if not request.user.has_perm('invoices.can_view_all_invoices'):
            if invoice.user != request.user:
                raise PermissionDenied
        
        try:
            pdf_file = invoice.generate_pdf()
            
            # Log the download activity
            invoice.log_activity(
                action='download',
                user=request.user,
                details={'format': 'PDF'}
            )
            
            response = HttpResponse(pdf_file, content_type='application/pdf')
            response['Content-Disposition'] = f'attachment; filename="Invoice_{invoice.invoice_number}.pdf"'
            return response
        except Exception as e:
            logger.error(f"Failed to generate PDF for invoice {invoice.id}: {e}")
            messages.error(request, 'Failed to generate PDF.')
            return redirect('invoice-detail', pk=invoice.pk)

class InvoiceJSONView(LoginRequiredMixin, DetailView):
    model = Invoice
    renderer_classes = [JSONRenderer]
    
    def get_queryset(self):
        queryset = super().get_queryset()
        if not self.request.user.has_perm('invoices.can_view_all_invoices'):
            queryset = queryset.filter(user=self.request.user)
        return queryset
    
    def render_to_response(self, context, **response_kwargs):
        invoice = self.get_object()
        data = invoice.to_dict(self.request)
        return JsonResponse(data, safe=False, **response_kwargs)
    

@login_required
def invoice_pdf(request, pk):
    invoice = get_object_or_404(Invoice, id=pk, user=request.user)
    site = SiteSetting.objects.first()
    
    template = get_template('invoices/pdf_template.html')
    html = template.render({'invoice': invoice, 'site': site})
    
    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="invoice_{invoice.invoice_number}.pdf"'
    
    pisa_status = pisa.CreatePDF(html, dest=response, link_callback=fetch_resources)
    if pisa_status.err:
        return HttpResponse('We had some errors generating the PDF')
    return response


@login_required
def mark_as_paid(request, uuid):
    invoice = get_object_or_404(Invoice, id=uuid, user=request.user)
    if invoice.status != 'paid':
        invoice.status = 'paid'
        invoice.save()
        messages.success(request, 'Invoice marked as paid!')
    return redirect('invoices:invoice-detail', uuid=invoice.id)


class InvoiceSendView(View):
    def get(self, request, pk, *args, **kwargs):
        invoice = get_object_or_404(Invoice, pk=pk)
        if invoice.client.email:
            send_invoice_email(invoice, invoice.client.email)
            messages.success(request, f"Invoice #{invoice.invoice_number} was sent to {invoice.client.email}")
        else:
            messages.error(request, "Client email not found. Cannot send invoice.")
        return redirect('invoices:invoice-detail', pk=invoice.pk)
