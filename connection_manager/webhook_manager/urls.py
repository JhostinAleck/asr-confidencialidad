from django.urls import path
from . import views

urlpatterns = [
    # Endpoints principales del experimento
    path('webhook/', views.webhook_endpoint, name='webhook_endpoint'),
    path('webhook/long/', views.long_webhook, name='long_webhook'),
    
    # Endpoints de monitoreo
    path('connections/status/', views.connection_status, name='connection_status'),
    path('connections/cleanup/', views.manual_cleanup, name='manual_cleanup'),
    path('system/stats/', views.system_stats, name='system_stats'),
    path('health/', views.health_check, name='health_check'),
]