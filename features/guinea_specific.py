"""
FONCTIONNALITÉS SPÉCIFIQUES À LA GUINÉE
- Support des langues locales
- Intégration des fêtes et événements
- Produits saisonniers
"""

from django.db import models
from django.contrib.auth import get_user_model

User = get_user_model()

class GuineaLanguage(models.Model):
    """Langues parlées en Guinée"""
    name = models.CharField(max_length=50)
    code = models.CharField(max_length=5, unique=True)
    is_official = models.BooleanField(default=False)
    region = models.ForeignKey('geolocation.GuineaRegion', on_delete=models.CASCADE, null=True, blank=True)
    
    # Français, Pular, Malinké, Soussou, Kissi, Toma, etc.

class GuineaEvent(models.Model):
    """Événements et fêtes guinéennes"""
    name = models.CharField(max_length=100)
    date = models.DateField()
    is_national = models.BooleanField(default=True)
    region = models.ForeignKey('geolocation.GuineaRegion', on_delete=models.CASCADE, null=True, blank=True)
    description = models.TextField()
    
    # Ramadan, Tabaski, Indépendance, etc.

class SeasonalProduct(models.Model):
    """Produits saisonniers guinéens"""
    product = models.ForeignKey('products.Product', on_delete=models.CASCADE)
    season = models.CharField(max_length=20, choices=[
        ('dry', 'Saison sèche'),
        ('rainy', 'Saison des pluies'),
        ('harvest', 'Récolte'),
        ('ramadan', 'Ramadan'),
        ('tabaski', 'Tabaski')
    ])
    start_date = models.DateField()
    end_date = models.DateField()
    seasonal_price = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)

class LocalCurrency(models.Model):
    """Gestion des devises locales"""
    currency_code = models.CharField(max_length=3, default='GNF')
    exchange_rate_to_eur = models.DecimalField(max_digits=10, decimal_places=4)
    last_updated = models.DateTimeField(auto_now=True)
    
    @classmethod
    def convert_to_gnf(cls, eur_amount):
        """Convertir EUR vers GNF"""
        rate = cls.objects.first()
        if rate:
            return eur_amount * rate.exchange_rate_to_eur
        return eur_amount * 11000  # Taux approximatif

class GuineaPaymentMethod(models.Model):
    """Méthodes de paiement spécifiques à la Guinée"""
    name = models.CharField(max_length=50)
    provider = models.CharField(max_length=50)
    is_mobile_money = models.BooleanField(default=False)
    phone_prefix = models.CharField(max_length=10, blank=True)  # +224, etc.
    is_active = models.BooleanField(default=True)
    regions = models.ManyToManyField('geolocation.GuineaRegion', blank=True)
    
    # Orange Money (+224 6XX), MTN Money (+224 7XX), etc.