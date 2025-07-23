from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from geolocation.models import DeliveryZone, GuineaCommune
from accounts.models import SellerDeliveryZone

User = get_user_model()

class Command(BaseCommand):
    help = 'Associe les vendeurs à des DeliveryZone en fonction de leur ville'

    def handle(self, *args, **options):
        sellers = User.objects.filter(user_type='seller')
        for seller in sellers:
            if seller.city:
                # Recherche une commune correspondant à la ville du vendeur
                commune = GuineaCommune.objects.filter(name__iexact=seller.city).first()
                if commune:
                    # Recherche les zones de livraison contenant cette commune
                    zones = DeliveryZone.objects.filter(communes=commune, is_active=True)
                    for zone in zones:
                        SellerDeliveryZone.objects.get_or_create(seller=seller, delivery_zone=zone)
                        self.stdout.write(self.style.SUCCESS(f'Associé {seller.username} à {zone.name}'))
                    if not zones:
                        self.stdout.write(self.style.WARNING(f'Aucune zone active trouvée pour la commune {seller.city}'))
                else:
                    self.stdout.write(self.style.WARNING(f'Aucune commune trouvée pour {seller.city}'))
            else:
                self.stdout.write(self.style.WARNING(f'Aucune ville définie pour {seller.username}'))