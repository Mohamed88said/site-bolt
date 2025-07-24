from django.db import models
from django.contrib.auth import get_user_model
from django.utils.translation import gettext_lazy as _
from orders.models import Order
from geolocation.models import LocationPoint, DeliveryZone
from datetime import timedelta
import requests
import uuid
from django.core.cache import cache
from geolocation.distance_calculator import DistanceCalculator

User = get_user_model()

class DeliveryPerson(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='delivery_person_profile', 
                               limit_choices_to={'user_type': 'delivery'}, verbose_name=_('Utilisateur'))
    phone_number = models.CharField(max_length=20, verbose_name=_('Numéro de téléphone'))
    location_point = models.ForeignKey(LocationPoint, on_delete=models.SET_NULL, null=True, blank=True,
                                     related_name='delivery_persons', verbose_name=_('Position actuelle'))
    availability_status = models.CharField(max_length=20, choices=[
        ('available', _('Disponible')),
        ('unavailable', _('Indisponible')),
    ], default='available', verbose_name=_('Statut de disponibilité'))
    vehicle_type = models.CharField(max_length=20, choices=[
        ('bike', _('Vélo')),
        ('car', _('Voiture')),
        ('van', _('Camionnette')),
        ('other', _('Autre')),
    ], blank=True, verbose_name=_('Type de véhicule'))
    created_at = models.DateTimeField(auto_now_add=True, verbose_name=_('Créé le'))
    updated_at = models.DateTimeField(auto_now=True, verbose_name=_('Mis à jour le'))
    
    class Meta:
        verbose_name = _('Livreur')
        verbose_name_plural = _('Livreurs')
    
    def __str__(self):
        return f"{self.user.username} - {self.get_availability_status_display()}"

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
    estimated_delivery_time = models.DateTimeField(null=True, blank=True)
    actual_delivery_time = models.DateTimeField(null=True, blank=True)
    delivery_notes = models.TextField(blank=True)
    tracking_number = models.CharField(max_length=100, unique=True, blank=True)
    delivery_cost = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    paid_by = models.CharField(max_length=20, choices=PAID_BY_CHOICES, default='buyer', verbose_name=_('Payé par'))
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = _('Livraison')
        verbose_name_plural = _('Livraisons')
        ordering = ['-created_at']
    
    def __str__(self):
        return f"Livraison {self.tracking_number or self.id} - {self.order}"
    
    def save(self, *args, **kwargs):
        if not self.tracking_number:
            self.tracking_number = str(uuid.uuid4())[:8].upper()
        
        if self.location_point and not self.delivery_zone:
            self.delivery_zone = self._get_delivery_zone()
        
        if self.delivery_zone and not self.estimated_delivery_time:
            from django.utils import timezone
            self.estimated_delivery_time = timezone.now() + timedelta(days=self.delivery_zone.estimated_delivery_days)
        
        if self.location_point and self.delivery_zone and self.status == 'pending':
            self.delivery_cost = self._calculate_delivery_cost()
        
        super().save(*args, **kwargs)
    
    def _get_delivery_zone(self):
        if self.location_point:
            zones = DeliveryZone.objects.filter(
                models.Q(communes=self.location_point.commune) |
                models.Q(prefectures=self.location_point.prefecture) |
                models.Q(regions=self.location_point.region),
                is_active=True
            ).order_by('communes__isnull', 'prefectures__isnull', 'regions__isnull')
            return zones.first() if zones.exists() else None
        return None
    
    def _calculate_delivery_cost(self):
        if not self.location_point or not self.delivery_zone:
            return self.delivery_cost
        
        # Obtenir les coordonnées du vendeur
        seller = self.order.items.first().product.seller if self.order.items.exists() else None
        if seller and hasattr(seller, 'seller_profile'):
            # Essayer d'obtenir la localisation du vendeur
            seller_location = getattr(seller.seller_profile, 'location_point', None)
            if seller_location:
                start_coords = (float(seller_location.latitude), float(seller_location.longitude))
            else:
                # Fallback: géocoder l'adresse du vendeur
                if seller.address and seller.city:
                    start_coords = LocationPoint.geocode_address(seller.address, seller.city, seller.country or 'Guinée')
                else:
                    start_coords = (9.6412, -13.5784)  # Conakry par défaut
        else:
            start_coords = (9.6412, -13.5784)  # Conakry par défaut
            
        end_coords = (self.location_point.latitude, self.location_point.longitude)
        
        try:
            distance_info = DistanceCalculator.get_best_distance(
                start_coords[0], start_coords[1],
                float(end_coords[0]), float(end_coords[1])
            )
            
            if distance_info['success']:
                distance_km = distance_info['distance_km']
                cost = self.delivery_zone.calculate_delivery_cost(distance_km)
                return cost if cost else self.delivery_zone.base_delivery_cost
            else:
                return self.delivery_zone.base_delivery_cost
        except Exception as e:
            print(f"Erreur calcul distance: {e}")
            return self.delivery_zone.base_delivery_cost
    
    def get_distance_info(self):
        """Obtient les informations de distance pour cette livraison"""
        if not self.location_point:
            return None
        
        seller = self.order.items.first().product.seller if self.order.items.exists() else None
        if not seller:
            return None
        
        # Coordonnées du vendeur
        seller_location = getattr(seller.seller_profile, 'location_point', None) if hasattr(seller, 'seller_profile') else None
        if seller_location:
            start_coords = (float(seller_location.latitude), float(seller_location.longitude))
        else:
            if seller.address and seller.city:
                start_coords = LocationPoint.geocode_address(seller.address, seller.city, seller.country or 'Guinée')
            else:
                start_coords = (9.6412, -13.5784)
        
        end_coords = (float(self.location_point.latitude), float(self.location_point.longitude))
        
        return DistanceCalculator.get_best_distance(
            start_coords[0], start_coords[1],
            end_coords[0], end_coords[1]
        )

class DeliveryRequest(models.Model):
    delivery = models.ForeignKey(Delivery, on_delete=models.CASCADE, related_name='requests')
    delivery_person = models.ForeignKey(User, on_delete=models.CASCADE, related_name='delivery_requests',
                                      limit_choices_to={'user_type': 'delivery'})
    message = models.TextField(blank=True)
    proposed_cost = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
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
    




# Ajouter à deliveries/models.py
class DeliveryNegotiation(models.Model):
    delivery = models.ForeignKey(Delivery, on_delete=models.CASCADE, related_name='negotiations')
    seller = models.ForeignKey(User, on_delete=models.CASCADE, related_name='delivery_negotiations_seller')
    delivery_person = models.ForeignKey(User, on_delete=models.CASCADE, related_name='delivery_negotiations_person')
    proposed_price = models.DecimalField(max_digits=10, decimal_places=2)
    status = models.CharField(max_length=20, choices=[
        ('pending', 'En attente'),
        ('accepted', 'Accepté'),
        ('rejected', 'Rejeté')
    ], default='pending')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Négociation de livraison'
        verbose_name_plural = 'Négociations de livraison'

    def __str__(self):
        return f"Négociation {self.id} pour livraison {self.delivery.id}"