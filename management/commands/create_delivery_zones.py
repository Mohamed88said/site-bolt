from django.core.management.base import BaseCommand
from geolocation.models import DeliveryZone, GuineaRegion, GuineaPrefecture, GuineaCommune

class Command(BaseCommand):
    help = 'Créer les zones de livraison par défaut pour la Guinée'

    def handle(self, *args, **options):
        # Zone Conakry (centre)
        conakry_zone, created = DeliveryZone.objects.get_or_create(
            name='Conakry Centre',
            defaults={
                'base_delivery_cost': 5.00,
                'cost_per_km': 0.50,
                'free_delivery_threshold': 50.00,
                'estimated_delivery_days': 1,
                'max_distance_km': 15,
                'is_active': True
            }
        )
        
        if created:
            # Ajouter les communes de Conakry
            conakry_communes = GuineaCommune.objects.filter(
                prefecture__region__code='CNK'
            )
            conakry_zone.communes.set(conakry_communes)
            self.stdout.write(f"Zone créée: {conakry_zone.name}")
        
        # Zone Kindia
        kindia_zone, created = DeliveryZone.objects.get_or_create(
            name='Région Kindia',
            defaults={
                'base_delivery_cost': 8.00,
                'cost_per_km': 0.75,
                'free_delivery_threshold': 75.00,
                'estimated_delivery_days': 2,
                'max_distance_km': 30,
                'is_active': True
            }
        )
        
        if created:
            kindia_region = GuineaRegion.objects.filter(code='KIN').first()
            if kindia_region:
                kindia_zone.regions.add(kindia_region)
            self.stdout.write(f"Zone créée: {kindia_zone.name}")
        
        # Zone Kankan
        kankan_zone, created = DeliveryZone.objects.get_or_create(
            name='Région Kankan',
            defaults={
                'base_delivery_cost': 12.00,
                'cost_per_km': 1.00,
                'free_delivery_threshold': 100.00,
                'estimated_delivery_days': 3,
                'max_distance_km': 50,
                'is_active': True
            }
        )
        
        if created:
            kankan_region = GuineaRegion.objects.filter(code='KAN').first()
            if kankan_region:
                kankan_zone.regions.add(kankan_region)
            self.stdout.write(f"Zone créée: {kankan_zone.name}")
        
        self.stdout.write(self.style.SUCCESS('Zones de livraison créées avec succès!'))