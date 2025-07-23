from django.db import models
from django.contrib.auth import get_user_model
from orders.models import Order, OrderItem
from django.utils.translation import gettext_lazy as _

User = get_user_model()

class ReturnRequest(models.Model):
    STATUS_CHOICES = [
        ('pending', _('En attente')),
        ('approved', _('Approuvée')),
        ('rejected', _('Rejetée')),
        ('processing', _('En cours de traitement')),
        ('completed', _('Terminée')),
        ('cancelled', _('Annulée')),
    ]
    
    REASON_CHOICES = [
        ('defective', _('Produit défectueux')),
        ('wrong_item', _('Mauvais article')),
        ('not_as_described', _('Non conforme à la description')),
        ('damaged', _('Endommagé pendant le transport')),
        ('changed_mind', _('Changement d\'avis')),
        ('size_issue', _('Problème de taille')),
        ('quality_issue', _('Problème de qualité')),
        ('other', _('Autre')),
    ]
    
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='return_requests')
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='return_requests')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    reason = models.CharField(max_length=20, choices=REASON_CHOICES)
    description = models.TextField(verbose_name=_('Description détaillée'))
    refund_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    admin_notes = models.TextField(blank=True, verbose_name=_('Notes administrateur'))
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = _('Demande de retour')
        verbose_name_plural = _('Demandes de retour')
        ordering = ['-created_at']
    
    def __str__(self):
        return f"Retour #{self.id} - Commande #{str(self.order.id)[:8]}"
    
    @property
    def can_be_cancelled(self):
        return self.status in ['pending', 'approved']

class ReturnItem(models.Model):
    return_request = models.ForeignKey(ReturnRequest, on_delete=models.CASCADE, related_name='items')
    order_item = models.ForeignKey(OrderItem, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField()
    condition = models.TextField(verbose_name=_('État du produit'))
    images = models.JSONField(default=list, verbose_name=_('Photos du produit'))
    
    class Meta:
        verbose_name = _('Article de retour')
        verbose_name_plural = _('Articles de retour')
    
    def __str__(self):
        return f"{self.quantity}x {self.order_item.product.name}"

class ReturnShipping(models.Model):
    return_request = models.OneToOneField(ReturnRequest, on_delete=models.CASCADE, related_name='shipping')
    tracking_number = models.CharField(max_length=100, blank=True)
    shipping_cost = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    pickup_address = models.TextField(verbose_name=_('Adresse de récupération'))
    pickup_date = models.DateTimeField(null=True, blank=True)
    delivered_date = models.DateTimeField(null=True, blank=True)
    notes = models.TextField(blank=True)
    
    class Meta:
        verbose_name = _('Expédition de retour')
        verbose_name_plural = _('Expéditions de retour')
    
    def __str__(self):
        return f"Expédition - {self.return_request}"