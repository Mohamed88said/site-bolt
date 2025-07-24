from django.db import models
from django.contrib.auth import get_user_model
from django.utils.translation import gettext_lazy as _
from django.utils import timezone
from datetime import timedelta
from decimal import Decimal

User = get_user_model()

class Auction(models.Model):
    """Système d'enchères"""
    product = models.ForeignKey('products.Product', on_delete=models.CASCADE, related_name='auctions')
    seller = models.ForeignKey(User, on_delete=models.CASCADE, related_name='created_auctions')
    title = models.CharField(max_length=200, verbose_name=_('Titre'))
    description = models.TextField(verbose_name=_('Description'))
    starting_price_gnf = models.DecimalField(max_digits=12, decimal_places=0, verbose_name=_('Prix de départ (GNF)'))
    current_price_gnf = models.DecimalField(max_digits=12, decimal_places=0, verbose_name=_('Prix actuel (GNF)'))
    reserve_price_gnf = models.DecimalField(max_digits=12, decimal_places=0, null=True, blank=True, verbose_name=_('Prix de réserve (GNF)'))
    buy_now_price_gnf = models.DecimalField(max_digits=12, decimal_places=0, null=True, blank=True, verbose_name=_('Achat immédiat (GNF)'))
    start_time = models.DateTimeField(verbose_name=_('Début'))
    end_time = models.DateTimeField(verbose_name=_('Fin'))
    auto_extend_minutes = models.IntegerField(default=5, verbose_name=_('Extension auto (minutes)'))
    minimum_bid_increment_gnf = models.DecimalField(max_digits=12, decimal_places=0, default=1000, verbose_name=_('Enchère min (GNF)'))
    is_active = models.BooleanField(default=True, verbose_name=_('Actif'))
    winner = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='won_auctions')
    total_bids = models.IntegerField(default=0, verbose_name=_('Nombre d\'enchères'))
    views = models.IntegerField(default=0, verbose_name=_('Vues'))
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = _('Enchère')
        verbose_name_plural = _('Enchères')
        ordering = ['-created_at']
    
    def __str__(self):
        return f"Enchère: {self.title}"
    
    @property
    def time_remaining(self):
        if self.end_time > timezone.now():
            return self.end_time - timezone.now()
        return timedelta(0)
    
    @property
    def is_live(self):
        now = timezone.now()
        return self.start_time <= now <= self.end_time and self.is_active
    
    @property
    def is_ended(self):
        return timezone.now() > self.end_time
    
    @property
    def reserve_met(self):
        if not self.reserve_price_gnf:
            return True
        return self.current_price_gnf >= self.reserve_price_gnf
    
    def place_bid(self, bidder, amount_gnf):
        """Placer une enchère"""
        if not self.is_live:
            return False, "Enchère non active"
        
        if bidder == self.seller:
            return False, "Le vendeur ne peut pas enchérir"
        
        if amount_gnf < self.current_price_gnf + self.minimum_bid_increment_gnf:
            return False, f"Enchère minimum: {self.current_price_gnf + self.minimum_bid_increment_gnf} GNF"
        
        # Créer l'enchère
        bid = Bid.objects.create(
            auction=self,
            bidder=bidder,
            amount_gnf=amount_gnf
        )
        
        # Mettre à jour l'enchère actuelle
        Bid.objects.filter(auction=self).update(is_winning=False)
        bid.is_winning = True
        bid.save()
        
        self.current_price_gnf = amount_gnf
        self.total_bids += 1
        
        # Extension automatique si enchère dans les dernières minutes
        time_left = self.time_remaining
        if time_left.total_seconds() < (self.auto_extend_minutes * 60):
            self.end_time += timedelta(minutes=self.auto_extend_minutes)
        
        self.save()
        return True, "Enchère placée avec succès"

class Bid(models.Model):
    """Enchères"""
    auction = models.ForeignKey(Auction, on_delete=models.CASCADE, related_name='bids')
    bidder = models.ForeignKey(User, on_delete=models.CASCADE, related_name='bids')
    amount_gnf = models.DecimalField(max_digits=12, decimal_places=0, verbose_name=_('Montant (GNF)'))
    is_winning = models.BooleanField(default=False, verbose_name=_('Enchère gagnante'))
    is_auto_bid = models.BooleanField(default=False, verbose_name=_('Enchère automatique'))
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = _('Enchère')
        verbose_name_plural = _('Enchères')
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.bidder.username} - {self.amount_gnf} GNF"

class PriceNegotiation(models.Model):
    """Négociation de prix"""
    product = models.ForeignKey('products.Product', on_delete=models.CASCADE, related_name='negotiations')
    buyer = models.ForeignKey(User, on_delete=models.CASCADE, related_name='negotiations_as_buyer')
    seller = models.ForeignKey(User, on_delete=models.CASCADE, related_name='negotiations_as_seller')
    original_price_gnf = models.DecimalField(max_digits=12, decimal_places=0, verbose_name=_('Prix original (GNF)'))
    proposed_price_gnf = models.DecimalField(max_digits=12, decimal_places=0, verbose_name=_('Prix proposé (GNF)'))
    counter_price_gnf = models.DecimalField(max_digits=12, decimal_places=0, null=True, blank=True, verbose_name=_('Contre-proposition (GNF)'))
    final_price_gnf = models.DecimalField(max_digits=12, decimal_places=0, null=True, blank=True, verbose_name=_('Prix final (GNF)'))
    status = models.CharField(max_length=20, choices=[
        ('pending', _('En attente')),
        ('countered', _('Contre-proposition')),
        ('accepted', _('Accepté')),
        ('rejected', _('Rejeté')),
        ('expired', _('Expiré'))
    ], default='pending', verbose_name=_('Statut'))
    quantity = models.IntegerField(default=1, verbose_name=_('Quantité'))
    buyer_message = models.TextField(blank=True, verbose_name=_('Message acheteur'))
    seller_message = models.TextField(blank=True, verbose_name=_('Message vendeur'))
    expires_at = models.DateTimeField(verbose_name=_('Expire le'))
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = _('Négociation de prix')
        verbose_name_plural = _('Négociations de prix')
        ordering = ['-created_at']
    
    def __str__(self):
        return f"Négociation {self.product.name} - {self.buyer.username}"
    
    @property
    def is_expired(self):
        return timezone.now() > self.expires_at
    
    @property
    def savings_gnf(self):
        if self.final_price_gnf:
            return self.original_price_gnf - self.final_price_gnf
        elif self.proposed_price_gnf:
            return self.original_price_gnf - self.proposed_price_gnf
        return 0

class FlashSale(models.Model):
    """Ventes flash"""
    name = models.CharField(max_length=100, verbose_name=_('Nom'))
    description = models.TextField(verbose_name=_('Description'))
    start_time = models.DateTimeField(verbose_name=_('Début'))
    end_time = models.DateTimeField(verbose_name=_('Fin'))
    is_active = models.BooleanField(default=True, verbose_name=_('Actif'))
    max_quantity_per_user = models.IntegerField(default=1, verbose_name=_('Quantité max par utilisateur'))
    regions = models.ManyToManyField('geolocation.GuineaRegion', blank=True, verbose_name=_('Régions'))
    banner_image = models.ImageField(upload_to='flash_sales/', blank=True, verbose_name=_('Image bannière'))
    created_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='created_flash_sales')
    total_sales_gnf = models.DecimalField(max_digits=12, decimal_places=0, default=0)
    total_orders = models.IntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = _('Vente flash')
        verbose_name_plural = _('Ventes flash')
        ordering = ['-created_at']
    
    def __str__(self):
        return self.name
    
    @property
    def is_live(self):
        now = timezone.now()
        return self.start_time <= now <= self.end_time and self.is_active
    
    @property
    def is_upcoming(self):
        return timezone.now() < self.start_time
    
    @property
    def is_ended(self):
        return timezone.now() > self.end_time

class FlashSaleProduct(models.Model):
    """Produits en vente flash"""
    flash_sale = models.ForeignKey(FlashSale, on_delete=models.CASCADE, related_name='flash_products')
    product = models.ForeignKey('products.Product', on_delete=models.CASCADE)
    original_price_gnf = models.DecimalField(max_digits=12, decimal_places=0, verbose_name=_('Prix original (GNF)'))
    flash_price_gnf = models.DecimalField(max_digits=12, decimal_places=0, verbose_name=_('Prix flash (GNF)'))
    available_quantity = models.IntegerField(verbose_name=_('Quantité disponible'))
    sold_quantity = models.IntegerField(default=0, verbose_name=_('Quantité vendue'))
    max_per_user = models.IntegerField(default=1, verbose_name=_('Max par utilisateur'))
    
    class Meta:
        verbose_name = _('Produit vente flash')
        verbose_name_plural = _('Produits ventes flash')
        unique_together = ['flash_sale', 'product']
    
    def __str__(self):
        return f"{self.flash_sale.name} - {self.product.name}"
    
    @property
    def discount_percentage(self):
        if self.original_price_gnf > 0:
            return ((self.original_price_gnf - self.flash_price_gnf) / self.original_price_gnf) * 100
        return 0
    
    @property
    def is_sold_out(self):
        return self.sold_quantity >= self.available_quantity
    
    @property
    def stock_percentage(self):
        if self.available_quantity > 0:
            return (self.sold_quantity / self.available_quantity) * 100
        return 100

class CommunityGroup(models.Model):
    """Groupes d'achat communautaires"""
    name = models.CharField(max_length=100, verbose_name=_('Nom'))
    description = models.TextField(verbose_name=_('Description'))
    creator = models.ForeignKey(User, on_delete=models.CASCADE, related_name='created_groups')
    members = models.ManyToManyField(User, through='GroupMembership', related_name='community_groups')
    region = models.ForeignKey('geolocation.GuineaRegion', on_delete=models.CASCADE, verbose_name=_('Région'))
    prefecture = models.ForeignKey('geolocation.GuineaPrefecture', on_delete=models.CASCADE, null=True, blank=True)
    is_active = models.BooleanField(default=True, verbose_name=_('Actif'))
    is_public = models.BooleanField(default=True, verbose_name=_('Public'))
    min_members_for_discount = models.IntegerField(default=5, verbose_name=_('Membres min pour réduction'))
    group_discount_percentage = models.DecimalField(max_digits=5, decimal_places=2, default=10, verbose_name=_('% réduction groupe'))
    max_members = models.IntegerField(default=50, verbose_name=_('Membres max'))
    group_image = models.ImageField(upload_to='groups/', blank=True, verbose_name=_('Image du groupe'))
    total_savings_gnf = models.DecimalField(max_digits=12, decimal_places=0, default=0)
    total_orders = models.IntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = _('Groupe communautaire')
        verbose_name_plural = _('Groupes communautaires')
        ordering = ['-created_at']
    
    def __str__(self):
        return self.name
    
    @property
    def member_count(self):
        return self.members.count()
    
    @property
    def discount_active(self):
        return self.member_count >= self.min_members_for_discount
    
    @property
    def can_join(self):
        return self.is_active and self.member_count < self.max_members

class GroupMembership(models.Model):
    """Adhésion aux groupes"""
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    group = models.ForeignKey(CommunityGroup, on_delete=models.CASCADE)
    role = models.CharField(max_length=20, choices=[
        ('member', _('Membre')),
        ('moderator', _('Modérateur')),
        ('admin', _('Administrateur'))
    ], default='member', verbose_name=_('Rôle'))
    joined_at = models.DateTimeField(auto_now_add=True)
    is_active = models.BooleanField(default=True)
    
    class Meta:
        verbose_name = _('Adhésion groupe')
        verbose_name_plural = _('Adhésions groupes')
        unique_together = ['user', 'group']
    
    def __str__(self):
        return f"{self.user.username} - {self.group.name}"

class GroupOrder(models.Model):
    """Commandes groupées"""
    group = models.ForeignKey(CommunityGroup, on_delete=models.CASCADE, related_name='group_orders')
    product = models.ForeignKey('products.Product', on_delete=models.CASCADE)
    target_quantity = models.IntegerField(verbose_name=_('Quantité cible'))
    current_quantity = models.IntegerField(default=0, verbose_name=_('Quantité actuelle'))
    original_price_gnf = models.DecimalField(max_digits=12, decimal_places=0, verbose_name=_('Prix original (GNF)'))
    group_price_gnf = models.DecimalField(max_digits=12, decimal_places=0, verbose_name=_('Prix groupe (GNF)'))
    deadline = models.DateTimeField(verbose_name=_('Date limite'))
    is_active = models.BooleanField(default=True, verbose_name=_('Actif'))
    is_successful = models.BooleanField(default=False, verbose_name=_('Réussi'))
    created_by = models.ForeignKey(User, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = _('Commande groupée')
        verbose_name_plural = _('Commandes groupées')
    
    def __str__(self):
        return f"Commande groupe {self.group.name} - {self.product.name}"
    
    @property
    def progress_percentage(self):
        if self.target_quantity > 0:
            return min((self.current_quantity / self.target_quantity) * 100, 100)
        return 0
    
    @property
    def is_target_reached(self):
        return self.current_quantity >= self.target_quantity