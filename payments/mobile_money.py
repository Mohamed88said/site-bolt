import requests
import json
from django.conf import settings
from decimal import Decimal
import logging

logger = logging.getLogger(__name__)

class MobileMoneyProcessor:
    """Processeur de paiement Mobile Money pour l'Afrique"""
    
    def __init__(self):
        self.api_url = getattr(settings, 'MOBILE_MONEY_API_URL', 'https://api.mobilemoney.com')
        self.api_key = getattr(settings, 'MOBILE_MONEY_API_KEY', '')
        self.merchant_id = getattr(settings, 'MOBILE_MONEY_MERCHANT_ID', '')
    
    def initiate_payment(self, amount, phone_number, provider='orange', reference=None):
        """Initier un paiement Mobile Money"""
        try:
            payload = {
                'merchant_id': self.merchant_id,
                'amount': float(amount),
                'phone_number': phone_number,
                'provider': provider,  # orange, mtn, moov, etc.
                'reference': reference or f"PAY_{phone_number}_{amount}",
                'callback_url': f"{settings.SITE_URL}/payments/mobile-money/callback/"
            }
            
            headers = {
                'Authorization': f'Bearer {self.api_key}',
                'Content-Type': 'application/json'
            }
            
            response = requests.post(
                f"{self.api_url}/payments/initiate",
                json=payload,
                headers=headers,
                timeout=30
            )
            
            if response.status_code == 200:
                return response.json()
            else:
                logger.error(f"Erreur Mobile Money: {response.text}")
                return None
                
        except requests.RequestException as e:
            logger.error(f"Erreur réseau Mobile Money: {e}")
            return None
    
    def check_payment_status(self, transaction_id):
        """Vérifier le statut d'un paiement"""
        try:
            headers = {
                'Authorization': f'Bearer {self.api_key}',
                'Content-Type': 'application/json'
            }
            
            response = requests.get(
                f"{self.api_url}/payments/{transaction_id}/status",
                headers=headers,
                timeout=30
            )
            
            if response.status_code == 200:
                return response.json()
            else:
                return None
                
        except requests.RequestException as e:
            logger.error(f"Erreur vérification statut: {e}")
            return None
    
    def get_supported_providers(self, country_code='GN'):
        """Obtenir les fournisseurs supportés par pays"""
        providers = {
            'GN': ['orange', 'mtn'],  # Guinée
            'CI': ['orange', 'mtn', 'moov'],  # Côte d'Ivoire
            'SN': ['orange', 'free'],  # Sénégal
            'ML': ['orange', 'malitel'],  # Mali
        }
        return providers.get(country_code, ['orange', 'mtn'])