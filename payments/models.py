from django.db import models
from django.contrib.auth import get_user_model
from orders.models import Order
from django.utils.translation import gettext_lazy as _
import uuid
import random
import string
import qrcode
from io import BytesIO
from django.core.files import File
from django.utils import timezone

User = get_user_model()

class Payment(models.Model):
    PAYMENT_METHOD_CHOICES = [
        ('stripe', _('Carte bancaire')),
        ('paypal', _('PayPal')),
        ('mobile_money', _('Mobile Money')),
        ('cash_on_delivery', _('Paiement à la livraison')),
    ]
    
    STATUS_CHOICES = [
        ('pending', _('En attente')),
        ('processing', _('En cours')),
        ('completed', _('Terminé')),
        ('failed', _('Échoué')),
        ('cancelled', _('Annulé')),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    order = models.OneToOneField(Order, on_delete=models.CASCADE, related_name='payment')
    payment_method = models.CharField(max_length=20, choices=PAYMENT_METHOD_CHOICES)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    confirmation_code = models.CharField(max_length=6, unique=True, blank=True)
    qr_code_image = models.ImageField(upload_to='qrcodes/', blank=True, null=True)
    
    # Identifiants des processeurs de paiement
    stripe_payment_intent_id = models.CharField(max_length=200, blank=True)
    paypal_order_id = models.CharField(max_length=200, blank=True)
    mobile_money_transaction_id = models.CharField(max_length=200, blank=True)
    mobile_money_provider = models.CharField(max_length=50, blank=True)
    mobile_money_phone = models.CharField(max_length=20, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    confirmed_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        verbose_name = _('Paiement')
        verbose_name_plural = _('Paiements')
    
    def __str__(self):
        return f"Paiement {self.id} - {self.order}"
    
    def save(self, *args, **kwargs):
        if not self.confirmation_code:
            self.confirmation_code = self.generate_confirmation_code()
        if not self.qr_code_image:
            self.generate_qr_code_image()
        super().save(*args, **kwargs)
    
    def generate_confirmation_code(self):
        """Générer un code de confirmation unique à 6 chiffres"""
        while True:
            code = ''.join(random.choices(string.digits, k=6))
            if not Payment.objects.filter(confirmation_code=code).exists():
                return code
    
    def generate_qr_code_image(self):
        """Générer et sauvegarder l'image QR code"""
        qr_data = f"ORDER:{self.order.id}|PAYMENT:{self.id}|CODE:{self.confirmation_code}|AMOUNT:{self.amount}"
        
        qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_L,
            box_size=10,
            border=4,
        )
        qr.add_data(qr_data)
        qr.make(fit=True)
        img = qr.make_image(fill_color="black", back_color="white")
        
        buffer = BytesIO()
        img.save(buffer, format='PNG')
        filename = f"qrcode_{self.id}.png"
        self.qr_code_image.save(filename, File(buffer), save=False)
        buffer.close()
    
    @property
    def qr_scan_url(self):
        """URL pour scanner le QR code"""
        from django.urls import reverse
        from django.conf import settings
        return f"{settings.SITE_URL}{reverse('payments:qr_scan', kwargs={'payment_id': self.id})}"