from django.db import models
from django.contrib.auth import get_user_model
from django.utils.translation import gettext_lazy as _
from orders.models import Order
from geolocation.models import LocationPoint, DeliveryZone
import uuid
import math

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
                                     related_name='deliveries', verbose_name=_('Point de localisation'))
    delivery_zone = models.ForeignKey(DeliveryZone, on_delete=models.SET_NULL, null=True, blank=True,
                                    related_name='deliveries', verbose_name=_('Zone de livraison'))
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    tracking_number = models.CharField(max_length=100, unique=True, blank=True)
    delivery_cost = models.DecimalField(max_digits=10, decimal_places=2, default=15000)  # 15,000 GNF
    paid_by = models.CharField(max_length=20, choices=PAID_BY_CHOICES, default='buyer', verbose_name=_('Payé par'))
    estimated_delivery_time = models.DateTimeField(null=True, blank=True)
    actual_delivery_time = models.DateTimeField(null=True, blank=True)
    delivery_notes = models.TextField(blank=True)
    
    # Informations du vendeur pour la collecte
    seller_address = models.TextField(blank=True, verbose_name=_('Adresse du vendeur'))
    seller_phone = models.CharField(max_length=20, blank=True, verbose_name=_('Téléphone du vendeur'))
    seller_instructions = models.TextField(blank=True, verbose_name=_('Instructions pour la collecte'))
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = _('Livraison')
        verbose_name_plural = _('Livraisons')
        ordering = ['-created_at']
    
    def __str__(self):
        return f"Livraison {self.tracking_number} - {self.order}"
    
    def save(self, *args, **kwargs):
        if not self.tracking_number:
            self.tracking_number = f"LIV{str(uuid.uuid4())[:8].upper()}"
        
        # Récupérer les informations du vendeur
        if self.order and self.order.items.exists():
            seller = self.order.items.first().product.seller
            if not self.seller_address:
                self.seller_address = seller.address or "Adresse non renseignée"
            if not self.seller_phone:
                self.seller_phone = seller.phone or "Téléphone non renseigné"
        
        super().save(*args, **kwargs)
    
    def calculate_distance_to_seller(self):
        """Calcule la distance entre le point de livraison et le vendeur"""
        if not self.location_point:
            return None
        
        # Obtenir le vendeur principal (premier produit)
        seller = self.order.items.first().product.seller if self.order.items.exists() else None
        if not seller:
            return None
        
        # Coordonnées du vendeur (par défaut Conakry si pas défini)
        seller_lat = 9.6412  # Conakry par défaut
        seller_lng = -13.5784
        
        # Coordonnées de livraison
        delivery_lat = float(self.location_point.latitude)
        delivery_lng = float(self.location_point.longitude)
        
        # Calcul de distance (formule Haversine)
        R = 6371  # Rayon de la Terre en km
        
        lat1_rad = math.radians(seller_lat)
        lat2_rad = math.radians(delivery_lat)
        delta_lat = math.radians(delivery_lat - seller_lat)
        delta_lng = math.radians(delivery_lng - seller_lng)
        
        a = (math.sin(delta_lat / 2) ** 2 + 
             math.cos(lat1_rad) * math.cos(lat2_rad) * 
             math.sin(delta_lng / 2) ** 2)
        c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
        
        return R * c
    
    def calculate_delivery_cost(self):
        """Calcule le coût de livraison basé sur la distance"""
        distance = self.calculate_distance_to_seller()
        if not distance:
            return 15000  # Coût par défaut
        
        # Coût de base + distance
        base_cost = 15000  # 15,000 GNF
        cost_per_km = 1000  # 1,000 GNF par km
        
        total_cost = base_cost + (distance * cost_per_km)
        return min(total_cost, 100000)  # Maximum 100,000 GNF

class DeliveryRequest(models.Model):
    delivery = models.ForeignKey(Delivery, on_delete=models.CASCADE, related_name='requests')
    delivery_person = models.ForeignKey(User, on_delete=models.CASCADE, related_name='delivery_requests',
                                      limit_choices_to={'user_type': 'delivery'})
    message = models.TextField(blank=True, verbose_name=_('Message'))
    proposed_cost = models.DecimalField(max_digits=10, decimal_places=2, default=15000, verbose_name=_('Coût proposé'))
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

class DeliveryPerson(models.Model):
    AVAILABILITY_CHOICES = [
        ('available', _('Disponible')),
        ('unavailable', _('Indisponible')),
    ]
    
    VEHICLE_CHOICES = [
        ('bike', _('Vélo')),
        ('car', _('Voiture')),
        ('van', _('Camionnette')),
        ('other', _('Autre')),
    ]
    
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='delivery_person_profile',
                              limit_choices_to={'user_type': 'delivery'}, verbose_name=_('Utilisateur'))
    phone_number = models.CharField(max_length=20, verbose_name=_('Numéro de téléphone'))
    vehicle_type = models.CharField(max_length=20, choices=VEHICLE_CHOICES, blank=True, verbose_name=_('Type de véhicule'))
    location_point = models.ForeignKey(LocationPoint, on_delete=models.SET_NULL, null=True, blank=True,
                                     related_name='delivery_persons', verbose_name=_('Position actuelle'))
    availability_status = models.CharField(max_length=20, choices=AVAILABILITY_CHOICES, default='available',
                                         verbose_name=_('Statut de disponibilité'))
    created_at = models.DateTimeField(auto_now_add=True, verbose_name=_('Créé le'))
    updated_at = models.DateTimeField(auto_now=True, verbose_name=_('Mis à jour le'))
    
    class Meta:
        verbose_name = _('Livreur')
        verbose_name_plural = _('Livreurs')
    
    def __str__(self):
        return f"{self.user.username} - {self.get_vehicle_type_display()}"
    
    @property
    def is_available(self):
        return self.availability_status == 'available'
    
    def calculate_distance_to(self, location_point):
        """Calcule la distance vers un point de livraison"""
        if not self.location_point or not location_point:
            return None
        
        return self.location_point.calculate_distance_to(location_point)