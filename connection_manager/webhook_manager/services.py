from django.utils import timezone
from django.conf import settings
from .models import ActiveConnection, ConnectionCleanupLog, SuspiciousIP
import logging
import random

logger = logging.getLogger('webhook_manager')

class ConnectionCleanupService:
    """Servicio para limpiar conexiones inactivas"""
    
    def __init__(self):
        self.timeout = getattr(settings, 'CONNECTION_TIMEOUT', 30)
        self.max_connections = getattr(settings, 'MAX_CONNECTIONS', 200)
        self.cleanup_percentage = getattr(settings, 'CLEANUP_PERCENTAGE', 0.5)
    
    def cleanup_connections(self):
        """Ejecutar limpieza de conexiones inactivas"""
        
        logger.info("Iniciando limpieza de conexiones inactivas...")
        
        # Obtener todas las conexiones activas
        active_connections = list(ActiveConnection.objects.filter(status='ACTIVE'))
        total_before = len(active_connections)
        
        # Filtrar conexiones inactivas
        inactive_connections = [
            conn for conn in active_connections 
            if conn.is_inactive
        ]
        
        inactive_count = len(inactive_connections)
        
        logger.info(f"Encontradas {inactive_count} conexiones inactivas de {total_before} totales")
        
        # Verificar si se debe ejecutar limpieza
        if inactive_count <= self.max_connections:
            logger.info(f"No se requiere limpieza: {inactive_count} <= {self.max_connections}")
            return {
                'executed': False,
                'reason': 'Umbral no alcanzado',
                'inactive_connections': inactive_count,
                'threshold': self.max_connections
            }
        
        # Calcular cuántas conexiones cerrar (50%)
        connections_to_close = int(inactive_count * self.cleanup_percentage)
        
        logger.warning(f"LIMPIEZA ACTIVADA: Cerrando {connections_to_close} de {inactive_count} conexiones inactivas")
        
        # Seleccionar conexiones a cerrar (las más antiguas)
        connections_to_close_list = sorted(
            inactive_connections, 
            key=lambda x: x.last_activity
        )[:connections_to_close]
        
        # Cerrar conexiones seleccionadas
        closed_connections = []
        for connection in connections_to_close_list:
            try:
                # Registrar IP sospechosa si es webhook
                if connection.is_webhook:
                    self.register_suspicious_ip(connection.client_ip)
                
                # Marcar conexión como cerrada
                connection.status = 'CLOSED'
                connection.save()
                
                closed_connections.append({
                    'connection_id': str(connection.connection_id),
                    'client_ip': connection.client_ip,
                    'inactive_time': connection.inactive_time,
                    'is_webhook': connection.is_webhook
                })
                
                logger.info(f"Conexión cerrada: {connection.connection_id} de {connection.client_ip}")
                
            except Exception as e:
                logger.error(f"Error cerrando conexión {connection.connection_id}: {e}")
        
        # Registrar en log de limpieza
        cleanup_log = ConnectionCleanupLog.objects.create(
            total_connections_before=total_before,
            inactive_connections_found=inactive_count,
            connections_closed=len(closed_connections),
            cleanup_reason=f"Umbral de {self.max_connections} conexiones inactivas excedido",
            connections_closed_list=closed_connections
        )
        
        # Generar alerta de seguridad
        self.generate_security_alert(cleanup_log, closed_connections)
        
        result = {
            'executed': True,
            'total_connections_before': total_before,
            'inactive_connections_found': inactive_count,
            'connections_closed': len(closed_connections),
            'cleanup_percentage': self.cleanup_percentage * 100,
            'closed_connections': closed_connections,
            'cleanup_log_id': cleanup_log.id
        }
        
        logger.info(f"Limpieza completada: {len(closed_connections)} conexiones cerradas")
        
        return result
    
    def register_suspicious_ip(self, ip_address):
        """Registrar IP que deja conexiones webhook abiertas"""
        
        try:
            suspicious_ip, created = SuspiciousIP.objects.get_or_create(
                ip_address=ip_address
            )
            
            if not created:
                suspicious_ip.connection_count += 1
                suspicious_ip.last_seen = timezone.now()
                suspicious_ip.save()
            
            logger.info(f"IP sospechosa registrada en RAID 1: {ip_address} ({suspicious_ip.connection_count} conexiones)")
            
        except Exception as e:
            logger.error(f"Error registrando IP sospechosa {ip_address}: {e}")
    
    def generate_security_alert(self, cleanup_log, closed_connections):
        """Generar alerta de seguridad cuando se ejecuta limpieza"""
        
        separator = "=" * 60
        
        alert_message = f"""
{separator}
ALERTA DE SEGURIDAD - SISTEMA DATA MANAGER DJANGO
{separator}
Timestamp: {cleanup_log.timestamp.strftime('%Y-%m-%d %H:%M:%S')}
Evento: Limpieza automática de conexiones inactivas
Conexiones totales antes: {cleanup_log.total_connections_before}
Conexiones inactivas encontradas: {cleanup_log.inactive_connections_found}
Conexiones cerradas: {cleanup_log.connections_closed}
Porcentaje de limpieza: {self.cleanup_percentage * 100}%
Umbral configurado: {self.max_connections} conexiones

ASR DE INTEGRIDAD CUMPLIDO:
- Sistema detectó sobrecarga de conexiones inactivas
- Limpieza automática ejecutada (50% de conexiones inactivas)
- Rendimiento del sistema protegido
- Registro RAID 1 de IPs sospechosas actualizado

IPs de conexiones cerradas:
"""
        
        for conn in closed_connections[:10]:  # Mostrar solo las primeras 10
            alert_message += f"• {conn['client_ip']} - Inactiva por {conn['inactive_time']:.1f}s - Webhook: {conn['is_webhook']}\n"
        
        if len(closed_connections) > 10:
            alert_message += f"... y {len(closed_connections) - 10} más\n"
        
        alert_message += f"\n{separator}\n"
        
        # Imprimir en consola y logs
        print(alert_message)
        logger.warning(alert_message)