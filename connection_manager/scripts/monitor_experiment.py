#!/usr/bin/env python3
"""
Script para monitorear el experimento en tiempo real
"""

import requests
import time
import json
from datetime import datetime

class ExperimentMonitor:
    def __init__(self, server_url):
        self.server_url = server_url.rstrip('/')
        self.status_url = f"{self.server_url}/api/connections/status/"
        self.stats_url = f"{self.server_url}/api/system/stats/"
        self.cleanup_url = f"{self.server_url}/api/connections/cleanup/"
        
    def check_status(self):
        """Verificar estado del sistema"""
        try:
            response = requests.get(self.status_url)
            if response.status_code == 200:
                return response.json()
            else:
                print(f"Error obteniendo estado: {response.status_code}")
                return None
        except Exception as e:
            print(f"Error verificando estado: {e}")
            return None
    
    def get_stats(self):
        """Obtener estadísticas completas"""
        try:
            response = requests.get(self.stats_url)
            if response.status_code == 200:
                return response.json()
            else:
                print(f"Error obteniendo estadísticas: {response.status_code}")
                return None
        except Exception as e:
            print(f"Error obteniendo estadísticas: {e}")
            return None
    
    def manual_cleanup(self):
        """Ejecutar limpieza manual"""
        try:
            response = requests.post(self.cleanup_url)
            if response.status_code == 200:
                return response.json()
            else:
                print(f"Error ejecutando limpieza: {response.status_code}")
                return None
        except Exception as e:
            print(f"Error ejecutando limpieza: {e}")
            return None
    
    def monitor_continuously(self, interval=5):
        """Monitorear continuamente el sistema"""
        print("Iniciando monitoreo continuo del experimento...")
        print("Presiona Ctrl+C para detener")
        
        try:
            while True:
                status = self.check_status()
                if status:
                    timestamp = datetime.now().strftime('%H:%M:%S')
                    print(f"\n[{timestamp}] Estado del Sistema:")
                    print(f"  Conexiones activas: {status['total_active_connections']}")
                    print(f"  Conexiones inactivas: {status['inactive_connections']}")
                    print(f"  Conexiones webhook: {status['webhook_connections']}")
                    print(f"  Umbral alcanzado: {status['threshold_reached']}")
                    
                    if status['cleanup_needed']:
                        print("  ⚠️  LIMPIEZA AUTOMÁTICA ACTIVADA")
                
                time.sleep(interval)
                
        except KeyboardInterrupt:
            print("\nMonitoreo detenido.")

if __name__ == "__main__":
    SERVER_URL = "http://35.193.220.139:8080"  # Cambiar por IP de GCP
    
    monitor = ExperimentMonitor(SERVER_URL)
    
    print("MONITOR DEL EXPERIMENTO DJANGO")
    print("="*40)
    print("1. Verificar estado")
    print("2. Ver estadísticas completas")
    print("3. Ejecutar limpieza manual")
    print("4. Monitoreo continuo")
    print("5. Salir")
    
    while True:
        try:
            option = input("\nSeleccione una opción: ")
            
            if option == "1":
                status = monitor.check_status()
                if status:
                    print(json.dumps(status, indent=2))
            
            elif option == "2":
                stats = monitor.get_stats()
                if stats:
                    print(json.dumps(stats, indent=2))
            
            elif option == "3":
                result = monitor.manual_cleanup()
                if result:
                    print(json.dumps(result, indent=2))
            
            elif option == "4":
                monitor.monitor_continuously()
            
            elif option == "5":
                break
            
            else:
                print("Opción inválida")
                
        except KeyboardInterrupt:
            print("\nSaliendo...")
            break