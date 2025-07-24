from django.contrib.auth.models import AbstractUser
from django.db import models
from django.utils.translation import gettext_lazy as _
import uuid
import random
import string
from decimal import Decimal
from django.utils import timezone
from datetime import timedelta
from decimal import Decimal
from django.utils import timezone
from datetime import timedelta

class User(AbstractUser):
    USER_TYPE_CHOICES = [
        ('buyer', _('Acheteur')),
        ('seller', _('Vendeur')),
        ('delivery', _('Livreur')),
        ('admin', _('Admin')),
        ('superadmin', _('Super Admin')),
        ('support', _('Support')),
    ]
    
    SUBSCRIPTION_CHOICES = [
        ('free', _('Gratuit')),
        ('premium', _('Premium')),
        ('business', _('Business')),
        ('enterprise', _('Enterprise')),
    ]
    
    SUBSCRIPTION_CHOICES = [
        ('free', _('Gratuit')),
        ('premium', _('Premium')),
        ('business', _('Business')),
        ('enterprise', _('Enterprise')),
    ]
    
    user_type = models.CharField(
        max_length=20,
        choices=USER_TYPE_CHOICES,
        default='buyer',
        verbose_name=_('Type d\'utilisateur')
    )
    subscription_type = models.CharField(
        max_length=20,
        choices=SUBSCRIPTION_CHOICES,
        default='free',
        verbose_name=_('Type d\'abonnement')
    )
    subscription_expires_at = models.DateTimeField(null=True, blank=True, verbose_name=_('Abonnement expire le'))
    subscription_auto_renew = models.BooleanField(default=False, verbose_name=_('Renouvellement automatique'))
    subscription_type = models.CharField(
        max_length=20,
        choices=SUBSCRIPTION_CHOICES,
        default='free',
        verbose_name=_('Type d\'abonnement')
    )
    subscription_expires_at = models.DateTimeField(null=True, blank=True, verbose_name=_('Abonnement expire le'))
    subscription_auto_renew = models.BooleanField(default=False, verbose_name=_('Renouvellement automatique'))
    phone = models.CharField(max_length=20, blank=True, verbose_name=_('Téléphone'))
    address = models.TextField(blank=True, verbose_name=_('Adresse'))
    city = models.CharField(max_length=100, blank=True, verbose_name=_('Ville'))
    postal_code = models.CharField(max_length=10, blank=True, verbose_name=_('Code postal'))
    country = models.CharField(max_length=100, blank=True, verbose_name=_('Pays'))
    avatar = models.ImageField(upload_to='avatars/', blank=True, verbose_name=_('Avatar'))
    birth_date = models.DateField(blank=True, null=True, verbose_name=_('Date de naissance'))
    is_verified = models.BooleanField(default=False, verbose_name=_('Vérifié'))
    two_factor_enabled = models.BooleanField(default=False, verbose_name=_('2FA activé'))
    two_factor_secret = models.CharField(max_length=32, blank=True)
    two_factor_enabled = models.BooleanField(default=False, verbose_name=_('2FA activé'))
    two_factor_secret = models.CharField(max_length=32, blank=True)
    created_at = models.DateTimeField(auto_now_add=True, verbose_name=_('Créé le'))
    updated_at = models.DateTimeField(auto_now=True, verbose_name=_('Mis à jour le'))
    
    verification_code = models.CharField(max_length=6, blank=True)
    email_verified = models.BooleanField(default=False)
    phone_verified = models.BooleanField(default=False)
    
    class Meta:
        verbose_name = _('Utilisateur')
        verbose_name_plural = _('Utilisateurs')
    
    def __str__(self):
        return f"{self.username} ({self.get_user_type_display()})"
    
    @property
    def is_premium(self):
        return self.subscription_type in ['premium', 'business', 'enterprise']
    
    @property
    def is_subscription_active(self):
        if self.subscription_type == 'free':
            return True
        return self.subscription_expires_at and self.subscription_expires_at > timezone.now()
    
    def get_subscription_limits(self):
        """Retourne les limites selon le type d'abonnement"""
        limits = {
            'free': {
                'max_products': 10,
                'max_images_per_product': 3,
                'max_categories': 3,
                'analytics_retention_days': 30,
                'can_use_ai_recommendations': False,
                'can_create_flash_sales': False,
                'can_create_auctions': False,
                'max_delivery_zones': 1,
                'commission_rate': 0.05,  # 5%
            },
            'premium': {
                'max_products': 100,
                'max_images_per_product': 10,
                'max_categories': 10,
                'analytics_retention_days': 365,
                'can_use_ai_recommendations': True,
                'can_create_flash_sales': True,
                'can_create_auctions': False,
                'max_delivery_zones': 5,
                'commission_rate': 0.03,  # 3%
            },
            'business': {
                'max_products': 1000,
                'max_images_per_product': 20,
                'max_categories': -1,  # Illimité
                'analytics_retention_days': 730,
                'can_use_ai_recommendations': True,
                'can_create_flash_sales': True,
                'can_create_auctions': True,
                'max_delivery_zones': 20,
                'commission_rate': 0.02,  # 2%
            },
            'enterprise': {
                'max_products': -1,  # Illimité
                'max_images_per_product': -1,
                'max_categories': -1,
                'analytics_retention_days': -1,
                'can_use_ai_recommendations': True,
                'can_create_flash_sales': True,
                'can_create_auctions': True,
                'max_delivery_zones': -1,
                'commission_rate': 0.01,  # 1%
            }
        }
        return limits.get(self.subscription_type, limits['free'])
    
    @property
    def is_premium(self):
        return self.subscription_type in ['premium', 'business', 'enterprise']
    
    @property
    def is_subscription_active(self):
        if self.subscription_type == 'free':
            return True
        return self.subscription_expires_at and self.subscription_expires_at > timezone.now()
    
    def get_subscription_limits(self):
        """Retourne les limites selon le type d'abonnement"""
        limits = {
            'free': {
                'max_products': 10,
                'max_images_per_product': 3,
                'max_categories': 3,
                'analytics_retention_days': 30,
                'can_use_ai_recommendations': False,
                'can_create_flash_sales': False,
                'can_create_auctions': False,
                'max_delivery_zones': 1,
                'commission_rate': 0.05,  # 5%
            },
            'premium': {
                'max_products': 100,
                'max_images_per_product': 10,
                'max_categories': 10,
                'analytics_retention_days': 365,
                'can_use_ai_recommendations': True,
                'can_create_flash_sales': True,
                'can_create_auctions': False,
                'max_delivery_zones': 5,
                'commission_rate': 0.03,  # 3%
            },
            'business': {
                'max_products': 1000,
                'max_images_per_product': 20,
                'max_categories': -1,  # Illimité
                'analytics_retention_days': 730,
                'can_use_ai_recommendations': True,
                'can_create_flash_sales': True,
                'can_create_auctions': True,
                'max_delivery_zones': 20,
                'commission_rate': 0.02,  # 2%
            },
            'enterprise': {
                'max_products': -1,  # Illimité
                'max_images_per_product': -1,
                'max_categories': -1,
                'analytics_retention_days': -1,
                'can_use_ai_recommendations': True,
                'can_create_flash_sales': True,
                'can_create_auctions': True,
                'max_delivery_zones': -1,
                'commission_rate': 0.01,  # 1%
            }
        }
        return limits.get(self.subscription_type, limits['free'])
    
    @property
    def is_buyer(self):
        return self.user_type == 'buyer'
    
    @property
    def is_seller(self):
        return self.user_type == 'seller'
    
    @property
    def is_delivery(self):
        return self.user_type == 'delivery'
    
    @property
    def is_admin(self):
        return self.user_type == 'admin'
    
    @property
    def is_superadmin(self):
        return self.user_type == 'superadmin'
    
    @property
    def full_address(self):
        return f"{self.address}, {self.city} {self.postal_code}, {self.country}".strip(", ")
    
    def generate_verification_code(self):
        self.verification_code = ''.join(random.choices(string.digits, k=6))
        self.save()
        return self.verification_code

class SellerProfile(models.Model):
    VERIFICATION_STATUS_CHOICES = [
        ('pending', _('En attente')),
        ('approved', _('Approuvé')),
        ('rejected', _('Rejeté')),
        ('suspended', _('Suspendu')),
    ]
    
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='seller_profile')
    company_name = models.CharField(max_length=200, verbose_name=_('Nom de l\'entreprise'))
    company_description = models.TextField(blank=True, verbose_name=_('Description'))
    logo = models.ImageField(upload_to='seller_logos/', blank=True, verbose_name=_('Logo'))
    website = models.URLField(blank=True, verbose_name=_('Site web'))
    tax_number = models.CharField(max_length=50, blank=True, verbose_name=_('Numéro de TVA'))
    bank_account = models.CharField(max_length=100, blank=True, verbose_name=_('Compte bancaire'))
    
    identity_document = models.FileField(upload_to='seller_docs/', verbose_name=_('Pièce d\'identité'))
    rccm_document = models.FileField(upload_to='seller_docs/', verbose_name=_('RCCM'))
    business_license = models.FileField(upload_to='seller_docs/', blank=True, verbose_name=_('Licence commerciale'))
    
    verification_status = models.CharField(max_length=20, choices=VERIFICATION_STATUS_CHOICES, default='pending')
    verification_notes = models.TextField(blank=True, verbose_name=_('Notes de vérification'))
    verified_at = models.DateTimeField(null=True, blank=True)
    verified_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='verified_sellers')
    
    accepts_cash_on_delivery = models.BooleanField(default=True, verbose_name=_('Accepte le paiement à la livraison'))
    accepts_store_pickup = models.BooleanField(default=False, verbose_name=_('Accepte le retrait en boutique'))
    
    rating = models.DecimalField(max_digits=3, decimal_places=2, default=0.00, verbose_name=_('Note'))
    total_sales = models.DecimalField(max_digits=10, decimal_places=2, default=0.00, verbose_name=_('Ventes totales'))
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = _('Profil vendeur')
        verbose_name_plural = _('Profils vendeurs')
    
    def __str__(self):
        return f"{self.company_name} - {self.user.username}"
    
    @property
    def is_verified(self):
        return self.verification_status == 'approved'
    
    @property
    def can_sell(self):
        return self.verification_status in ['approved']

class SellerDeliveryZone(models.Model):
    seller = models.ForeignKey(User, on_delete=models.CASCADE, related_name='delivery_zones', limit_choices_to={'user_type': 'seller'})
    delivery_zone = models.ForeignKey('geolocation.DeliveryZone', on_delete=models.CASCADE, related_name='seller_zones')
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = _('Zone de livraison du vendeur')
        verbose_name_plural = _('Zones de livraison des vendeurs')
        unique_together = ['seller', 'delivery_zone']
    
    def __str__(self):
        return f"{self.seller.username} - {self.delivery_zone.name}"

class DeliveryProfile(models.Model):
    VERIFICATION_STATUS_CHOICES = [
        ('pending', _('En attente')),
        ('approved', _('Approuvé')),
        ('rejected', _('Rejeté')),
        ('suspended', _('Suspendu')),
    ]
    
    VEHICLE_CHOICES = [
        ('bike', _('Vélo')),
        ('scooter', _('Scooter')),
        ('motorcycle', _('Moto')),
        ('car', _('Voiture')),
        ('van', _('Camionnette')),
        ('truck', _('Camion')),
    ]
    
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='delivery_profile')
    vehicle_type = models.CharField(max_length=20, choices=VEHICLE_CHOICES, verbose_name=_('Type de véhicule'))
    license_plate = models.CharField(max_length=20, blank=True, verbose_name=_('Plaque d\'immatriculation'))
    license_number = models.CharField(max_length=50, blank=True, verbose_name=_('Numéro de permis'))
    
    license_document = models.FileField(upload_to='delivery_docs/', verbose_name=_('Permis de conduire'))
    vehicle_registration = models.FileField(upload_to='delivery_docs/', blank=True, verbose_name=_('Carte grise'))
    insurance_document = models.FileField(upload_to='delivery_docs/', blank=True, verbose_name=_('Assurance'))
    
    verification_status = models.CharField(max_length=20, choices=VERIFICATION_STATUS_CHOICES, default='pending')
    verification_notes = models.TextField(blank=True, verbose_name=_('Notes de vérification'))
    verified_at = models.DateTimeField(null=True, blank=True)
    verified_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='verified_deliverers')
    
    availability_radius = models.IntegerField(default=10, verbose_name=_('Rayon de disponibilité (km)'))
    is_available = models.BooleanField(default=True, verbose_name=_('Disponible'))
    rating = models.DecimalField(max_digits=3, decimal_places=2, default=0.00, verbose_name=_('Note'))
    total_deliveries = models.IntegerField(default=0, verbose_name=_('Livraisons totales'))
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = _('Profil livreur')
        verbose_name_plural = _('Profils livreurs')
    
    def __str__(self):
        return f"{self.user.username} - {self.get_vehicle_type_display()}"
    
    @property
    def is_verified(self):
        return self.verification_status == 'approved'
    
    @property
    def can_deliver(self):
        return self.verification_status in ['approved'] and self.is_available