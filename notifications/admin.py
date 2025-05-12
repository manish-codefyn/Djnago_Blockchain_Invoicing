from django.contrib import admin
from .models import Notification, NotificationTemplate

@admin.register(NotificationTemplate)
class NotificationTemplateAdmin(admin.ModelAdmin):
    list_display = ('name', 'notification_type', 'is_active', 'created_at')
    list_filter = ('notification_type', 'is_active')
    search_fields = ('name', 'subject')


@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = ('recipient', 'template', 'is_read', 'sent_via_email', 'created_at')
    list_filter = ('is_read', 'sent_via_email')
    search_fields = ('recipient__email',)
