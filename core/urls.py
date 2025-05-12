from django.urls import path
from .import views 


app_name = "core"

urlpatterns = [
    path('settings/', views.settings_dashboard, name='settings'),
    path('', views.HomeView.as_view(), name='home'),
    path('dashboard/', views.DashboardView.as_view(), name='dashboard'),
    path('settings/site/', views.SiteSettingUpdateView.as_view(), name='site_settings'),
    path('settings/smtp/', views.SMTPSettingUpdateView.as_view(), name='smtp_settings'),
    path('test-smtp/', views.test_smtp_connection, name='test_smtp_connection'),
    path('privacy-policy/', views.PrivacyPolicyView.as_view(), name='privacy_policy'),
    path('terms-of-service/', views.TermsOfServiceView.as_view(), name='terms_of_service'),
    path('legal/create/', views.SiteLegalCreateView.as_view(), name='site_legal_create'),
    path('site/legal/', views.SiteLegalDetailView.as_view(), name='site_legal_detail'),
    path('legal/edit/', views.SiteLegalUpdateView.as_view(), name='site_legal_update'),
]   