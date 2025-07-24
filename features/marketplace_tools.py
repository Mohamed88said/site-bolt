"""
OUTILS MARKETPLACE AVANCÉS
- Système d'enchères
- Négociation de prix
- Ventes flash
"""

from django.db import models
from django.contrib.auth import get_user_model
from django.utils import timezone
from datetime import timedelta

User = get_user_model()

class Auction(models.Model):
    """Système d'enchères"""
    product = models.ForeignKey('products.Product', on_delete=models.CASCADE)
    seller = models.ForeignKey(User, on_delete=models.CASCADE, related_name='auctions')
    starting_price = models.DecimalField(max_digits=10, decimal_places=2)
    current_price = models.DecimalField(max_digits=10, decimal_places=2)
    reserve_price = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    start_time = models.DateTimeField()
    end_time = models.DateTimeField()
    is_active = models.BooleanField(default=True)
    winner = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='won_auctions')
    
    @property
    def time_remaining(self):
        if self.end_time > timezone.now():
            return self.end_time - timezone.now()
        return timedelta(0)

class Bid(models.Model):
    """Enchères"""
    auction = models.ForeignKey(Auction, on_delete=models.CASCADE, related_name='bids')
    bidder = models.ForeignKey(User, on_delete=models.CASCADE)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    created_at = models.DateTimeField(auto_now_add=True)
    is_winning = models.BooleanField(default=False)

class PriceNegotiation(models.Model):
    """Négociation de prix"""
    product = models.ForeignKey('products.Product', on_delete=models.CASCADE)
    buyer = models.ForeignKey(User, on_delete=models.CASCADE, related_name='negotiations_as_buyer')
    seller = models.ForeignKey(User, on_delete=models.CASCADE, related_name='negotiations_as_seller')
    original_price = models.DecimalField(max_digits=10, decimal_places=2)
    proposed_price = models.DecimalField(max_digits=10, decimal_places=2)
    counter_price = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    final_price = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    status = models.CharField(max_length=20, choices=[
        ('pending', 'En attente'),
        ('countered', 'Contre-proposition'),
        ('accepted', 'Accepté'),
        ('rejected', 'Rejeté'),
        ('expired', 'Expiré')
    ], default='pending')
    quantity = models.IntegerField(default=1)
    message = models.TextField(blank=True)
    expires_at = models.DateTimeField()
    created_at = models.DateTimeField(auto_now_add=True)

class FlashSale(models.Model):
    """Ventes flash"""
    name = models.CharField(max_length=100)
    products = models.ManyToManyField('products.Product', through='FlashSaleProduct')
    start_time = models.DateTimeField()
    end_time = models.DateTimeField()
    is_active = models.BooleanField(default=True)
    max_quantity_per_user = models.IntegerField(default=1)
    regions = models.ManyToManyField('geolocation.GuineaRegion', blank=True)
    
    @property
    def is_live(self):
        now = timezone.now()
        return self.start_time <= now <= self.end_time and self.is_active

class FlashSaleProduct(models.Model):
    """Produits en vente flash"""
    flash_sale = models.ForeignKey(FlashSale, on_delete=models.CASCADE)
    product = models.ForeignKey('products.Product', on_delete=models.CASCADE)
    original_price = models.DecimalField(max_digits=10, decimal_places=2)
    flash_price = models.DecimalField(max_digits=10, decimal_places=2)
    available_quantity = models.IntegerField()
    sold_quantity = models.IntegerField(default=0)
    
    @property
    def discount_percentage(self):
        return ((self.original_price - self.flash_price) / self.original_price) * 100
    
    @property
    def is_sold_out(self):
        return self.sold_quantity >= self.available_quantity