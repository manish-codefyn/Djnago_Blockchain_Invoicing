from django.db.models import Count, Sum, Q, F, ExpressionWrapper, DecimalField, IntegerField
from django.db.models.functions import TruncMonth, Coalesce, ExtractMonth, ExtractYear
from django.utils import timezone
from django.http import HttpResponse
from io import BytesIO
import pandas as pd
from datetime import timedelta
from decimal import Decimal

from .models import Invoice, InvoicePayment, Client

from datetime import date
from decimal import Decimal
from django.db.models import Sum, Count, F, Q
from django.db.models.functions import TruncMonth
from django.db.models import Value
from django.db.models.functions import Coalesce
from django.utils import timezone

from .models import Invoice


class InvoiceReports:
    @staticmethod
    def generate_monthly_report(year=None, user=None):
        """
        Generate a report of invoice totals grouped by month
        Returns data in the format: 
        [
            {
                'month': datetime.date(2023, 1, 1),
                'total_invoices': 5,
                'total_amount': Decimal('12500.00'),
                'paid_amount': Decimal('10000.00'),
                'overdue_amount': Decimal('2500.00')
            },
            ...
        ]
        """
        if not year:
            year = timezone.now().year

        queryset = Invoice.objects.filter(
            date_issued__year=year,
            is_archived=False
        )

        if user:
            queryset = queryset.filter(user=user)

        # Get list of months and counts
        monthly_data = queryset.annotate(
            month=TruncMonth('date_issued')
        ).values('month').annotate(
            total_invoices=Count('id'),
            # These totals are estimated based on items' quantity and price (excluding tax/discount)
            total_amount=Sum(F('items__quantity') * F('items__unit_price')),
            paid_amount=Coalesce(
                Sum(F('items__quantity') * F('items__unit_price'), filter=Q(status='paid')),
                Value(Decimal('0.00'))
            ),
            overdue_amount=Coalesce(
                Sum(F('items__quantity') * F('items__unit_price'), filter=Q(status='overdue')),
                Value(Decimal('0.00'))
            ),
        ).order_by('month')

        # Override totals with actual invoice totals (which include tax and discounts)
        for month_data in monthly_data:
            month_invoices = queryset.filter(
                date_issued__month=month_data['month'].month,
                date_issued__year=month_data['month'].year
            )

            total = Decimal('0.00')
            paid = Decimal('0.00')
            overdue = Decimal('0.00')

            for invoice in month_invoices:
                if invoice.status == 'paid':
                    paid += invoice.total_amount
                elif invoice.status == 'overdue':
                    overdue += invoice.total_amount
                total += invoice.total_amount

            month_data['total_amount'] = total
            month_data['paid_amount'] = paid
            month_data['overdue_amount'] = overdue

        return list(monthly_data)


    @staticmethod
    def generate_client_report(user=None):
        """
        Generate a report of invoice totals grouped by client
        Returns data in the format:
        [
            {
                'client_id': UUID('...'),
                'client_name': 'Acme Corp',
                'client_company': 'Acme Inc',
                'total_invoices': 3,
                'total_amount': Decimal('5000.00'),
                'total_paid': Decimal('3000.00'),
                'total_outstanding': Decimal('2000.00')
            },
            ...
        ]
        """
        queryset = Invoice.objects.filter(is_archived=False)

        if user:
            queryset = queryset.filter(user=user)

        # Get all clients with invoices
        clients = Client.objects.filter(
            id__in=queryset.values_list('client_id', flat=True).distinct()
        )

        report_data = []
        
        for client in clients:
            client_invoices = queryset.filter(client=client)
            
            total_invoices = client_invoices.count()
            total_amount = Decimal('0.00')
            total_paid = Decimal('0.00')
            total_outstanding = Decimal('0.00')
            
            for invoice in client_invoices:
                total_amount += invoice.total_amount
                if invoice.status == 'paid':
                    total_paid += invoice.total_amount
                else:
                    total_outstanding += invoice.total_amount
            
            report_data.append({
                'client_id': client.id,
                'client_name': client.name,
                'client_company': client.company,
                'total_invoices': total_invoices,
                'total_amount': total_amount,
                'total_paid': total_paid,
                'total_outstanding': total_outstanding
            })

        # Sort by total amount descending
        report_data.sort(key=lambda x: x['total_amount'], reverse=True)
        
        return report_data

    @staticmethod
    def generate_payment_method_report(start_date=None, end_date=None, user=None):
        """
        Generate a report of payments grouped by payment method.
        Returns data in the format:
        [
            {
                'payment_method': 'bank',
                'payment_method_display': 'Bank Transfer',
                'total_payments': 5,
                'total_amount': Decimal('7500.00')
            },
            ...
        ]
        """
        queryset = InvoicePayment.objects.filter(is_verified=True)

        if start_date:
            queryset = queryset.filter(payment_date__gte=start_date)
        if end_date:
            queryset = queryset.filter(payment_date__lte=end_date)
        if user:
            queryset = queryset.filter(created_by=user)

        # Get all distinct payment methods
        methods = set(queryset.values_list('payment_method', flat=True))

        report_data = []

        for method in methods:
            method_payments = queryset.filter(payment_method=method)
            total_payments = method_payments.count()
            total_amount = method_payments.aggregate(
                total=Sum('amount')
            )['total'] or Decimal('0.00')

            # Get display name from choices
            display = dict(Invoice.PAYMENT_METHOD_CHOICES).get(method, method)

            report_data.append({
                'payment_method': method,
                'payment_method_display': display,
                'total_payments': total_payments,
                'total_amount': total_amount
            })

        # Sort by total amount in descending order
        report_data.sort(key=lambda x: x['total_amount'], reverse=True)

        return report_data

    @staticmethod
    def generate_tax_report(year=None, user=None):
        """
        Generate a tax summary report
        Returns data in the format:
        {
            'total_tax': Decimal('1500.00'),
            'total_sales': Decimal('10000.00'),
            'total_invoices': 25,
            'tax_rate': Decimal('15.00')  # Average tax rate
        }
        """
        if not year:
            year = timezone.now().year

        queryset = Invoice.objects.filter(
            date_issued__year=year,
            is_archived=False,
            status='paid'
        )

        if user:
            queryset = queryset.filter(user=user)

        total_tax = Decimal('0.00')
        total_sales = Decimal('0.00')
        total_invoices = queryset.count()
        
        for invoice in queryset:
            total_tax += invoice.tax_amount
            total_sales += invoice.subtotal
        
        average_tax_rate = (total_tax / total_sales * 100) if total_sales > 0 else Decimal('0.00')
        
        return {
            'total_tax': total_tax,
            'total_sales': total_sales,
            'total_invoices': total_invoices,
            'tax_rate': average_tax_rate.quantize(Decimal('0.01'))
        }

    @staticmethod
    def generate_aging_report(user=None):
        """
        Generate an accounts receivable aging report
        Returns data in the format:
        [
            {
                'client_name': 'Acme Corp',
                'invoice_number': 'INV-2023-001',
                'date_issued': '2023-01-15',
                'due_date': '2023-02-15',
                'days_overdue': 30,
                'amount': Decimal('2500.00'),
                'currency': 'USD',
                'status': 'overdue'
            },
            ...
        ]
        """
        queryset = Invoice.objects.filter(
            status__in=['sent', 'overdue'],
            is_archived=False
        )

        if user:
            queryset = queryset.filter(user=user)

        report_data = []
        today = timezone.now().date()
        
        for invoice in queryset:
            days_overdue = (today - invoice.due_date).days if today > invoice.due_date else 0
            
            report_data.append({
                'client_name': invoice.client.name,
                'invoice_number': invoice.invoice_number,
                'date_issued': invoice.date_issued,
                'due_date': invoice.due_date,
                'days_overdue': days_overdue,
                'amount': invoice.total_amount,
                'currency': invoice.currency,
                'status': invoice.status
            })

        # Sort by days overdue descending
        report_data.sort(key=lambda x: x['days_overdue'], reverse=True)
        
        return report_data

    @staticmethod
    def export_to_excel(report_data, report_name):
        """
        Export report data to Excel format
        """
        # Convert to DataFrame
        if isinstance(report_data, dict):
            df = pd.DataFrame([report_data])
        else:
            df = pd.DataFrame(report_data)
        
        # Format datetime columns
        date_cols = ['month', 'date_issued', 'due_date', 'payment_date']
        for col in date_cols:
            if col in df.columns:
                df[col] = pd.to_datetime(df[col]).dt.strftime('%Y-%m-%d')
        
        # Format decimal columns
        decimal_cols = ['total_amount', 'paid_amount', 'overdue_amount', 
                       'total_paid', 'total_outstanding', 'amount', 
                       'total_tax', 'total_sales', 'tax_rate']
        for col in decimal_cols:
            if col in df.columns:
                df[col] = df[col].apply(lambda x: f"{float(x):,.2f}" if pd.notnull(x) else "0.00")
        
        # Create Excel file in memory
        output = BytesIO()
        with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
            df.to_excel(writer, sheet_name=report_name, index=False)
            
            # Auto-adjust columns' width
            worksheet = writer.sheets[report_name]
            for idx, col in enumerate(df.columns):
                max_len = max(
                    df[col].astype(str).map(len).max(),
                    len(col)
                )
                worksheet.set_column(idx, idx, min(max_len, 30))
        
        output.seek(0)
        response = HttpResponse(
            output.getvalue(),
            content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        )
        response['Content-Disposition'] = f'attachment; filename="{report_name}.xlsx"'
        return response