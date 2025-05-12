from django.views.generic import TemplateView,View
from django.contrib.auth.mixins import LoginRequiredMixin
from django.utils import timezone
from datetime import timedelta
from django.http import JsonResponse

from .reports import InvoiceReports

class ReportBaseView(LoginRequiredMixin):
    """Base view for reports with common functionality"""
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['current_year'] = timezone.now().year
        context['years'] = range(context['current_year'] - 5, context['current_year'] + 1)
        return context

class DashboardView(ReportBaseView, TemplateView):
    template_name = 'invoices/reports/dashboard.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['monthly_data'] = InvoiceReports.generate_monthly_report(user=self.request.user)
        context['client_data'] = InvoiceReports.generate_client_report(user=self.request.user)
        context['payment_data'] = InvoiceReports.generate_payment_method_report(
            start_date=timezone.now().date() - timedelta(days=30),
            user=self.request.user
        )

        
        return context

class MonthlyReportView(ReportBaseView, TemplateView):
    template_name = 'invoices/reports/monthly.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        year = self.request.GET.get('year', timezone.now().year)
        context['report_data'] = InvoiceReports.generate_monthly_report(
            year=year, 
            user=self.request.user
        )
        context['selected_year'] = int(year)
        return context

class ClientReportView(ReportBaseView, TemplateView):
    template_name = 'invoices/reports/clients.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['report_data'] = InvoiceReports.generate_client_report(
            user=self.request.user
        )

        report_data = InvoiceReports.generate_client_report(user=self.request.user)
    
        # Calculate totals
        total_amount = sum(client['total_amount'] for client in report_data)
        total_paid = sum(client['total_paid'] for client in report_data)
        total_outstanding = sum(client['total_outstanding'] for client in report_data)
        
        context.update({
            'report_data': report_data,
            'total_amount': total_amount,
            'total_paid': total_paid,
            'total_outstanding': total_outstanding,
            'paid_percent': (total_paid / total_amount * 100) if total_amount > 0 else 0
        })
        return context
     

class PaymentMethodReportView(ReportBaseView, TemplateView):
    template_name = 'invoices/reports/payment_methods.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        end_date = timezone.now().date()
        start_date = end_date - timedelta(days=365)
        context['report_data'] = InvoiceReports.generate_payment_method_report(
            start_date=start_date,
            end_date=end_date,
            user=self.request.user
        )
        return context

class TaxReportView(ReportBaseView, TemplateView):
    template_name = 'invoices/reports/taxes.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        year = self.request.GET.get('year', timezone.now().year)
        context['report_data'] = InvoiceReports.generate_tax_report(
            year=year,
            user=self.request.user
        )
        context['selected_year'] = int(year)
        return context

class AgingReportView(ReportBaseView, TemplateView):
    template_name = 'invoices/reports/aging.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['report_data'] = InvoiceReports.generate_aging_report(
            user=self.request.user
        )
        return context

def export_report(request, report_type):
    """Export report data to Excel"""
    report_map = {
        'monthly': (InvoiceReports.generate_monthly_report, 'Monthly_Invoices'),
        'clients': (InvoiceReports.generate_client_report, 'Client_Report'),
        'payment-methods': (InvoiceReports.generate_payment_method_report, 'Payment_Methods'),
        'taxes': (InvoiceReports.generate_tax_report, 'Tax_Report'),
        'aging': (InvoiceReports.generate_aging_report, 'Aging_Report'),
    }
    
    if report_type not in report_map:
        return JsonResponse({'error': 'Invalid report type'}, status=400)
    
    report_func, default_name = report_map[report_type]
    
    # Handle parameters
    params = {'user': request.user}
    if report_type in ['monthly', 'taxes']:
        params['year'] = request.GET.get('year', timezone.now().year)
    elif report_type == 'payment-methods':
        params['start_date'] = request.GET.get('start_date')
        params['end_date'] = request.GET.get('end_date')
    
    data = report_func(**params)
    return InvoiceReports.export_to_excel(data, default_name)


class ExportClientReportView(View):
    def get(self, request, *args, **kwargs):
        # Generate the report data
        report_data = InvoiceReports.generate_client_report(user=request.user)
        
        # Export to Excel
        response = InvoiceReports.export_to_excel(
            report_data=report_data,
            report_name="Client_Report"
        )
        
        # Set filename with current date
        today = timezone.now().strftime("%Y-%m-%d")
        response['Content-Disposition'] = f'attachment; filename="Client_Report_{today}.xlsx"'
        
        return response