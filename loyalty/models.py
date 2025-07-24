from django.db import models
from django.contrib.auth import get_user_model
from django.utils.translation import gettext_lazy as _
from decimal import Decimal
import random
import string

User = get_user_model()

class LoyaltyProgram(models.Model):
    """Programme de fidélité adapté à la Guinée"""
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='loyalty')
    points_balance = models.DecimalField(max_digits=12, decimal_places=0, default=0, verbose_name=_('Solde points (GNF)'))
    total_earned = models.DecimalField(max_digits=12, decimal_places=0, default=0, verbose_name=_('Total gagné'))
    total_spent = models.DecimalField(max_digits=12, decimal_places=0, default=0, verbose_name=_('Total dépensé'))
    level = models.CharField(max_length=20, choices=[
        ('bronze', _('Bronze')),
        ('silver', _('Argent')), 
        ('gold', _('Or')),
        ('platinum', _('Platine')),
        ('diamond', _('Diamant'))
    ], default='bronze', verbose_name=_('Niveau'))
    referral_code = models.CharField(max_length=10, unique=True, verbose_name=_('Code de parrainage'))
    referred_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, verbose_name=_('Parrainé par'))
    referral_count = models.IntegerField(default=0, verbose_name=_('Nombre de parrainages'))
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = _('Programme de fidélité')
        verbose_name_plural = _('Programmes de fidélité')
    
    def __str__(self):
        return f"Fidélité {self.user.username} - {self.get_level_display()}"
    
    def save(self, *args, **kwargs):
        if not self.referral_code:
            self.referral_code = self.generate_referral_code()
        super().save(*args, **kwargs)
    
    def generate_referral_code(self):
        """Générer un code de parrainage unique"""
        while True:
            code = ''.join(random.choices(string.ascii_uppercase + string.digits, k=8))
            if not LoyaltyProgram.objects.filter(referral_code=code).exists():
                return code
    
    def calculate_level(self):
        """Calculer le niveau basé sur les achats totaux"""
        total = float(self.total_earned)
        if total >= 50000000:  # 50M GNF
            return 'diamond'
        elif total >= 20000000:  # 20M GNF
            return 'platinum'
        elif total >= 10000000:  # 10M GNF
            return 'gold'
        elif total >= 5000000:   # 5M GNF
            return 'silver'
        return 'bronze'
    
    def add_points(self, amount, reason="", transaction_type='purchase'):
        """Ajouter des points (1% du montant d'achat en GNF)"""
        points = Decimal(str(amount)) * Decimal('0.01')
        self.points_balance += points
        self.total_earned += points
        old_level = self.level
        self.level = self.calculate_level()
        self.save()
        
        # Créer la transaction
        LoyaltyTransaction.objects.create(
            user=self.user,
            points=points,
            transaction_type='earned',
            reason=reason or f"Achat de {amount} GNF",
            order_amount=amount
        )
        
        # Bonus de niveau
        if old_level != self.level:
            level_bonus = {
                'silver': 50000,
                'gold': 100000,
                'platinum': 200000,
                'diamond': 500000
            }.get(self.level, 0)
            
            if level_bonus:
                self.points_balance += level_bonus
                self.save()
                LoyaltyTransaction.objects.create(
                    user=self.user,
                    points=level_bonus,
                    transaction_type='bonus',
                    reason=f"Bonus niveau {self.get_level_display()}"
                )
    
    def redeem_points(self, points, reason=""):
        """Utiliser des points"""
        if self.points_balance >= points:
            self.points_balance -= points
            self.total_spent += points
            self.save()
            
            LoyaltyTransaction.objects.create(
                user=self.user,
                points=-points,
                transaction_type='redeemed',
                reason=reason
            )
            return True
        return False

class LoyaltyTransaction(models.Model):
    """Historique des transactions de fidélité"""
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='loyalty_transactions')
    points = models.DecimalField(max_digits=12, decimal_places=0, verbose_name=_('Points'))
    transaction_type = models.CharField(max_length=20, choices=[
        ('earned', _('Gagné')),
        ('redeemed', _('Utilisé')),
        ('expired', _('Expiré')),
        ('bonus', _('Bonus')),
        ('referral', _('Parrainage'))
    ], verbose_name=_('Type'))
    reason = models.CharField(max_length=200, verbose_name=_('Raison'))
    order_amount = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = _('Transaction fidélité')
        verbose_name_plural = _('Transactions fidélité')
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.user.username} - {self.points} points ({self.get_transaction_type_display()})"

class GuineaReward(models.Model):
    """Récompenses spécifiques à la Guinée"""
    name = models.CharField(max_length=100, verbose_name=_('Nom'))
    description = models.TextField(verbose_name=_('Description'))
    points_required = models.DecimalField(max_digits=12, decimal_places=0, verbose_name=_('Points requis'))
    reward_type = models.CharField(max_length=20, choices=[
        ('discount', _('Réduction')),
        ('free_delivery', _('Livraison gratuite')),
        ('product', _('Produit gratuit')),
        ('cashback', _('Remboursement GNF')),
        ('subscription_upgrade', _('Upgrade abonnement')),
        ('local_service', _('Service local'))
    ], verbose_name=_('Type de récompense'))
    value = models.DecimalField(max_digits=12, decimal_places=2, verbose_name=_('Valeur'))
    is_active = models.BooleanField(default=True, verbose_name=_('Actif'))
    region_specific = models.ForeignKey('geolocation.GuineaRegion', on_delete=models.CASCADE, null=True, blank=True)
    subscription_required = models.CharField(max_length=20, choices=User.SUBSCRIPTION_CHOICES, default='free')
    stock_quantity = models.IntegerField(default=-1, verbose_name=_('Stock (-1 = illimité)'))
    redeemed_count = models.IntegerField(default=0, verbose_name=_('Nombre d\'échanges'))
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = _('Récompense')
        verbose_name_plural = _('Récompenses')
    
    def __str__(self):
        return f"{self.name} - {self.points_required} points"
    
    @property
    def is_available(self):
        return self.is_active and (self.stock_quantity == -1 or self.redeemed_count < self.stock_quantity)

class RewardRedemption(models.Model):
    """Échanges de récompenses"""
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    reward = models.ForeignKey(GuineaReward, on_delete=models.CASCADE)
    points_used = models.DecimalField(max_digits=12, decimal_places=0)
    status = models.CharField(max_length=20, choices=[
        ('pending', _('En attente')),
        ('approved', _('Approuvé')),
        ('delivered', _('Livré')),
        ('cancelled', _('Annulé'))
    ], default='pending')
    redemption_code = models.CharField(max_length=20, unique=True)
    created_at = models.DateTimeField(auto_now_add=True)
    processed_at = models.DateTimeField(null=True, blank=True)
    
    def save(self, *args, **kwargs):
        if not self.redemption_code:
            self.redemption_code = ''.join(random.choices(string.ascii_uppercase + string.digits, k=12))
        super().save(*args, **kwargs)