from django.db import models
from django.contrib.auth import get_user_model
from django.utils.translation import gettext_lazy as _
from orders.models import Order
from geolocation.models import LocationPoint, DeliveryZone
import uuid

User = get_user_model()

class Delivery(models.Model):
    STATUS_CHOICES = [
        ('pending', _('En attente')),
        ('assigned', _('Assignée')),
        ('in_progress', _('En cours')),
        ('completed', _('Terminée')),
        ('cancelled', _('Annulée')),
    ]
    
    PAID_BY_CHOICES = [
        ('buyer', _('Acheteur')),
        ('seller', _('Vendeur')),
    ]
    
    order = models.OneToOneField(Order, on_delete=models.CASCADE, related_name='delivery')
    delivery_person = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, 
                                      related_name='deliveries', limit_choices_to={'user_type': 'delivery'})
    location_point = models.ForeignKey(LocationPoint, on_delete=models.SET_NULL, null=True, blank=True,
                                     related_name='deliveries')
    delivery_zone = models.ForeignKey(DeliveryZone, on_delete=models.SET_NULL, null=True, blank=True,
                                    related_name='deliveries')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    tracking_number = models.CharField(max_length=100, unique=True, blank=True)
    delivery_cost = models.DecimalField(max_digits=10, decimal_places=2, default=15000)  # 15,000 GNF par défaut
    paid_by = models.CharField(max_length=20, choices=PAID_BY_CHOICES, default='buyer')
    estimated_delivery_time = models.DateTimeField(null=True, blank=True)
    actual_delivery_time = models.DateTimeField(null=True, blank=True)
    delivery_notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = _('Livraison')
        verbose_name_plural = _('Livraisons')
        ordering = ['-created_at']
    
    def __str__(self):
        return f"Livraison {self.tracking_number or self.id} - {self.order}"
    
    def save(self, *args, **kwargs):
        if not self.tracking_number:
            self.tracking_number = str(uuid.uuid4())[:8].upper()
        super().save(*args, **kwargs)
    
    def calculate_delivery_cost(self):
        """Calcule le coût de livraison basé sur la distance"""
        if not self.location_point:
            return self.delivery_cost
        
        # Obtenir la localisation du vendeur
        seller = self.order.items.first().product.seller if self.order.items.exists() else None
        if not seller:
            return self.delivery_cost
        
        # Coordonnées par défaut (Conakry)
        seller_location = None
        if hasattr(seller, 'seller_profile') and seller.seller_profile.location_point:
            seller_location = seller.seller_profile.location_point
        
        if seller_location:
            distance = seller_location.calculate_distance_to(self.location_point)
            if distance:
                # Coût de base + distance
                zone = self.delivery_zone or self.get_delivery_zone()
                if zone:
                    return zone.calculate_delivery_cost(distance)
                else:
                    # Calcul simple : 15,000 GNF + 1,000 GNF/km
                    return 15000 + (distance * 1000)
        
        return self.delivery_cost
    
    def get_delivery_zone(self):
        """Trouve la zone de livraison appropriée"""
        if not self.location_point:
            return None
        
        zones = DeliveryZone.objects.filter(
            models.Q(communes=self.location_point.commune) |
            models.Q(prefectures=self.location_point.prefecture) |
            models.Q(regions=self.location_point.region),
            is_active=True
        ).first()
        
        return zones

class DeliveryRequest(models.Model):
    """Demandes de livraison par les livreurs"""
    delivery = models.ForeignKey(Delivery, on_delete=models.CASCADE, related_name='requests')
    delivery_person = models.ForeignKey(User, on_delete=models.CASCADE, related_name='delivery_requests',
                                      limit_choices_to={'user_type': 'delivery'})
    message = models.TextField(blank=True, verbose_name=_('Message'))
    proposed_cost = models.DecimalField(max_digits=10, decimal_places=2, default=0.00, verbose_name=_('Coût proposé'))
    is_accepted = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = _('Demande de livraison')
        verbose_name_plural = _('Demandes de livraison')
        unique_together = ['delivery', 'delivery_person']
        ordering = ['-created_at']
    
    def __str__(self):
        return f"Demande de {self.delivery_person.username} pour {self.delivery}"

class DeliveryRating(models.Model):
    """Évaluations des livraisons"""
    delivery = models.OneToOneField(Delivery, on_delete=models.CASCADE, related_name='rating')
    rating = models.IntegerField(choices=[(i, str(i)) for i in range(1, 6)])
    comment = models.TextField(blank=True)
    created_by = models.ForeignKey(User, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = _('Évaluation de livraison')
        verbose_name_plural = _('Évaluations de livraison')
    
    def __str__(self):
        return f"Évaluation {self.rating}/5 pour {self.delivery}"