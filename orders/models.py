from django.db import models
from django.contrib.auth import get_user_model
from django.utils.translation import gettext_lazy as _
from products.models import Product, ProductVariant
from geolocation.models import LocationPoint
from decimal import Decimal
import uuid

User = get_user_model()

class Order(models.Model):
    STATUS_CHOICES = [
        ('pending', _('En attente')),
        ('confirmed', _('Confirmée')),
        ('processing', _('En traitement')),
        ('shipped', _('Expédiée')),
        ('delivered', _('Livrée')),
        ('cancelled', _('Annulée')),
        ('refunded', _('Remboursée')),
    ]
    
    PAYMENT_STATUS_CHOICES = [
        ('pending', _('En attente')),
        ('completed', _('Terminé')),
        ('failed', _('Échoué')),
        ('refunded', _('Remboursé')),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='orders')
    location_point = models.ForeignKey(LocationPoint, on_delete=models.SET_NULL, null=True, blank=True,
                                     related_name='orders', verbose_name=_('Point de localisation'))
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    payment_status = models.CharField(max_length=20, choices=PAYMENT_STATUS_CHOICES, default='pending')
    total_amount = models.DecimalField(max_digits=10, decimal_places=2)
    shipping_cost = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    tax_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    
    # Adresse de livraison
    shipping_first_name = models.CharField(max_length=100)
    shipping_last_name = models.CharField(max_length=100)
    shipping_address = models.TextField()
    shipping_city = models.CharField(max_length=100)
    shipping_postal_code = models.CharField(max_length=10)
    shipping_country = models.CharField(max_length=100, default='Guinée')
    shipping_phone = models.CharField(max_length=20, blank=True)
    
    # Adresse de facturation
    billing_first_name = models.CharField(max_length=100)
    billing_last_name = models.CharField(max_length=100)
    billing_address = models.TextField()
    billing_city = models.CharField(max_length=100)
    billing_postal_code = models.CharField(max_length=10)
    billing_country = models.CharField(max_length=100, default='Guinée')
    
    # Informations de paiement
    payment_method = models.CharField(max_length=50, default='cash_on_delivery')
    payment_id = models.CharField(max_length=100, blank=True)
    
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = _('Commande')
        verbose_name_plural = _('Commandes')
        ordering = ['-created_at']
    
    def __str__(self):
        return f"Commande #{str(self.id)[:8]}"
    
    @property
    def total_with_shipping(self):
        return self.total_amount + self.shipping_cost + self.tax_amount
    
    @property
    def can_be_cancelled(self):
        return self.status in ['pending', 'confirmed']
    
    @property
    def full_shipping_address(self):
        return f"{self.shipping_address}, {self.shipping_city} {self.shipping_postal_code}, {self.shipping_country}"
    
    @property
    def shipping_full_name(self):
        return f"{self.shipping_first_name} {self.shipping_last_name}"

class OrderItem(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='items')
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    variant = models.ForeignKey(ProductVariant, on_delete=models.CASCADE, null=True, blank=True)
    quantity = models.PositiveIntegerField()
    price = models.DecimalField(max_digits=10, decimal_places=2)
    total_price = models.DecimalField(max_digits=10, decimal_places=2)
    
    class Meta:
        verbose_name = _('Article de commande')
        verbose_name_plural = _('Articles de commande')
    
    def __str__(self):
        return f"{self.quantity} x {self.product.name}"
    
    def save(self, *args, **kwargs):
        if not self.total_price:
            self.total_price = self.price * self.quantity
        super().save(*args, **kwargs)

class OrderStatusHistory(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='status_history')
    status = models.CharField(max_length=20, choices=Order.STATUS_CHOICES)
    comment = models.TextField(blank=True)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = _('Historique de statut')
        verbose_name_plural = _('Historiques de statut')
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.order} - {self.get_status_display()}"