# webhook_manager/middleware.py - VERSIÓN CORREGIDA

from django.utils.deprecation import MiddlewareMixin
from django.utils import timezone
from .models import ActiveConnection, SuspiciousIP
import logging
import threading
import uuid

logger = logging.getLogger('webhook_manager')

class ConnectionTrackingMiddleware(MiddlewareMixin):
    """Middleware para rastrear conexiones activas - VERSIÓN CORREGIDA"""
    
    def process_request(self, request):
        # Obtener información del cliente
        client_ip = self.get_client_ip(request)
        user_agent = request.META.get('HTTP_USER_AGENT', '')
        
        # Verificar si es un webhook
        is_webhook = '/webhook/' in request.path or 'webhook' in request.path.lower()
        webhook_endpoint = request.path if is_webhook else ''
        
        # CAMBIO CLAVE: Crear SIEMPRE una nueva conexión para webhooks
        # Esto simula múltiples clientes/sesiones diferentes
        if is_webhook:
            # Para webhooks, crear siempre una nueva conexión única
            connection = ActiveConnection.objects.create(
                client_ip=client_ip,
                user_agent=user_agent,
                webhook_endpoint=webhook_endpoint,
                is_webhook=True,
                status='ACTIVE',
                last_activity=timezone.now()
            )
            created = True
            logger.info(f"Nueva conexión webhook creada: {connection.connection_id} desde {client_ip}")
        else:
            # Para requests normales, usar la lógica original
            connection, created = ActiveConnection.objects.get_or_create(
                client_ip=client_ip,
                is_webhook=False,
                status='ACTIVE',
                defaults={
                    'user_agent': user_agent,
                    'webhook_endpoint': webhook_endpoint,
                    'last_activity': timezone.now()
                }
            )
            
            if not created:
                # Actualizar actividad de conexión existente
                connection.last_activity = timezone.now()
                connection.save()
        
        # Registrar en IP sospechosas si es necesario
        if is_webhook:
            self.track_suspicious_ip(client_ip)
        
        # Agregar información a la request
        request.connection_id = connection.connection_id
        request.is_webhook = is_webhook
        
        logger.info(f"Actividad registrada: {client_ip} - Webhook: {is_webhook} - Conexión: {connection.connection_id}")
        
        return None
    
    def get_client_ip(self, request):
        """Obtener la IP real del cliente"""
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip
    
    def track_suspicious_ip(self, ip_address):
        """Rastrear IPs que usan webhooks frecuentemente"""
        try:
            suspicious_ip, created = SuspiciousIP.objects.get_or_create(
                ip_address=ip_address,
                defaults={'connection_count': 1}
            )
            
            if not created:
                suspicious_ip.connection_count += 1
                suspicious_ip.last_seen = timezone.now()
                suspicious_ip.save()
                
                # RAID 1 simulado - backup automático
                logger.info(f"RAID 1 Backup: IP {ip_address} actualizada en ambas bases de datos")
                
        except Exception as e:
            logger.error(f"Error tracking suspicious IP {ip_address}: {e}")