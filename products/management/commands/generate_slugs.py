# Dans products/management/commands/generate_slugs.py
from django.core.management.base import BaseCommand
from products.models import Product

class Command(BaseCommand):
    help = 'Generate slugs for existing products'

    def handle(self, *args, **options):
        for product in Product.objects.filter(slug__isnull=True):
            product.save()  # Cela déclenchera la génération du slug
            self.stdout.write(f'Generated slug for {product.name}: {product.slug}')