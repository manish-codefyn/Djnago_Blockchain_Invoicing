
from django import forms
from .models import SiteSetting, SMTPSetting, SiteLegal

class SiteLegalForm(forms.ModelForm):
    class Meta:
        model = SiteLegal
        fields = ['terms_of_service', 'privacy_policy']
        labels = {
            'terms_of_service': 'Terms of Service',
            'privacy_policy': 'Privacy Policy',
        }
        help_texts = {
            'terms_of_service': 'Enter your terms and conditions',
            'privacy_policy': 'Enter your privacy policy',
        }
        widgets = {
            'terms_of_service': forms.Textarea(attrs={'class': 'form-control', 'rows': 5}),
            'privacy_policy': forms.Textarea(attrs={'class': 'form-control', 'rows': 5}),
        }

class SiteSettingForm(forms.ModelForm):
    class Meta:
        model = SiteSetting
        fields = '__all__'
        widgets = {
            'address': forms.Textarea(attrs={'rows': 3}),
        }


class SMTPSettingForm(forms.ModelForm):
    class Meta:
        model = SMTPSetting
        fields = '__all__'
        widgets = {
            'email_host_password': forms.PasswordInput(render_value=True),
        }