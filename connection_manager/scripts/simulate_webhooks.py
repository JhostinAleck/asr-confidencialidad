#!/usr/bin/env python3
"""
Script para simular webhooks y probar el experimento de conexiones inactivas
"""

import requests
import threading
import time
import random
import json
from datetime import datetime

class WebhookSimulator:
    def __init__(self, server_url):
        self.server_url = server_url.rstrip('/')
        self.webhook_url = f"{self.server_url}/api/webhook/"
        self.long_webhook_url = f"{self.server_url}/api/webhook/long/"
        self.status_url = f"{self.server_url}/api/connections/status/"
        
    def send_webhook(self, webhook_id, data=None, long_webhook=False):
        """Enviar un webhook individual"""
        
        url = self.long_webhook_url if long_webhook else self.webhook_url
        
        payload = data or {
            'webhook_id': webhook_id,
            'timestamp': datetime.now().isoformat(),
            'data': f'Simulación webhook #{webhook_id}',
            'source': 'webhook_simulator'
        }
        
        try:
            print(f"Enviando webhook #{webhook_id} {'(LONG)' if long_webhook else ''} a {url}")
            
            response = requests.post(
                url,
                json=payload,
                timeout=60 if long_webhook else 10
            )
            
            print(f"Webhook #{webhook_id} - Status: {response.status_code}")
            return response.status_code == 200
            
        except requests.exceptions.Timeout:
            print(f"Webhook #{webhook_id} - TIMEOUT")
            return False
        except Exception as e:
            print(f"Webhook #{webhook_id} - ERROR: {e}")
            return False
    
    def simulate_inactive_connections(self, num_connections=220):
        """Simular múltiples conexiones que se volverán inactivas"""
        
        print(f"Iniciando simulación de {num_connections} webhooks...")
        print("Esto creará conexiones que se volverán inactivas después de 30 segundos")
        
        threads = []
        
        # Crear threads para simular conexiones concurrentes
        for i in range(num_connections):
            # 10% de webhooks serán "long webhooks" que tardan más
            is_long = i % 10 == 0
            
            thread = threading.Thread(
                target=self.send_webhook,
                args=(i + 1, None, is_long)
            )
            
            threads.append(thread)
            thread.start()
            
            # Pequeña pausa para no saturar el servidor
            time.sleep(0.1)
        
        print(f"Todos los webhooks iniciados. Esperando respuestas...")
        
        # Esperar a que terminen todos los webhooks
        for thread in threads:
            thread.join()
        
        print("Todos los webhooks completados.")
        print("Esperando 35 segundos para que las conexiones se vuelvan inactivas...")
        
        # Esperar para que las conexiones se vuelvan inactivas
        for i in range(35):
            print(f"Esperando... {35-i} segundos restantes")
            time.sleep(1)
        
        print("Verificando estado del sistema...")
        self.check_system_status()
    
    def check_system_status(self):
        """Verificar el estado actual del sistema"""
        
        try:
            response = requests.get(self.status_url)
            
            if response.status_code == 200:
                data = response.json()
                
                print("\n" + "="*50)
                print("ESTADO DEL SISTEMA")
                print("="*50)
                print(f"Conexiones activas totales: {data['total_active_connections']}")
                print(f"Conexiones inactivas: {data['inactive_connections']}")
                print(f"Conexiones webhook: {data['webhook_connections']}")
                print(f"Umbral alcanzado: {data['threshold_reached']}")
                print(f"Limpieza necesaria: {data['cleanup_needed']}")
                print("="*50)
                
                if data['cleanup_needed']:
                    print("SISTEMA ACTIVARÁ LIMPIEZA AUTOMÁTICA")
                    print("El 50% de las conexiones inactivas serán cerradas")
                
            else:
                print(f"Error obteniendo estado: {response.status_code}")
                
        except Exception as e:
            print(f"Error verificando estado: {e}")

if __name__ == "__main__":
    # Configurar la URL del servidor
    SERVER_URL = "http://35.193.220.139:8080"  # Cambiar por la IP externa de GCP
    
    print("SIMULADOR DE WEBHOOKS - EXPERIMENTO DJANGO")
    print("="*50)
    
    simulator = WebhookSimulator(SERVER_URL)
    
    # Simular 220 conexiones inactivas
    simulator.simulate_inactive_connections(220)
    
    print("\nExperimento completado.")
    print("Revisar logs del servidor Django para ver la limpieza automática.")