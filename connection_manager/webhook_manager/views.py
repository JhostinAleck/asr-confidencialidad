from django.shortcuts import render
from django.http import JsonResponse, HttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.utils import timezone
from django.conf import settings
from rest_framework.decorators import api_view
from rest_framework.response import Response
from .models import ActiveConnection, ConnectionCleanupLog, SuspiciousIP
from .services import ConnectionCleanupService
import json
import logging
import threading
import time

logger = logging.getLogger('webhook_manager')

@csrf_exempt
@require_http_methods(["GET", "POST"])
def webhook_endpoint(request):
    """Endpoint principal para recibir webhooks"""
    
    # Simular procesamiento de webhook
    if request.method == 'POST':
        try:
            data = json.loads(request.body) if request.body else {}
            
            logger.info(f"Webhook recibido de {request.META.get('REMOTE_ADDR')}: {data}")
            
            # Simular tiempo de procesamiento para mantener la conexión activa
            time.sleep(2)
            
            response_data = {
                'status': 'success',
                'message': 'Webhook procesado correctamente',
                'timestamp': timezone.now().isoformat(),
                'connection_id': str(request.connection_id) if hasattr(request, 'connection_id') else None,
                'data_received': data
            }
            
            return JsonResponse(response_data, status=200)
            
        except Exception as e:
            logger.error(f"Error procesando webhook: {e}")
            return JsonResponse({
                'status': 'error',
                'message': str(e)
            }, status=500)
    
    else:  # GET request
        return JsonResponse({
            'status': 'active',
            'message': 'Webhook endpoint activo',
            'timestamp': timezone.now().isoformat()
        })

@api_view(['GET'])
def connection_status(request):
    """Endpoint para verificar el estado de las conexiones"""
    
    total_connections = ActiveConnection.objects.filter(status='ACTIVE').count()
    inactive_connections = [
        conn for conn in ActiveConnection.objects.filter(status='ACTIVE') 
        if conn.is_inactive
    ]
    
    webhook_connections = ActiveConnection.objects.filter(
        status='ACTIVE', 
        is_webhook=True
    ).count()
    
    response_data = {
        'total_active_connections': total_connections,
        'inactive_connections': len(inactive_connections),
        'webhook_connections': webhook_connections,
        'threshold_reached': len(inactive_connections) > settings.MAX_CONNECTIONS,
        'cleanup_needed': len(inactive_connections) > settings.MAX_CONNECTIONS,
        'timestamp': timezone.now().isoformat()
    }
    
    # Si se alcanza el umbral, disparar limpieza automática
    if len(inactive_connections) > settings.MAX_CONNECTIONS:
        logger.warning(f"Umbral alcanzado: {len(inactive_connections)} conexiones inactivas")
        cleanup_service = ConnectionCleanupService()
        threading.Thread(target=cleanup_service.cleanup_connections).start()
    
    return Response(response_data)

@api_view(['POST'])
def manual_cleanup(request):
    """Endpoint para disparar limpieza manual de conexiones"""
    
    cleanup_service = ConnectionCleanupService()
    result = cleanup_service.cleanup_connections()
    
    return Response({
        'status': 'success',
        'message': 'Limpieza ejecutada',
        'result': result,
        'timestamp': timezone.now().isoformat()
    })

@api_view(['GET'])
def system_stats(request):
    """Endpoint para estadísticas del sistema"""
    
    total_connections = ActiveConnection.objects.filter(status='ACTIVE').count()
    inactive_connections = [
        conn for conn in ActiveConnection.objects.filter(status='ACTIVE') 
        if conn.is_inactive
    ]
    
    recent_cleanups = ConnectionCleanupLog.objects.all()[:5]
    suspicious_ips = SuspiciousIP.objects.filter(connection_count__gte=5)
    
    stats = {
        'connections': {
            'total_active': total_connections,
            'inactive_count': len(inactive_connections),
            'webhook_connections': ActiveConnection.objects.filter(is_webhook=True, status='ACTIVE').count(),
            'max_allowed': settings.MAX_CONNECTIONS,
            'cleanup_threshold_reached': len(inactive_connections) > settings.MAX_CONNECTIONS
        },
        'cleanup_history': [
            {
                'timestamp': cleanup.timestamp.isoformat(),
                'connections_closed': cleanup.connections_closed,
                'reason': cleanup.cleanup_reason
            } for cleanup in recent_cleanups
        ],
        'suspicious_ips': [
            {
                'ip': ip.ip_address,
                'connection_count': ip.connection_count,
                'backup_count': ip.backup_connection_count,  # RAID 1 backup
                'is_blocked': ip.is_blocked
            } for ip in suspicious_ips
        ],
        'raid1_status': {
            'enabled': True,
            'backup_synchronized': all(
                ip.connection_count == ip.backup_connection_count 
                for ip in suspicious_ips
            )
        }
    }
    
    return Response(stats)

@csrf_exempt
def long_webhook(request):
    """Webhook que simula una conexión que permanece abierta por mucho tiempo"""
    
    if request.method == 'POST':
        logger.info(f"Long webhook iniciado desde {request.META.get('REMOTE_ADDR')}")
        
        # Simular procesamiento largo (más de 30 segundos para que sea marcado como inactivo)
        time.sleep(45)
        
        return JsonResponse({
            'status': 'completed',
            'message': 'Procesamiento largo completado',
            'duration': '45 segundos',
            'timestamp': timezone.now().isoformat()
        })
    
    return JsonResponse({'message': 'Long webhook endpoint activo'})

def health_check(request):
    """Health check del sistema"""
    
    return JsonResponse({
        'status': 'healthy',
        'service': 'Django Connection Manager',
        'timestamp': timezone.now().isoformat(),
        'version': '1.0.0'
    })