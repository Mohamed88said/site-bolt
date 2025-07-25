from django.db import models
from django.contrib.auth import get_user_model
from decimal import Decimal
from products.models import Product, ProductVariant
from geolocation.models import UserLocation, DeliveryZone
from django.utils.translation import gettext_lazy as _

User = get_user_model()

class Cart(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='cart')
    location_point = models.ForeignKey(
        UserLocation, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True, 
        related_name='carts', 
        verbose_name=_('Point de localisation')
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = _('Panier')
        verbose_name_plural = _('Paniers')
    
    def __str__(self):
        return f"Panier de {self.user.username}"
    
    @property
    def total_items(self):
        return self.items.aggregate(total=models.Sum('quantity'))['total'] or 0
    
    @property
    def total_price(self):
        total = Decimal('0.00')
        for item in self.items.all():
            total += Decimal(str(item.total_price))
        return total
    
    @property
    def shipping_cost(self):
        """Calculer les frais de livraison basés sur la DeliveryZone et la distance"""
        if not self.location_point or not self.items.exists():
            return Decimal('15000.00')  # Fallback si pas d'adresse ou panier vide
        
        # Récupérer le vendeur du premier produit (hypothèse : un seul vendeur par panier)
        seller = self.items.first().product.seller
        zone = self._get_delivery_zone()
        if not zone:
            return Decimal('15000.00')  # Fallback si pas de zone
        
        try:
            # Calculer le coût basé sur la zone
            base_cost = float(zone.base_delivery_cost)
            return Decimal(str(base_cost))
        except Exception as e:
            print(f"Erreur calcul livraison: {e}")
            return Decimal('15000.00')  # Fallback en cas d'erreur
    
    @property
    def estimated_delivery_time(self):
        """Récupérer le temps de livraison estimé depuis DeliveryZone"""
        if not self.location_point:
            return "24-48h"  # Fallback
        zone = self._get_delivery_zone()
        return zone.estimated_delivery_time if zone else "24-48h"
    
    def _get_delivery_zone(self):
        """Trouver la DeliveryZone correspondant au LocationPoint"""
        if self.location_point and self.location_point.location_point:
            zones = DeliveryZone.objects.filter(
                models.Q(communes=self.location_point.location_point.commune) |
                models.Q(prefectures=self.location_point.location_point.prefecture) |
                models.Q(regions=self.location_point.location_point.region),
                is_active=True
            ).order_by('communes__isnull', 'prefectures__isnull', 'regions__isnull')
            return zones.first() if zones.exists() else None
        return None
    
    def clear(self):
        self.items.all().delete()
        self.location_point = None
        self.save()

class CartItem(models.Model):
    cart = models.ForeignKey(Cart, on_delete=models.CASCADE, related_name='items')
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    variant = models.ForeignKey(ProductVariant, on_delete=models.CASCADE, null=True, blank=True)
    quantity = models.PositiveIntegerField(default=1)
    added_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = ['cart', 'product', 'variant']
        verbose_name = _('Article du panier')
        verbose_name_plural = _('Articles du panier')
    
    def __str__(self):
        return f"{self.quantity} x {self.product.name}"
    
    @property
    def price(self):
        base_price = Decimal(str(self.product.current_price))
        if self.variant and self.variant.price_adjustment:
            base_price += Decimal(str(self.variant.price_adjustment))
        return base_price
    
    @property
    def total_price(self):
        return self.price * Decimal(str(self.quantity))