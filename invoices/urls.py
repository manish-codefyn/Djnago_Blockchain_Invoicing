from django.urls import path
from . import views, views_api
from . import reports_views
from . import payments
from django.views.generic import TemplateView

app_name = "invoices"

urlpatterns = [
    # Web Views

    path('dashboard/', views.DashboardView.as_view(), name='dashboard'),
    path('', views.InvoiceListView.as_view(), name='invoice-list'),
    path('create/', views.InvoiceCreateView.as_view(), name='invoice-create'),
    path('<uuid:pk>/', views.InvoiceDetailView.as_view(), name='invoice-detail'),
    path('<uuid:pk>/update/', views.InvoiceUpdateView.as_view(), name='invoice-update'),
    path('<uuid:pk>/delete/', views.InvoiceDeleteView.as_view(), name='invoice-delete'),
    path('<uuid:pk>/mark-paid/', views.InvoiceMarkAsPaidView.as_view(), name='invoice-mark-paid'),
    path('<uuid:pk>/send/', views.InvoiceSendView.as_view(), name='invoice-send'),
    path('<uuid:pk>/download/', views.InvoiceDownloadPDFView.as_view(), name='invoice-download'),
    path('<uuid:pk>/json/', views.InvoiceJSONView.as_view(), name='invoice-json'),
    # path('<uuid:invoice_pk>/payments/create/', views.InvoicePaymentCreateView.as_view(), name='payment-create'),
    path('invoices/<uuid:pk>/payments/add/', payments.InvoicePaymentCreateView.as_view(), name='invoice-payment-create'),
    path('payments/', payments.PaymentListView.as_view(), name='payment-list'),
    path('payments/<uuid:pk>/', payments.PaymentDetailView.as_view(), name='payment-detail'),
    path('payments/<uuid:pk>/verify/', payments.VerifyPaymentView.as_view(), name='verify-payment'),
    path('payments/export/csv/', payments.PaymentCSVExportView.as_view(), name='payment-export-csv'),

    path('<uuid:pk>/pdf/', views.invoice_pdf, name='invoice-pdf'),
    path('<uuid:pk>/paid/', views.mark_as_paid, name='invoice-mark-paid'),
    path('<uuid:pk>/send/', views.InvoiceSendView.as_view(), name='invoice-send'),
    # API Endpoints
    path('api/invoices/', views_api.InvoiceListCreateAPIView.as_view(), name='api-invoice-list'),
    path('api/invoices/<uuid:id>/', views_api.InvoiceRetrieveUpdateDestroyAPIView.as_view(), name='api-invoice-detail'),
    path('api/clients/', views_api.ClientListCreateAPIView.as_view(), name='api-client-list'),
    path('api/clients/<uuid:id>/', views_api.ClientRetrieveUpdateDestroyAPIView.as_view(), name='api-client-detail'),
    path('api/blockchain/', views_api.BlockchainView.as_view(), name='api-blockchain'),

    # reports

    path('reports/', reports_views.DashboardView.as_view(), name='reports'),
    path('reports/monthly/', reports_views.MonthlyReportView.as_view(), name='reports_monthly'),
    path('reports/clients/', reports_views.ClientReportView.as_view(), name='reports_clients'),
    path('reports/payment-methods/', reports_views.PaymentMethodReportView.as_view(), name='reports_payment_methods'),
    path('reports/taxes/', reports_views.TaxReportView.as_view(), name='reports_taxes'),
    path('reports/aging/', reports_views.AgingReportView.as_view(), name='reports_aging'),
    path('reports/export/<str:report_type>/', reports_views.export_report, name='export_report'),
        path(
        'reports/clients/export/',
        reports_views.ExportClientReportView.as_view(),
        name='export_client_report'
    ),
]

