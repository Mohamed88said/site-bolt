from django.db import models
from django.contrib.auth import get_user_model
from django.utils.translation import gettext_lazy as _
from django.utils import timezone
from decimal import Decimal
import uuid

User = get_user_model()

class SubscriptionPlan(models.Model):
    """Plans d'abonnement"""
    name = models.CharField(max_length=50, verbose_name=_('Nom'))
    slug = models.SlugField(unique=True)
    description = models.TextField(verbose_name=_('Description'))
    price_monthly_gnf = models.DecimalField(max_digits=12, decimal_places=0, verbose_name=_('Prix mensuel (GNF)'))
    price_yearly_gnf = models.DecimalField(max_digits=12, decimal_places=0, verbose_name=_('Prix annuel (GNF)'))
    max_products = models.IntegerField(default=10, verbose_name=_('Produits max'))
    max_images_per_product = models.IntegerField(default=3, verbose_name=_('Images max par produit'))
    max_categories = models.IntegerField(default=3, verbose_name=_('Catégories max'))
    analytics_retention_days = models.IntegerField(default=30, verbose_name=_('Rétention analytics (jours)'))
    can_use_ai_recommendations = models.BooleanField(default=False, verbose_name=_('Recommandations IA'))
    can_create_flash_sales = models.BooleanField(default=False, verbose_name=_('Ventes flash'))
    can_create_auctions = models.BooleanField(default=False, verbose_name=_('Enchères'))
    can_create_groups = models.BooleanField(default=False, verbose_name=_('Groupes d\'achat'))
    max_delivery_zones = models.IntegerField(default=1, verbose_name=_('Zones de livraison max'))
    commission_rate = models.DecimalField(max_digits=5, decimal_places=4, default=0.05, verbose_name=_('Taux de commission'))
    priority_support = models.BooleanField(default=False, verbose_name=_('Support prioritaire'))
    advanced_analytics = models.BooleanField(default=False, verbose_name=_('Analytics avancées'))
    bulk_operations = models.BooleanField(default=False, verbose_name=_('Opérations en lot'))
    api_access = models.BooleanField(default=False, verbose_name=_('Accès API'))
    white_label = models.BooleanField(default=False, verbose_name=_('Marque blanche'))
    is_active = models.BooleanField(default=True, verbose_name=_('Actif'))
    sort_order = models.IntegerField(default=0, verbose_name=_('Ordre d\'affichage'))
    
    class Meta:
        verbose_name = _('Plan d\'abonnement')
        verbose_name_plural = _('Plans d\'abonnement')
        ordering = ['sort_order', 'price_monthly_gnf']
    
    def __str__(self):
        return self.name
    
    @property
    def yearly_savings_gnf(self):
        """Économies annuelles par rapport au paiement mensuel"""
        monthly_yearly = self.price_monthly_gnf * 12
        return monthly_yearly - self.price_yearly_gnf

class Subscription(models.Model):
    """Abonnements actifs"""
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='subscription')
    plan = models.ForeignKey(SubscriptionPlan, on_delete=models.CASCADE)
    status = models.CharField(max_length=20, choices=[
        ('active', _('Actif')),
        ('cancelled', _('Annulé')),
        ('expired', _('Expiré')),
        ('suspended', _('Suspendu'))
    ], default='active', verbose_name=_('Statut'))
    billing_cycle = models.CharField(max_length=20, choices=[
        ('monthly', _('Mensuel')),
        ('yearly', _('Annuel'))
    ], default='monthly', verbose_name=_('Cycle de facturation'))
    started_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField(verbose_name=_('Expire le'))
    auto_renew = models.BooleanField(default=True, verbose_name=_('Renouvellement automatique'))
    stripe_subscription_id = models.CharField(max_length=200, blank=True)
    last_payment_date = models.DateTimeField(null=True, blank=True)
    next_payment_date = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        verbose_name = _('Abonnement')
        verbose_name_plural = _('Abonnements')
    
    def __str__(self):
        return f"{self.user.username} - {self.plan.name}"
    
    @property
    def is_active(self):
        return self.status == 'active' and self.expires_at > timezone.now()
    
    @property
    def days_remaining(self):
        if self.expires_at > timezone.now():
            return (self.expires_at - timezone.now()).days
        return 0

class SubscriptionPayment(models.Model):
    """Paiements d'abonnement"""
    subscription = models.ForeignKey(Subscription, on_delete=models.CASCADE, related_name='payments')
    amount_gnf = models.DecimalField(max_digits=12, decimal_places=0, verbose_name=_('Montant (GNF)'))
    payment_method = models.CharField(max_length=50, verbose_name=_('Méthode de paiement'))
    stripe_payment_intent_id = models.CharField(max_length=200, blank=True)
    mobile_money_transaction_id = models.CharField(max_length=200, blank=True)
    status = models.CharField(max_length=20, choices=[
        ('pending', _('En attente')),
        ('completed', _('Terminé')),
        ('failed', _('Échoué')),
        ('refunded', _('Remboursé'))
    ], default='pending')
    created_at = models.DateTimeField(auto_now_add=True)
    processed_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        verbose_name = _('Paiement abonnement')
        verbose_name_plural = _('Paiements abonnements')