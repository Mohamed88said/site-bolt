from django.core.management.base import BaseCommand
from geolocation.models import DeliveryZone, GuineaRegion, GuineaPrefecture, GuineaCommune

class GuineaDeliveryZoneManager:
    """Gestionnaire des zones de livraison spécifiques à la Guinée"""
    
    @staticmethod
    def create_guinea_delivery_zones():
        """Créer les zones de livraison adaptées à la Guinée"""
        
        # Zone Conakry - Centre économique
        conakry_zone, created = DeliveryZone.objects.get_or_create(
            name='Grand Conakry',
            defaults={
                'base_delivery_cost': 15000,  # 15,000 GNF
                'cost_per_km': 1000,          # 1,000 GNF par km
                'free_delivery_threshold': 200000,  # 200,000 GNF
                'estimated_delivery_days': 1,
                'max_distance_km': 25,
                'is_active': True
            }
        )
        
        if created:
            # Ajouter toutes les communes de Conakry
            conakry_region = GuineaRegion.objects.filter(code='CNK').first()
            if conakry_region:
                conakry_zone.regions.add(conakry_region)
                # Ajouter aussi Coyah et Dubréka (banlieue)
                nearby_prefectures = GuineaPrefecture.objects.filter(
                    code__in=['CNK-COY', 'CNK-DUB']
                )
                conakry_zone.prefectures.set(nearby_prefectures)
        
        # Zone Kindia - Région proche
        kindia_zone, created = DeliveryZone.objects.get_or_create(
            name='Région Kindia',
            defaults={
                'base_delivery_cost': 25000,  # 25,000 GNF
                'cost_per_km': 1500,          # 1,500 GNF par km
                'free_delivery_threshold': 300000,  # 300,000 GNF
                'estimated_delivery_days': 2,
                'max_distance_km': 40,
                'is_active': True
            }
        )
        
        if created:
            kindia_region = GuineaRegion.objects.filter(code='KIN').first()
            if kindia_region:
                kindia_zone.regions.add(kindia_region)
        
        # Zone Kankan - Haute Guinée
        kankan_zone, created = DeliveryZone.objects.get_or_create(
            name='Haute Guinée (Kankan)',
            defaults={
                'base_delivery_cost': 40000,  # 40,000 GNF
                'cost_per_km': 2000,          # 2,000 GNF par km
                'free_delivery_threshold': 500000,  # 500,000 GNF
                'estimated_delivery_days': 3,
                'max_distance_km': 60,
                'is_active': True
            }
        )
        
        if created:
            kankan_region = GuineaRegion.objects.filter(code='KAN').first()
            if kankan_region:
                kankan_zone.regions.add(kankan_region)
        
        # Zone Labé - Moyenne Guinée
        labe_zone, created = DeliveryZone.objects.get_or_create(
            name='Moyenne Guinée (Labé)',
            defaults={
                'base_delivery_cost': 35000,  # 35,000 GNF
                'cost_per_km': 1800,          # 1,800 GNF par km
                'free_delivery_threshold': 400000,  # 400,000 GNF
                'estimated_delivery_days': 3,
                'max_distance_km': 50,
                'is_active': True
            }
        )
        
        if created:
            labe_region = GuineaRegion.objects.filter(code='LAB').first()
            if labe_region:
                labe_zone.regions.add(labe_region)
        
        # Zone Nzérékoré - Guinée Forestière
        nzerekore_zone, created = DeliveryZone.objects.get_or_create(
            name='Guinée Forestière (Nzérékoré)',
            defaults={
                'base_delivery_cost': 45000,  # 45,000 GNF
                'cost_per_km': 2500,          # 2,500 GNF par km
                'free_delivery_threshold': 600000,  # 600,000 GNF
                'estimated_delivery_days': 4,
                'max_distance_km': 70,
                'is_active': True
            }
        )
        
        if created:
            nzerekore_region = GuineaRegion.objects.filter(code='NZE').first()
            if nzerekore_region:
                nzerekore_zone.regions.add(nzerekore_region)
        
        # Zone Boké - Guinée Maritime
        boke_zone, created = DeliveryZone.objects.get_or_create(
            name='Guinée Maritime (Boké)',
            defaults={
                'base_delivery_cost': 30000,  # 30,000 GNF
                'cost_per_km': 1600,          # 1,600 GNF par km
                'free_delivery_threshold': 350000,  # 350,000 GNF
                'estimated_delivery_days': 2,
                'max_distance_km': 45,
                'is_active': True
            }
        )
        
        if created:
            boke_region = GuineaRegion.objects.filter(code='BOK').first()
            if boke_region:
                boke_zone.regions.add(boke_region)
        
        return {
            'conakry': conakry_zone,
            'kindia': kindia_zone,
            'kankan': kankan_zone,
            'labe': labe_zone,
            'nzerekore': nzerekore_zone,
            'boke': boke_zone
        }
    
    @staticmethod
    def get_delivery_cost_for_location(location_point, product_value=0):
        """Calculer le coût de livraison pour une localisation donnée"""
        if not location_point:
            return 15000  # Coût par défaut
        
        # Trouver la zone de livraison appropriée
        zones = DeliveryZone.objects.filter(
            models.Q(communes=location_point.commune) |
            models.Q(prefectures=location_point.prefecture) |
            models.Q(regions=location_point.region),
            is_active=True
        ).order_by('communes__isnull', 'prefectures__isnull', 'regions__isnull')
        
        zone = zones.first()
        if not zone:
            return 15000  # Coût par défaut si aucune zone trouvée
        
        # Vérifier si livraison gratuite
        if zone.free_delivery_threshold and product_value >= zone.free_delivery_threshold:
            return 0
        
        # Calculer le coût basé sur la distance si possible
        try:
            from .distance_calculator import DistanceCalculator
            # Coordonnées de Conakry comme point de référence
            conakry_coords = (9.6412, -13.5784)
            location_coords = (float(location_point.latitude), float(location_point.longitude))
            
            distance_info = DistanceCalculator.get_best_distance(
                conakry_coords[0], conakry_coords[1],
                location_coords[0], location_coords[1]
            )
            
            if distance_info['success']:
                distance_km = distance_info['distance_km']
                total_cost = float(zone.base_delivery_cost) + (distance_km * float(zone.cost_per_km))
                return min(total_cost, 100000)  # Maximum 100,000 GNF
            
        except Exception as e:
            print(f"Erreur calcul distance: {e}")
        
        return float(zone.base_delivery_cost)
    
    @staticmethod
    def get_estimated_delivery_time(location_point):
        """Obtenir le délai de livraison estimé"""
        if not location_point:
            return "2-3 jours"
        
        zones = DeliveryZone.objects.filter(
            models.Q(communes=location_point.commune) |
            models.Q(prefectures=location_point.prefecture) |
            models.Q(regions=location_point.region),
            is_active=True
        ).order_by('communes__isnull', 'prefectures__isnull', 'regions__isnull')
        
        zone = zones.first()
        if zone:
            days = zone.estimated_delivery_days
            if days == 1:
                return "24h"
            elif days == 2:
                return "2-3 jours"
            else:
                return f"{days} jours"
        
        return "2-3 jours"

class Command(BaseCommand):
    help = 'Créer les zones de livraison pour la Guinée'

    def handle(self, *args, **options):
        zones = GuineaDeliveryZoneManager.create_guinea_delivery_zones()
        
        for zone_name, zone in zones.items():
            self.stdout.write(f"Zone {zone_name}: {zone.name} créée/mise à jour")
        
        self.stdout.write(self.style.SUCCESS('Zones de livraison Guinée créées avec succès!'))