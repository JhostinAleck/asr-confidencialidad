#!/usr/bin/env python3
"""
Script para probar todos los endpoints del experimento
"""

import requests
import json
from datetime import datetime

def test_endpoints(server_url):
    """Probar todos los endpoints disponibles"""
    
    server_url = server_url.rstrip('/')
    
    endpoints = [
        ('GET', f"{server_url}/api/health/", "Health Check"),
        ('GET', f"{server_url}/api/webhook/", "Webhook GET"),
        ('POST', f"{server_url}/api/webhook/", "Webhook POST"),
        ('GET', f"{server_url}/api/connections/status/", "Connection Status"),
        ('GET', f"{server_url}/api/system/stats/", "System Stats"),
    ]
    
    print("PRUEBA DE ENDPOINTS")
    print("="*50)
    
    for method, url, description in endpoints:
        try:
            if method == 'GET':
                response = requests.get(url, timeout=10)
            elif method == 'POST':
                test_data = {
                    'test': True,
                    'timestamp': datetime.now().isoformat(),
                    'message': 'Test webhook from script'
                }
                response = requests.post(url, json=test_data, timeout=10)
            
            status = "✅ OK" if response.status_code == 200 else f"❌ {response.status_code}"
            print(f"{description}: {status}")
            
            if response.status_code != 200:
                print(f"  Error: {response.text}")
            
        except Exception as e:
            print(f"{description}: ❌ ERROR - {e}")
    
    print("="*50)

if __name__ == "__main__":
    SERVER_URL = "http://35.193.220.139:8080"  # Cambiar por IP de GCP
    test_endpoints(SERVER_URL)