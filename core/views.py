

from django.shortcuts import render,redirect
from django.urls import reverse_lazy
from django.views.generic import TemplateView,UpdateView,CreateView,View,DetailView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import Count
from .models import SiteSetting, SMTPSetting,SiteLegal
from .forms import SiteSettingForm, SMTPSettingForm,SiteLegalForm
import smtplib
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
import json
from django.contrib import messages

from django.contrib.admin.views.decorators import staff_member_required

@staff_member_required
def settings_dashboard(request):
    return render(request, 'core/setting_page.html')


class SiteLegalUpdateView(LoginRequiredMixin,UpdateView):
    form_class = SiteLegalForm
    template_name = 'core/sitelegal_form.html'
    success_url = reverse_lazy('core:site_legal_detail')


    def get_object(self):
        return SiteLegal.objects.first() or SiteLegal.objects.create()
    
    def form_valid(self, form):
        form.instance.updated_by = self.request.user
        messages.success(self.request, "Legal content updated successfully!")
        return super().form_valid(form)


class SiteLegalDetailView(DetailView):
    model = SiteLegal
    template_name = 'core/sitelegal_detail.html'
    context_object_name = 'legal_content'

    def get_object(self, queryset=None):
        """Get the single SiteLegal instance or redirect to create view"""
        obj = SiteLegal.objects.first()
        if not obj:
            # Redirect to a create view if no SiteLegal object exists
            return redirect(reverse_lazy('core:site_legal_create'))  # Add the create URL
        return obj
    

class SiteLegalCreateView(LoginRequiredMixin, CreateView):
    model = SiteLegal
    form_class = SiteLegalForm
    template_name = 'core/sitelegal_form.html'
    success_url = reverse_lazy('core:site_legal_detail')  # Change to your detail view name

    def test_func(self):
        """Only allow staff users to create legal content"""
        return self.request.user.is_staff

    def form_valid(self, form):
        """Handle successful form submission"""
        response = super().form_valid(form)
        messages.success(
            self.request,
            'Legal content created successfully!',
            extra_tags='alert-success'
        )
        return response

    def form_invalid(self, form):
        """Handle invalid form submission"""
        messages.error(
            self.request,
            'Please correct the errors below.',
            extra_tags='alert-danger'
        )
        return super().form_invalid(form)


class PrivacyPolicyView(TemplateView):
    template_name = 'core/privacy_policy.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        legal = SiteLegal.objects.first()
        context['privacy_policy'] = legal.privacy_policy if legal else ''
        return context

class TermsOfServiceView(TemplateView):
    template_name = 'core/terms_of_service.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        legal = SiteLegal.objects.first()
        context['terms_of_service'] = legal.terms_of_service if legal else ''
        return context

@csrf_exempt
def test_smtp_connection(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            
            # Get SMTP settings from request
            email_host = data.get('email_host')
            email_port = int(data.get('email_port', 587))
            email_use_tls = data.get('email_use_tls', True)
            email_host_user = data.get('email_host_user')
            email_host_password = data.get('email_host_password')
            
            # Test connection
            server = smtplib.SMTP(email_host, email_port, timeout=10)
            if email_use_tls:
                server.starttls()
            server.login(email_host_user, email_host_password)
            server.quit()
            
            return JsonResponse({
                'success': True,
                'message': 'SMTP connection successful!'
            })
        except smtplib.SMTPAuthenticationError as e:
            return JsonResponse({
                'success': False,
                'message': f'Authentication failed: {str(e)}'
            })
        except smtplib.SMTPException as e:
            return JsonResponse({
                'success': False,
                'message': f'SMTP error: {str(e)}'
            })
        except Exception as e:
            return JsonResponse({
                'success': False,
                'message': f'Connection error: {str(e)}'
            })
    return JsonResponse({
        'success': False,
        'message': 'Invalid request method'
    })


class SiteSettingUpdateView(LoginRequiredMixin, UpdateView):
    model = SiteSetting
    form_class = SiteSettingForm
    template_name = 'core/site_setting_form.html'
    success_url = reverse_lazy('core:site_settings')
    
    def get_object(self):
        return SiteSetting.objects.first() or SiteSetting.objects.create()


class SMTPSettingUpdateView(LoginRequiredMixin, UpdateView):
    model = SMTPSetting
    form_class = SMTPSettingForm
    template_name = 'core/smtp_setting_form.html'
    success_url = reverse_lazy('core:smtp_settings')
    
    def get_object(self):
        return SMTPSetting.objects.first() or SMTPSetting.objects.create()


class HomeView(TemplateView):
    template_name = 'core/home.html'
   


class DashboardView(LoginRequiredMixin, HomeView):
    template_name = 'core/dashboard.html'
    
 

def handler404(request, exception):
    return render(request, '404.html', status=404)

def handler500(request):
    return render(request, '500.html', status=500)