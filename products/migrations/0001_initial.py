# Generated by Django 5.2.4 on 2025-07-13 12:40

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='Category',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=100, verbose_name='Nom')),
                ('slug', models.SlugField(unique=True, verbose_name='Slug')),
                ('description', models.TextField(blank=True, verbose_name='Description')),
                ('image', models.ImageField(blank=True, upload_to='categories/', verbose_name='Image')),
                ('is_active', models.BooleanField(default=True, verbose_name='Actif')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('parent', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='products.category', verbose_name='Catégorie parent')),
            ],
            options={
                'verbose_name': 'Catégorie',
                'verbose_name_plural': 'Catégories',
                'ordering': ['name'],
            },
        ),
        migrations.CreateModel(
            name='Product',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=200, verbose_name='Nom')),
                ('slug', models.SlugField(unique=True, verbose_name='Slug')),
                ('description', models.TextField(verbose_name='Description')),
                ('short_description', models.TextField(blank=True, max_length=300, verbose_name='Description courte')),
                ('price', models.DecimalField(decimal_places=2, max_digits=10, verbose_name='Prix')),
                ('discount_price', models.DecimalField(blank=True, decimal_places=2, max_digits=10, null=True, verbose_name='Prix réduit')),
                ('stock', models.IntegerField(default=0, verbose_name='Stock')),
                ('sku', models.CharField(max_length=100, unique=True, verbose_name='SKU')),
                ('weight', models.DecimalField(blank=True, decimal_places=2, max_digits=5, null=True, verbose_name='Poids (kg)')),
                ('dimensions', models.CharField(blank=True, max_length=100, verbose_name='Dimensions')),
                ('is_active', models.BooleanField(default=True, verbose_name='Actif')),
                ('is_featured', models.BooleanField(default=False, verbose_name='Mis en avant')),
                ('views', models.IntegerField(default=0, verbose_name='Vues')),
                ('rating', models.DecimalField(decimal_places=2, default=0.0, max_digits=3, verbose_name='Note')),
                ('stock_alert_threshold', models.IntegerField(default=5, verbose_name="Seuil d'alerte stock")),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('category', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='products', to='products.category', verbose_name='Catégorie')),
                ('seller', models.ForeignKey(limit_choices_to={'user_type': 'seller'}, on_delete=django.db.models.deletion.CASCADE, related_name='products', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'verbose_name': 'Produit',
                'verbose_name_plural': 'Produits',
                'ordering': ['-created_at'],
            },
        ),
        migrations.CreateModel(
            name='ProductImage',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('image', models.ImageField(upload_to='products/', verbose_name='Image')),
                ('alt_text', models.CharField(blank=True, max_length=200, verbose_name='Texte alternatif')),
                ('is_main', models.BooleanField(default=False, verbose_name='Image principale')),
                ('order', models.IntegerField(default=0, verbose_name='Ordre')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('product', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='images', to='products.product')),
            ],
            options={
                'verbose_name': 'Image de produit',
                'verbose_name_plural': 'Images de produits',
                'ordering': ['order'],
            },
        ),
        migrations.CreateModel(
            name='ProductVariant',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=100, verbose_name='Nom')),
                ('value', models.CharField(max_length=100, verbose_name='Valeur')),
                ('price_adjustment', models.DecimalField(decimal_places=2, default=0.0, max_digits=10, verbose_name='Ajustement de prix')),
                ('stock', models.IntegerField(default=0, verbose_name='Stock')),
                ('sku', models.CharField(max_length=100, unique=True, verbose_name='SKU')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('product', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='variants', to='products.product')),
            ],
            options={
                'verbose_name': 'Variante de produit',
                'verbose_name_plural': 'Variantes de produits',
                'unique_together': {('product', 'name', 'value')},
            },
        ),
        migrations.CreateModel(
            name='Review',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('rating', models.IntegerField(choices=[(1, '1 étoile'), (2, '2 étoiles'), (3, '3 étoiles'), (4, '4 étoiles'), (5, '5 étoiles')], verbose_name='Note')),
                ('title', models.CharField(blank=True, max_length=200, verbose_name='Titre')),
                ('comment', models.TextField(blank=True, verbose_name='Commentaire')),
                ('is_verified', models.BooleanField(default=False, verbose_name='Achat vérifié')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('is_active', models.BooleanField(default=True, verbose_name='Actif')),
                ('product', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='product_reviews', to='products.product')),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='product_user_reviews', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'verbose_name': 'Avis',
                'verbose_name_plural': 'Avis',
                'ordering': ['-created_at'],
                'unique_together': {('product', 'user')},
            },
        ),
        migrations.CreateModel(
            name='StockAlert',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('is_active', models.BooleanField(default=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('notified_at', models.DateTimeField(blank=True, null=True)),
                ('product', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='stock_alerts', to='products.product')),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='stock_alerts', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'verbose_name': 'Alerte de stock',
                'verbose_name_plural': 'Alertes de stock',
                'unique_together': {('user', 'product')},
            },
        ),
    ]
