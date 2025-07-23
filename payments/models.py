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
import os
from django.utils import timezone

User = get_user_model()

class Payment(models.Model):
    PAYMENT_METHOD_CHOICES = [
        ('card', _('Carte bancaire')),
        ('mobile_money', _('Mobile Money')),
        ('cash_on_delivery', _('Paiement à la livraison')),
        ('store_pickup', _('Retrait en boutique')),
    ]
    
    STATUS_CHOICES = [
        ('pending', _('En attente')),
        ('processing', _('En cours')),
        ('completed', _('Terminé')),
        ('failed', _('Échoué')),
        ('cancelled', _('Annulé')),
        ('refunded', _('Remboursé')),
        ('pending_delivery_confirmation', _('En attente de confirmation du livreur')),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    order = models.OneToOneField(Order, on_delete=models.CASCADE, related_name='payment')
    payment_method = models.CharField(max_length=20, choices=PAYMENT_METHOD_CHOICES)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    status = models.CharField(max_length=30, choices=STATUS_CHOICES, default='pending')  # Changé de max_length=20 à max_length=30
    confirmation_code = models.CharField(max_length=6, unique=True, blank=True)
    qr_code = models.TextField(blank=True)
    qr_code_image = models.ImageField(upload_to='qrcodes/', blank=True, null=True)
    confirmation_attempts = models.PositiveIntegerField(default=0)
    qr_code_expires_at = models.DateTimeField(null=True, blank=True)
    transaction_id = models.CharField(max_length=100, blank=True)
    payment_gateway_response = models.JSONField(default=dict, blank=True)
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
        if not self.qr_code:
            self.qr_code = self.generate_qr_code_data()
            self.generate_qr_code_image()
            self.qr_code_expires_at = timezone.now() + timezone.timedelta(minutes=10)
        super().save(*args, **kwargs)
    
    def generate_confirmation_code(self):
        """Générer un code de confirmation unique à 6 chiffres"""
        while True:
            code = ''.join(random.choices(string.digits, k=6))
            if not Payment.objects.filter(confirmation_code=code).exists():
                return code
    
    def generate_qr_code_data(self):
        """Générer les données pour le QR code"""
        return f"ORDER:{self.order.id}|CODE:{self.confirmation_code}|AMOUNT:{self.amount}|URL:{self.get_confirmation_url()}"
    
    def generate_qr_code_image(self):
        """Générer et sauvegarder l'image QR code"""
        qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_L,
            box_size=10,
            border=4,
        )
        qr.add_data(self.qr_code)
        qr.make(fit=True)
        img = qr.make_image(fill_color="black", back_color="white")
        
        buffer = BytesIO()
        img.save(buffer)
        filename = f"qrcode_{self.id}.png"
        self.qr_code_image.save(filename, File(buffer), save=False)
        buffer.close()
    
    def get_confirmation_url(self):
        """Générer l'URL pour la page de confirmation"""
        from django.urls import reverse
        return reverse('payments:confirm_payment', kwargs={'payment_id': self.id})

class PaymentConfirmation(models.Model):
    payment = models.ForeignKey(Payment, on_delete=models.CASCADE, related_name='confirmations')
    confirmed_by = models.ForeignKey(User, on_delete=models.CASCADE)
    confirmation_method = models.CharField(max_length=20, choices=[
        ('qr_code', _('QR Code')),
        ('manual_code', _('Code manuel')),
        ('admin', _('Administrateur')),
    ])
    confirmed_at = models.DateTimeField(auto_now_add=True)
    notes = models.TextField(blank=True)
    
    class Meta:
        verbose_name = _('Confirmation de paiement')
        verbose_name_plural = _('Confirmations de paiement')
    
    def __str__(self):
        return f"Confirmation {self.payment} par {self.confirmed_by}"

class PaymentDispute(models.Model):
    payment = models.ForeignKey(Payment, on_delete=models.CASCADE, related_name='disputes')
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    reason = models.TextField()
    evidence = models.FileField(upload_to='dispute_evidences/', blank=True, null=True)
    status = models.CharField(max_length=20, choices=[
        ('pending', 'En attente'),
        ('resolved', 'Résolu'),
        ('rejected', 'Rejeté')
    ], default='pending')
    created_at = models.DateTimeField(auto_now_add=True)
    resolved_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        verbose_name = 'Litige de paiement'
        verbose_name_plural = 'Litiges de paiement'

    def __str__(self):
        return f"Litige {self.id} pour paiement {self.payment.id}"

class Invoice(models.Model):
    payment = models.OneToOneField(Payment, on_delete=models.CASCADE, related_name='invoice')
    invoice_number = models.CharField(max_length=20, unique=True)
    pdf_file = models.FileField(upload_to='invoices/', blank=True)
    generated_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = _('Facture')
        verbose_name_plural = _('Factures')
    
    def __str__(self):
        return f"Facture {self.invoice_number}"
    
    def save(self, *args, **kwargs):
        if not self.invoice_number:
            self.invoice_number = self.generate_invoice_number()
        super().save(*args, **kwargs)
    
    def generate_invoice_number(self):
        """Générer un numéro de facture unique"""
        from datetime import datetime
        year = datetime.now().year
        count = Invoice.objects.filter(generated_at__year=year).count() + 1
        return f"INV-{year}-{count:06d}"