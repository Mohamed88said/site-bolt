from django.db import models
from django.contrib.auth import get_user_model
from django.utils.translation import gettext_lazy as _
from geolocation.distance_calculator import DistanceCalculator
from decimal import Decimal

User = get_user_model()

class DeliveryRoute(models.Model):
    """Routes de livraison optimisées"""
    delivery_person = models.ForeignKey(User, on_delete=models.CASCADE, related_name='delivery_routes')
    date = models.DateField(verbose_name=_('Date'))
    start_location = models.ForeignKey('geolocation.LocationPoint', on_delete=models.CASCADE, related_name='routes_starting')
    deliveries = models.ManyToManyField('deliveries.Delivery', through='RouteStop')
    total_distance_km = models.DecimalField(max_digits=8, decimal_places=2, default=0, verbose_name=_('Distance totale (km)'))
    estimated_duration_minutes = models.IntegerField(default=0, verbose_name=_('Durée estimée (min)'))
    actual_duration_minutes = models.IntegerField(null=True, blank=True, verbose_name=_('Durée réelle (min)'))
    total_earnings_gnf = models.DecimalField(max_digits=12, decimal_places=0, default=0, verbose_name=_('Gains totaux (GNF)'))
    fuel_cost_gnf = models.DecimalField(max_digits=10, decimal_places=0, default=0, verbose_name=_('Coût carburant (GNF)'))
    status = models.CharField(max_length=20, choices=[
        ('planned', _('Planifiée')),
        ('in_progress', _('En cours')),
        ('completed', _('Terminée')),
        ('cancelled', _('Annulée'))
    ], default='planned', verbose_name=_('Statut'))
    optimization_score = models.DecimalField(max_digits=3, decimal_places=2, default=0, verbose_name=_('Score d\'optimisation'))
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = _('Route de livraison')
        verbose_name_plural = _('Routes de livraison')
        ordering = ['-created_at']
    
    def __str__(self):
        return f"Route {self.delivery_person.username} - {self.date}"
    
    def calculate_optimization_score(self):
        """Calculer le score d'optimisation de la route"""
        if not self.deliveries.exists():
            return 0
        
        # Facteurs: distance, temps, nombre de livraisons, gains
        deliveries_count = self.deliveries.count()
        if deliveries_count == 0:
            return 0
        
        # Score basé sur l'efficacité (gains/km)
        if self.total_distance_km > 0:
            efficiency = float(self.total_earnings_gnf) / float(self.total_distance_km)
            # Normaliser le score entre 0 et 1
            max_efficiency = 10000  # 10,000 GNF par km comme référence
            score = min(efficiency / max_efficiency, 1.0)
            return round(score, 2)
        return 0

class RouteStop(models.Model):
    """Arrêts dans une route"""
    route = models.ForeignKey(DeliveryRoute, on_delete=models.CASCADE, related_name='stops')
    delivery = models.ForeignKey('deliveries.Delivery', on_delete=models.CASCADE)
    stop_order = models.IntegerField(verbose_name=_('Ordre d\'arrêt'))
    estimated_arrival = models.DateTimeField(verbose_name=_('Arrivée estimée'))
    actual_arrival = models.DateTimeField(null=True, blank=True, verbose_name=_('Arrivée réelle'))
    estimated_duration_minutes = models.IntegerField(default=15, verbose_name=_('Durée estimée (min)'))
    actual_duration_minutes = models.IntegerField(null=True, blank=True, verbose_name=_('Durée réelle (min)'))
    distance_from_previous_km = models.DecimalField(max_digits=8, decimal_places=2, default=0)
    is_completed = models.BooleanField(default=False, verbose_name=_('Terminé'))
    notes = models.TextField(blank=True, verbose_name=_('Notes'))
    
    class Meta:
        verbose_name = _('Arrêt de route')
        verbose_name_plural = _('Arrêts de route')
        ordering = ['route', 'stop_order']
    
    def __str__(self):
        return f"Arrêt {self.stop_order} - {self.delivery.tracking_number}"

class GroupDelivery(models.Model):
    """Livraisons groupées"""
    delivery_person = models.ForeignKey(User, on_delete=models.CASCADE, related_name='group_deliveries')
    deliveries = models.ManyToManyField('deliveries.Delivery', related_name='group_deliveries')
    region = models.ForeignKey('geolocation.GuineaRegion', on_delete=models.CASCADE)
    prefecture = models.ForeignKey('geolocation.GuineaPrefecture', on_delete=models.CASCADE, null=True, blank=True)
    scheduled_date = models.DateField(verbose_name=_('Date programmée'))
    total_cost_savings_gnf = models.DecimalField(max_digits=10, decimal_places=0, default=0, verbose_name=_('Économies totales (GNF)'))
    individual_cost_gnf = models.DecimalField(max_digits=10, decimal_places=0, default=0, verbose_name=_('Coût individuel (GNF)'))
    group_cost_gnf = models.DecimalField(max_digits=10, decimal_places=0, default=0, verbose_name=_('Coût groupé (GNF)'))
    status = models.CharField(max_length=20, choices=[
        ('planned', _('Planifiée')),
        ('confirmed', _('Confirmée')),
        ('in_progress', _('En cours')),
        ('completed', _('Terminée')),
        ('cancelled', _('Annulée'))
    ], default='planned', verbose_name=_('Statut'))
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = _('Livraison groupée')
        verbose_name_plural = _('Livraisons groupées')
    
    def __str__(self):
        return f"Livraison groupée {self.region.name} - {self.scheduled_date}"
    
    @property
    def delivery_count(self):
        return self.deliveries.count()
    
    @property
    def savings_percentage(self):
        if self.individual_cost_gnf > 0:
            return ((self.individual_cost_gnf - self.group_cost_gnf) / self.individual_cost_gnf) * 100
        return 0

class DeliveryPrediction(models.Model):
    """Prédictions de délais de livraison"""
    delivery = models.OneToOneField('deliveries.Delivery', on_delete=models.CASCADE, related_name='prediction')
    predicted_duration_minutes = models.IntegerField(verbose_name=_('Durée prédite (minutes)'))
    confidence_level = models.DecimalField(max_digits=3, decimal_places=2, verbose_name=_('Niveau de confiance'))
    factors_considered = models.JSONField(default=dict, verbose_name=_('Facteurs considérés'))
    weather_impact = models.DecimalField(max_digits=3, decimal_places=2, default=0, verbose_name=_('Impact météo'))
    traffic_impact = models.DecimalField(max_digits=3, decimal_places=2, default=0, verbose_name=_('Impact trafic'))
    distance_km = models.DecimalField(max_digits=8, decimal_places=2, verbose_name=_('Distance (km)'))
    actual_duration_minutes = models.IntegerField(null=True, blank=True, verbose_name=_('Durée réelle (min)'))
    accuracy_score = models.DecimalField(max_digits=3, decimal_places=2, null=True, blank=True, verbose_name=_('Score de précision'))
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = _('Prédiction de livraison')
        verbose_name_plural = _('Prédictions de livraison')
    
    def __str__(self):
        return f"Prédiction {self.delivery.tracking_number}"
    
    def calculate_accuracy(self):
        """Calculer la précision de la prédiction"""
        if self.actual_duration_minutes:
            predicted = self.predicted_duration_minutes
            actual = self.actual_duration_minutes
            error_percentage = abs(predicted - actual) / actual * 100
            accuracy = max(0, 100 - error_percentage) / 100
            self.accuracy_score = round(accuracy, 2)
            self.save()
            return self.accuracy_score
        return None

class SmartWarehouse(models.Model):
    """Entrepôts intelligents"""
    name = models.CharField(max_length=100, verbose_name=_('Nom'))
    location = models.ForeignKey('geolocation.LocationPoint', on_delete=models.CASCADE)
    manager = models.ForeignKey(User, on_delete=models.CASCADE, related_name='managed_warehouses')
    capacity_cubic_meters = models.DecimalField(max_digits=10, decimal_places=2, verbose_name=_('Capacité (m³)'))
    current_utilization = models.DecimalField(max_digits=5, decimal_places=2, default=0, verbose_name=_('Utilisation actuelle (%)'))
    temperature_controlled = models.BooleanField(default=False, verbose_name=_('Température contrôlée'))
    security_level = models.CharField(max_length=20, choices=[
        ('basic', _('Basique')),
        ('standard', _('Standard')),
        ('high', _('Élevé')),
        ('maximum', _('Maximum'))
    ], default='standard', verbose_name=_('Niveau de sécurité'))
    operating_hours = models.JSONField(default=dict, verbose_name=_('Heures d\'ouverture'))
    is_active = models.BooleanField(default=True, verbose_name=_('Actif'))
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = _('Entrepôt intelligent')
        verbose_name_plural = _('Entrepôts intelligents')
    
    def __str__(self):
        return self.name

class WarehouseInventory(models.Model):
    """Inventaire d'entrepôt"""
    warehouse = models.ForeignKey(SmartWarehouse, on_delete=models.CASCADE, related_name='inventory')
    product = models.ForeignKey('products.Product', on_delete=models.CASCADE)
    quantity = models.IntegerField(default=0, verbose_name=_('Quantité'))
    reserved_quantity = models.IntegerField(default=0, verbose_name=_('Quantité réservée'))
    location_in_warehouse = models.CharField(max_length=50, blank=True, verbose_name=_('Emplacement'))
    last_updated = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = _('Inventaire entrepôt')
        verbose_name_plural = _('Inventaires entrepôts')
        unique_together = ['warehouse', 'product']
    
    def __str__(self):
        return f"{self.warehouse.name} - {self.product.name} ({self.quantity})"
    
    @property
    def available_quantity(self):
        return self.quantity - self.reserved_quantity