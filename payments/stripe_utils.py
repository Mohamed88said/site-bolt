import stripe
from django.conf import settings
from decimal import Decimal
import logging

logger = logging.getLogger(__name__)

stripe.api_key = settings.STRIPE_SECRET_KEY

class StripePaymentProcessor:
    @staticmethod
    def create_payment_intent(amount, currency='eur', metadata=None):
        """Créer un PaymentIntent Stripe"""
        try:
            intent = stripe.PaymentIntent.create(
                amount=int(amount * 100),  # Stripe utilise les centimes
                currency=currency,
                metadata=metadata or {},
                automatic_payment_methods={'enabled': True}
            )
            return intent
        except stripe.error.StripeError as e:
            logger.error(f"Erreur Stripe: {e}")
            return None
    
    @staticmethod
    def confirm_payment_intent(payment_intent_id, payment_method_id):
        """Confirmer un PaymentIntent"""
        try:
            intent = stripe.PaymentIntent.confirm(
                payment_intent_id,
                payment_method=payment_method_id
            )
            return intent
        except stripe.error.StripeError as e:
            logger.error(f"Erreur confirmation Stripe: {e}")
            return None
    
    @staticmethod
    def create_refund(payment_intent_id, amount=None):
        """Créer un remboursement"""
        try:
            refund_data = {'payment_intent': payment_intent_id}
            if amount:
                refund_data['amount'] = int(amount * 100)
            
            refund = stripe.Refund.create(**refund_data)
            return refund
        except stripe.error.StripeError as e:
            logger.error(f"Erreur remboursement Stripe: {e}")
            return None