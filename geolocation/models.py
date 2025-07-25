from django.db import models
from django.contrib.auth import get_user_model
from django.utils.translation import gettext_lazy as _
from decimal import Decimal
import math

User = get_user_model()

class GuineaRegion(models.Model):
    """Régions administratives de Guinée"""
    name = models.CharField(max_length=100, verbose_name=_('Nom'))
    code = models.CharField(max_length=10, unique=True, verbose_name=_('Code'))
    is_active = models.BooleanField(default=True, verbose_name=_('Actif'))
    
    class Meta:
        verbose_name = _('Région')
        verbose_name_plural = _('Régions')
        ordering = ['name']
    
    def __str__(self):
        return self.name

class GuineaPrefecture(models.Model):
    """Préfectures de Guinée"""
    region = models.ForeignKey(GuineaRegion, on_delete=models.CASCADE, related_name='prefectures', verbose_name=_('Région'))
    name = models.CharField(max_length=100, verbose_name=_('Nom'))
    code = models.CharField(max_length=10, unique=True, verbose_name=_('Code'))
    is_active = models.BooleanField(default=True, verbose_name=_('Actif'))
    
    class Meta:
        verbose_name = _('Préfecture')
        verbose_name_plural = _('Préfectures')
        ordering = ['name']
    
    def __str__(self):
        return f"{self.name} ({self.region.name})"

class GuineaCommune(models.Model):
    """Communes de Guinée"""
    prefecture = models.ForeignKey(GuineaPrefecture, on_delete=models.CASCADE, related_name='communes', verbose_name=_('Préfecture'))
    name = models.CharField(max_length=100, verbose_name=_('Nom'))
    code = models.CharField(max_length=10, unique=True, verbose_name=_('Code'))
    is_active = models.BooleanField(default=True, verbose_name=_('Actif'))
    
    class Meta:
        verbose_name = _('Commune')
        verbose_name_plural = _('Communes')
        ordering = ['name']
    
    def __str__(self):
        return f"{self.name} ({self.prefecture.name})"

class LocationPoint(models.Model):
    """Points de localisation avec coordonnées GPS"""
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='created_locations', verbose_name=_('Créé par'))
    name = models.CharField(max_length=200, verbose_name=_('Nom du lieu'))
    description = models.TextField(blank=True, verbose_name=_('Description'))
    latitude = models.DecimalField(max_digits=10, decimal_places=8, verbose_name=_('Latitude'))
    longitude = models.DecimalField(max_digits=11, decimal_places=8, verbose_name=_('Longitude'))
    
    # Localisation administrative
    region = models.ForeignKey(GuineaRegion, on_delete=models.SET_NULL, null=True, blank=True, verbose_name=_('Région'))
    prefecture = models.ForeignKey(GuineaPrefecture, on_delete=models.SET_NULL, null=True, blank=True, verbose_name=_('Préfecture'))
    commune = models.ForeignKey(GuineaCommune, on_delete=models.SET_NULL, null=True, blank=True, verbose_name=_('Commune'))
    
    # Informations d'adresse
    address = models.CharField(max_length=255, blank=True, verbose_name=_('Adresse'))
    city = models.CharField(max_length=100, blank=True, verbose_name=_('Ville'))
    postal_code = models.CharField(max_length=20, blank=True, verbose_name=_('Code postal'))
    country = models.CharField(max_length=100, default='Guinée', verbose_name=_('Pays'))
    landmark = models.CharField(max_length=200, blank=True, verbose_name=_('Point de repère'))
    access_instructions = models.TextField(blank=True, verbose_name=_('Instructions d\'accès'))
    
    # Métadonnées
    verified_by_locals = models.BooleanField(default=False, verbose_name=_('Vérifié par les locaux'))
    verification_count = models.IntegerField(default=0, verbose_name=_('Nombre de vérifications'))
    is_active = models.BooleanField(default=True, verbose_name=_('Actif'))
    created_at = models.DateTimeField(auto_now_add=True, verbose_name=_('Créé le'))
    updated_at = models.DateTimeField(auto_now=True, verbose_name=_('Mis à jour le'))
    
    class Meta:
        verbose_name = _('Point de localisation')
        verbose_name_plural = _('Points de localisation')
        ordering = ['-created_at']
    
    def __str__(self):
        return self.name
    
    @property
    def google_maps_url(self):
        return f"https://www.google.com/maps?q={self.latitude},{self.longitude}"
    
    @property
    def full_address(self):
        parts = []
        if self.address:
            parts.append(self.address)
        if self.city:
            parts.append(self.city)
        if self.commune:
            parts.append(self.commune.name)
        if self.prefecture:
            parts.append(self.prefecture.name)
        if self.region:
            parts.append(self.region.name)
        return ", ".join(parts) or "Adresse non définie"
    
    def calculate_distance_to(self, other_location):
        """Calcule la distance vers un autre point en km"""
        if not other_location:
            return None
        
        lat1, lon1 = float(self.latitude), float(self.longitude)
        lat2, lon2 = float(other_location.latitude), float(other_location.longitude)
        
        # Formule de Haversine
        R = 6371  # Rayon de la Terre en km
        
        lat1_rad = math.radians(lat1)
        lat2_rad = math.radians(lat2)
        delta_lat = math.radians(lat2 - lat1)
        delta_lon = math.radians(lon2 - lon1)
        
        a = (math.sin(delta_lat / 2) ** 2 + 
             math.cos(lat1_rad) * math.cos(lat2_rad) * 
             math.sin(delta_lon / 2) ** 2)
        c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
        
        return R * c

class UserLocation(models.Model):
    """Localisation des utilisateurs"""
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='locations', verbose_name=_('Utilisateur'))
    location_point = models.ForeignKey(LocationPoint, on_delete=models.CASCADE, related_name='user_locations', verbose_name=_('Point de localisation'))
    is_primary = models.BooleanField(default=False, verbose_name=_('Adresse principale'))
    label = models.CharField(max_length=50, blank=True, verbose_name=_('Libellé'))
    created_at = models.DateTimeField(auto_now_add=True, verbose_name=_('Créé le'))
    
    class Meta:
        verbose_name = _('Localisation utilisateur')
        verbose_name_plural = _('Localisations utilisateurs')
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.user.username} - {self.location_point.name}"
    
    def save(self, *args, **kwargs):
        if self.is_primary:
            UserLocation.objects.filter(user=self.user, is_primary=True).exclude(id=self.id).update(is_primary=False)
        super().save(*args, **kwargs)

class DeliveryZone(models.Model):
    """Zones de livraison avec tarification"""
    name = models.CharField(max_length=100, verbose_name=_('Nom de la zone'))
    regions = models.ManyToManyField(GuineaRegion, blank=True, related_name='delivery_zones', verbose_name=_('Régions'))
    prefectures = models.ManyToManyField(GuineaPrefecture, blank=True, related_name='delivery_zones', verbose_name=_('Préfectures'))
    communes = models.ManyToManyField(GuineaCommune, blank=True, related_name='delivery_zones', verbose_name=_('Communes'))
    base_delivery_cost = models.DecimalField(max_digits=10, decimal_places=2, verbose_name=_('Coût de base (GNF)'))
    cost_per_km = models.DecimalField(max_digits=5, decimal_places=2, default=1000, verbose_name=_('Coût par km (GNF)'))
    estimated_delivery_time = models.CharField(max_length=50, default="24-48h", verbose_name=_('Délai estimé'))
    is_active = models.BooleanField(default=True, verbose_name=_('Actif'))
    
    class Meta:
        verbose_name = _('Zone de livraison')
        verbose_name_plural = _('Zones de livraison')
        ordering = ['name']
    
    def __str__(self):
        return self.name
    
    def calculate_delivery_cost(self, distance_km):
        """Calcule le coût de livraison pour cette zone"""
        if distance_km <= 0:
            return self.base_delivery_cost
        
        total_cost = float(self.base_delivery_cost) + (distance_km * float(self.cost_per_km))
        return Decimal(str(round(total_cost, 2)))

class LocationVerification(models.Model):
    """Vérifications de localisation par la communauté"""
    location_point = models.ForeignKey(LocationPoint, on_delete=models.CASCADE, related_name='verifications', verbose_name=_('Point de localisation'))
    verified_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='location_verifications', verbose_name=_('Vérifié par'))
    is_accurate = models.BooleanField(verbose_name=_('Localisation exacte'))
    suggested_correction = models.TextField(blank=True, verbose_name=_('Correction suggérée'))
    local_description = models.TextField(blank=True, verbose_name=_('Description locale'))
    created_at = models.DateTimeField(auto_now_add=True, verbose_name=_('Créé le'))
    
    class Meta:
        verbose_name = _('Vérification de localisation')
        verbose_name_plural = _('Vérifications de localisation')
        unique_together = ['location_point', 'verified_by']
        ordering = ['-created_at']
    
    def __str__(self):
        return f"Vérification de {self.location_point.name} par {self.verified_by.username}"