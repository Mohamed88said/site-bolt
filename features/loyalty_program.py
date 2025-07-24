"""
PROGRAMME DE FIDÉLITÉ GUINÉEN
- Points de fidélité en GNF
- Récompenses locales
- Parrainage communautaire
"""

from django.db import models
from django.contrib.auth import get_user_model
from decimal import Decimal

User = get_user_model()

class LoyaltyProgram(models.Model):
    """Programme de fidélité adapté à la Guinée"""
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='loyalty')
    points_balance = models.DecimalField(max_digits=10, decimal_places=0, default=0)  # En GNF
    total_earned = models.DecimalField(max_digits=10, decimal_places=0, default=0)
    level = models.CharField(max_length=20, choices=[
        ('bronze', 'Bronze'),
        ('silver', 'Argent'), 
        ('gold', 'Or'),
        ('platinum', 'Platine'),
        ('diamond', 'Diamant')
    ], default='bronze')
    referral_code = models.CharField(max_length=10, unique=True)
    referred_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    
    def calculate_level(self):
        """Calculer le niveau basé sur les achats totaux"""
        if self.total_earned >= 5000000:  # 5M GNF
            return 'diamond'
        elif self.total_earned >= 2000000:  # 2M GNF
            return 'platinum'
        elif self.total_earned >= 1000000:  # 1M GNF
            return 'gold'
        elif self.total_earned >= 500000:   # 500K GNF
            return 'silver'
        return 'bronze'
    
    def add_points(self, amount, reason=""):
        """Ajouter des points (1% du montant d'achat)"""
        points = amount * Decimal('0.01')
        self.points_balance += points
        self.total_earned += points
        self.level = self.calculate_level()
        self.save()
        
        LoyaltyTransaction.objects.create(
            user=self.user,
            points=points,
            transaction_type='earned',
            reason=reason
        )

class LoyaltyTransaction(models.Model):
    """Historique des transactions de fidélité"""
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    points = models.DecimalField(max_digits=10, decimal_places=0)
    transaction_type = models.CharField(max_length=20, choices=[
        ('earned', 'Gagné'),
        ('redeemed', 'Utilisé'),
        ('expired', 'Expiré'),
        ('bonus', 'Bonus')
    ])
    reason = models.CharField(max_length=200)
    created_at = models.DateTimeField(auto_now_add=True)

class GuineaReward(models.Model):
    """Récompenses spécifiques à la Guinée"""
    name = models.CharField(max_length=100)
    description = models.TextField()
    points_required = models.DecimalField(max_digits=10, decimal_places=0)
    reward_type = models.CharField(max_length=20, choices=[
        ('discount', 'Réduction'),
        ('free_delivery', 'Livraison gratuite'),
        ('product', 'Produit gratuit'),
        ('cashback', 'Remboursement'),
        ('local_service', 'Service local')  # Spécifique Guinée
    ])
    value = models.DecimalField(max_digits=10, decimal_places=2)
    is_active = models.BooleanField(default=True)
    region_specific = models.ForeignKey('geolocation.GuineaRegion', on_delete=models.CASCADE, null=True, blank=True)