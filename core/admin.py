# admin.py

from django.contrib import admin
from .models import SiteSetting, SMTPSetting, SiteLegal

@admin.register(SiteLegal)
class SiteLegalAdmin(admin.ModelAdmin):
    list_display = ('id', 'updated_at')


@admin.register(SMTPSetting)
class SMTPSettingAdmin(admin.ModelAdmin):
    list_display = ('default_from_email', 'email_host', 'email_port', 'email_use_tls', 'updated_at')
    readonly_fields = ('updated_at',)
    fields = (
        'email_host',
        'email_port',
        'email_use_tls',
        'email_host_user',
        'email_host_password',
        'default_from_email',
        'updated_at',
    )


@admin.register(SiteSetting)
class SiteSettingAdmin(admin.ModelAdmin):
    list_display = ('site_name', 'mobile', 'email', 'updated_at')
    search_fields = ('site_name', 'mobile', 'email')
    readonly_fields = ('updated_at',)