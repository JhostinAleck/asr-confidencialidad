from django.test import TestCase
from django.urls import reverse
from .models import ActiveConnection, SuspiciousIP
import json

class WebhookManagerTests(TestCase):
    
    def test_webhook_endpoint(self):
        """Probar endpoint de webhook"""
        response = self.client.post(
            reverse('webhook_endpoint'),
            data=json.dumps({'test': 'data'}),
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 200)
    
    def test_connection_status(self):
        """Probar endpoint de estado de conexiones"""
        response = self.client.get(reverse('connection_status'))
        self.assertEqual(response.status_code, 200)
    
    def test_health_check(self):
        """Probar health check"""
        response = self.client.get(reverse('health_check'))
        self.assertEqual(response.status_code, 200)