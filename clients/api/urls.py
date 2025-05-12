from rest_framework.routers import DefaultRouter
from . import views

app_name = 'clients_api'

router = DefaultRouter()
router.register('clients', views.ClientViewSet, basename='client')

urlpatterns = router.urls