from django.apps import AppConfig
from django.conf import settings

class CoreConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'core'

    # def ready(self):
    #     from core.models import SMTPSetting

    #     site_setting = SMTPSetting.objects.first()
    #     if site_setting:
    #         settings.EMAIL_HOST = site_setting.email_host
    #         settings.EMAIL_PORT = site_setting.email_port
    #         settings.EMAIL_USE_TLS = site_setting.email_use_tls
    #         settings.EMAIL_HOST_USER = site_setting.email_host_user
    #         settings.EMAIL_HOST_PASSWORD = site_setting.email_host_password
    #         settings.DEFAULT_FROM_EMAIL = site_setting.default_from_email