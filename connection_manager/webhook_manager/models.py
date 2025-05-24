from django.db import models
from django.utils import timezone
import uuid

class ActiveConnection(models.Model):
    connection_id = models.UUIDField(default=uuid.uuid4, unique=True)
    client_ip = models.GenericIPAddressField()
    user_agent = models.TextField(blank=True)
    created_at = models.DateTimeField(default=timezone.now)
    last_activity = models.DateTimeField(default=timezone.now)
    is_webhook = models.BooleanField(default=False)
    webhook_endpoint = models.CharField(max_length=200, blank=True)
    status = models.CharField(max_length=20, default='ACTIVE')
    
    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Conexión Activa'
        verbose_name_plural = 'Conexiones Activas'
        
    def __str__(self):
        return f"Connection {self.connection_id} from {self.client_ip}"
        
    @property
    def is_inactive(self):
        """Determina si la conexión está inactiva (más de 30 segundos)"""
        return (timezone.now() - self.last_activity).total_seconds() > 30
        
    @property
    def inactive_time(self):
        """Tiempo en segundos que la conexión ha estado inactiva"""
        return (timezone.now() - self.last_activity).total_seconds()

class ConnectionCleanupLog(models.Model):
    timestamp = models.DateTimeField(default=timezone.now)
    total_connections_before = models.IntegerField()
    inactive_connections_found = models.IntegerField()
    connections_closed = models.IntegerField()
    cleanup_reason = models.TextField()
    connections_closed_list = models.JSONField(default=list)
    
    class Meta:
        ordering = ['-timestamp']
        verbose_name = 'Log de Limpieza'
        verbose_name_plural = 'Logs de Limpieza'
        
    def __str__(self):
        return f"Cleanup {self.timestamp}: {self.connections_closed} connections closed"

class SuspiciousIP(models.Model):
    """Base de datos RAID 1 simulada para IPs que dejan conexiones abiertas"""
    ip_address = models.GenericIPAddressField(unique=True)
    connection_count = models.IntegerField(default=1)
    first_seen = models.DateTimeField(default=timezone.now)
    last_seen = models.DateTimeField(default=timezone.now)
    is_blocked = models.BooleanField(default=False)
    notes = models.TextField(blank=True)
    
    # Simulación RAID 1 - campos de respaldo
    backup_connection_count = models.IntegerField(default=1)
    backup_last_seen = models.DateTimeField(default=timezone.now)
    
    def save(self, *args, **kwargs):
        # Simular RAID 1 - sincronizar datos principales con backup
        self.backup_connection_count = self.connection_count
        self.backup_last_seen = self.last_seen
        super().save(*args, **kwargs)
    
    class Meta:
        ordering = ['-connection_count']
        verbose_name = 'IP Sospechosa'
        verbose_name_plural = 'IPs Sospechosas'
        
    def __str__(self):
        return f"IP {self.ip_address} ({self.connection_count} connections)"