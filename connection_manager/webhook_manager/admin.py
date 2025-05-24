from django.contrib import admin
from .models import ActiveConnection, ConnectionCleanupLog, SuspiciousIP

@admin.register(ActiveConnection)
class ActiveConnectionAdmin(admin.ModelAdmin):
    list_display = ['connection_id', 'client_ip', 'is_webhook', 'status', 'created_at', 'last_activity']
    list_filter = ['status', 'is_webhook', 'created_at']
    search_fields = ['client_ip', 'connection_id']
    readonly_fields = ['connection_id', 'created_at']

@admin.register(ConnectionCleanupLog)
class ConnectionCleanupLogAdmin(admin.ModelAdmin):
    list_display = ['timestamp', 'total_connections_before', 'inactive_connections_found', 'connections_closed']
    list_filter = ['timestamp']
    readonly_fields = ['timestamp']

@admin.register(SuspiciousIP)
class SuspiciousIPAdmin(admin.ModelAdmin):
    list_display = ['ip_address', 'connection_count', 'backup_connection_count', 'is_blocked', 'last_seen']
    list_filter = ['is_blocked', 'last_seen']
    search_fields = ['ip_address']