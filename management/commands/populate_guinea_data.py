from django.core.management.base import BaseCommand
from geolocation.models import GuineaRegion, GuineaPrefecture, GuineaCommune

class Command(BaseCommand):
    help = 'Populate Guinea administrative divisions'

    def handle(self, *args, **options):
        # Créer les régions de Guinée
        regions_data = [
            {'name': 'Conakry', 'code': 'CNK'},
            {'name': 'Kindia', 'code': 'KIN'},
            {'name': 'Boké', 'code': 'BOK'},
            {'name': 'Labé', 'code': 'LAB'},
            {'name': 'Mamou', 'code': 'MAM'},
            {'name': 'Faranah', 'code': 'FAR'},
            {'name': 'Kankan', 'code': 'KAN'},
            {'name': 'Nzérékoré', 'code': 'NZE'},
        ]
        
        for region_data in regions_data:
            region, created = GuineaRegion.objects.get_or_create(
                code=region_data['code'],
                defaults={'name': region_data['name']}
            )
            if created:
                self.stdout.write(f"Région créée: {region.name}")
        
        # Créer quelques préfectures principales
        prefectures_data = [
            # Conakry
            {'region_code': 'CNK', 'name': 'Conakry', 'code': 'CNK-CNK'},
            {'region_code': 'CNK', 'name': 'Coyah', 'code': 'CNK-COY'},
            {'region_code': 'CNK', 'name': 'Dubréka', 'code': 'CNK-DUB'},
            
            # Kindia
            {'region_code': 'KIN', 'name': 'Kindia', 'code': 'KIN-KIN'},
            {'region_code': 'KIN', 'name': 'Forécariah', 'code': 'KIN-FOR'},
            {'region_code': 'KIN', 'name': 'Télimélé', 'code': 'KIN-TEL'},
            
            # Boké
            {'region_code': 'BOK', 'name': 'Boké', 'code': 'BOK-BOK'},
            {'region_code': 'BOK', 'name': 'Boffa', 'code': 'BOK-BOF'},
            {'region_code': 'BOK', 'name': 'Fria', 'code': 'BOK-FRI'},
            
            # Labé
            {'region_code': 'LAB', 'name': 'Labé', 'code': 'LAB-LAB'},
            {'region_code': 'LAB', 'name': 'Koubia', 'code': 'LAB-KOU'},
            {'region_code': 'LAB', 'name': 'Mali', 'code': 'LAB-MAL'},
            
            # Kankan
            {'region_code': 'KAN', 'name': 'Kankan', 'code': 'KAN-KAN'},
            {'region_code': 'KAN', 'name': 'Kérouané', 'code': 'KAN-KER'},
            {'region_code': 'KAN', 'name': 'Siguiri', 'code': 'KAN-SIG'},
        ]
        
        for pref_data in prefectures_data:
            try:
                region = GuineaRegion.objects.get(code=pref_data['region_code'])
                prefecture, created = GuineaPrefecture.objects.get_or_create(
                    code=pref_data['code'],
                    defaults={
                        'name': pref_data['name'],
                        'region': region
                    }
                )
                if created:
                    self.stdout.write(f"Préfecture créée: {prefecture.name}")
            except GuineaRegion.DoesNotExist:
                self.stdout.write(f"Région non trouvée: {pref_data['region_code']}")
        
        # Créer quelques communes principales
        communes_data = [
            # Conakry
            {'prefecture_code': 'CNK-CNK', 'name': 'Kaloum', 'code': 'CNK-CNK-KAL'},
            {'prefecture_code': 'CNK-CNK', 'name': 'Dixinn', 'code': 'CNK-CNK-DIX'},
            {'prefecture_code': 'CNK-CNK', 'name': 'Matam', 'code': 'CNK-CNK-MAT'},
            {'prefecture_code': 'CNK-CNK', 'name': 'Matoto', 'code': 'CNK-CNK-MAT2'},
            {'prefecture_code': 'CNK-CNK', 'name': 'Ratoma', 'code': 'CNK-CNK-RAT'},
            
            # Kindia
            {'prefecture_code': 'KIN-KIN', 'name': 'Kindia Centre', 'code': 'KIN-KIN-CEN'},
            {'prefecture_code': 'KIN-KIN', 'name': 'Damakania', 'code': 'KIN-KIN-DAM'},
            
            # Kankan
            {'prefecture_code': 'KAN-KAN', 'name': 'Kankan Centre', 'code': 'KAN-KAN-CEN'},
            {'prefecture_code': 'KAN-KAN', 'name': 'Baté-Nafadji', 'code': 'KAN-KAN-BAT'},
        ]
        
        for comm_data in communes_data:
            try:
                prefecture = GuineaPrefecture.objects.get(code=comm_data['prefecture_code'])
                commune, created = GuineaCommune.objects.get_or_create(
                    code=comm_data['code'],
                    defaults={
                        'name': comm_data['name'],
                        'prefecture': prefecture
                    }
                )
                if created:
                    self.stdout.write(f"Commune créée: {commune.name}")
            except GuineaPrefecture.DoesNotExist:
                self.stdout.write(f"Préfecture non trouvée: {comm_data['prefecture_code']}")
        
        self.stdout.write(self.style.SUCCESS('Données de la Guinée importées avec succès!'))