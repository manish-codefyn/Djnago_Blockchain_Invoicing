from django.urls import path
from notifications import views

app_name = 'notifications'

urlpatterns = [
    # Notification list views
    path('', views.NotificationListView.as_view(), name='all'),
    path('unread/', views.UnreadNotificationListView.as_view(), name='unread'),
    
    # Notification actions
    path('<uuid:pk>/mark-as-read/', views.mark_as_read, name='mark_as_read'),
    path('mark-all-read/', views.mark_all_as_read, name='mark_all_read'),
    
    # AJAX endpoints
    path('count/', views.get_notification_count, name='count'),
    path('latest/', views.get_latest_notifications, name='latest'),
]