from django.urls import path
from . import views

app_name = 'clients'

urlpatterns = [
    path('', views.ClientListView.as_view(), name='client_list'),
    path('<uuid:pk>/', views.ClientDetailView.as_view(), name='client_detail'),
    path('create/', views.ClientCreateView.as_view(), name='client_create'),
    path('<uuid:pk>/update/', views.ClientUpdateView.as_view(), name='client_update'),
    path('<uuid:pk>/delete/', views.ClientDeleteView.as_view(), name='client_delete'),
 
]