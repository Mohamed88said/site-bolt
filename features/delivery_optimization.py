"""
OPTIMISATION DES LIVRAISONS
- Routage intelligent
- Livraisons groupées
- Prédiction des délais
"""

from django.db import models
from django.contrib.auth import get_user_model
from geolocation.distance_calculator import DistanceCalculator

User = get_user_model()

class DeliveryRoute(models.Model):
    """Routes de livraison optimisées"""
    delivery_person = models.ForeignKey(User, on_delete=models.CASCADE, related_name='delivery_routes')
    date = models.DateField()
    start_location = models.ForeignKey('geolocation.LocationPoint', on_delete=models.CASCADE, related_name='routes_starting')
    deliveries = models.ManyToManyField('deliveries.Delivery', through='RouteStop')
    total_distance = models.DecimalField(max_digits=8, decimal_places=2, default=0)
    estimated_duration = models.IntegerField(default=0)  # en minutes
    actual_duration = models.IntegerField(null=True, blank=True)
    status = models.CharField(max_length=20, choices=[
        ('planned', 'Planifiée'),
        ('in_progress', 'En cours'),
        ('completed', 'Terminée'),
        ('cancelled', 'Annulée')
    ], default='planned')
    created_at = models.DateTimeField(auto_now_add=True)

class RouteStop(models.Model):
    """Arrêts dans une route"""
    route = models.ForeignKey(DeliveryRoute, on_delete=models.CASCADE)
    delivery = models.ForeignKey('deliveries.Delivery', on_delete=models.CASCADE)
    stop_order = models.IntegerField()
    estimated_arrival = models.DateTimeField()
    actual_arrival = models.DateTimeField(null=True, blank=True)
    is_completed = models.BooleanField(default=False)

class DeliveryOptimizer:
    """Optimiseur de routes de livraison"""
    
    @staticmethod
    def optimize_route(delivery_person, deliveries_list, start_location):
        """Optimiser une route de livraison"""
        if not deliveries_list:
            return []
        
        # Algorithme du plus proche voisin simplifié
        unvisited = list(deliveries_list)
        route = []
        current_location = start_location
        
        while unvisited:
            nearest_delivery = None
            min_distance = float('inf')
            
            for delivery in unvisited:
                if delivery.location_point:
                    distance_info = current_location.calculate_distance_to(delivery.location_point)
                    if distance_info and distance_info['success']:
                        distance = distance_info['distance_km']
                        if distance < min_distance:
                            min_distance = distance
                            nearest_delivery = delivery
            
            if nearest_delivery:
                route.append(nearest_delivery)
                unvisited.remove(nearest_delivery)
                current_location = nearest_delivery.location_point
            else:
                # Si pas de localisation, ajouter à la fin
                route.extend(unvisited)
                break
        
        return route

class GroupDelivery(models.Model):
    """Livraisons groupées"""
    delivery_person = models.ForeignKey(User, on_delete=models.CASCADE)
    deliveries = models.ManyToManyField('deliveries.Delivery')
    region = models.ForeignKey('geolocation.GuineaRegion', on_delete=models.CASCADE)
    scheduled_date = models.DateField()
    total_cost_savings = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    status = models.CharField(max_length=20, choices=[
        ('planned', 'Planifiée'),
        ('confirmed', 'Confirmée'),
        ('in_progress', 'En cours'),
        ('completed', 'Terminée')
    ], default='planned')

class DeliveryPrediction(models.Model):
    """Prédictions de délais de livraison"""
    delivery = models.OneToOneField('deliveries.Delivery', on_delete=models.CASCADE)
    predicted_duration = models.IntegerField()  # en minutes
    confidence_level = models.DecimalField(max_digits=3, decimal_places=2)
    factors_considered = models.JSONField(default=dict)  # météo, trafic, etc.
    actual_duration = models.IntegerField(null=True, blank=True)
    accuracy_score = models.DecimalField(max_digits=3, decimal_places=2, null=True, blank=True)