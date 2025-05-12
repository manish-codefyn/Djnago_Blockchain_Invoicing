from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.contrib.auth import views as auth_views

urlpatterns = [
    path('admin/', admin.site.urls),
    path('invoices/', include('invoices.urls')),
    path('', include('core.urls')),
    # Allauth URLs
    path('accounts/', include('allauth.urls')),
    path('clients/', include('clients.urls')),
    path('api/', include('clients.api.urls')),
    path('notifications/', include('notifications.urls')),
  
]
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)