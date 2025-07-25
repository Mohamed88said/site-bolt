# Generated by Django 5.2.4 on 2025-07-13 12:40

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('products', '0001_initial'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='ProductView',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('ip_address', models.GenericIPAddressField()),
                ('user_agent', models.TextField(blank=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('product', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='product_views', to='products.product')),
                ('user', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'verbose_name': 'Vue produit',
                'verbose_name_plural': 'Vues produits',
            },
        ),
        migrations.CreateModel(
            name='SearchQuery',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('query', models.CharField(max_length=200)),
                ('results_count', models.IntegerField(default=0)),
                ('ip_address', models.GenericIPAddressField()),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('user', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'verbose_name': 'Recherche',
                'verbose_name_plural': 'Recherches',
            },
        ),
        migrations.CreateModel(
            name='SalesAnalytics',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('date', models.DateField()),
                ('total_sales', models.DecimalField(decimal_places=2, default=0, max_digits=10)),
                ('total_orders', models.IntegerField(default=0)),
                ('total_products_sold', models.IntegerField(default=0)),
                ('average_order_value', models.DecimalField(decimal_places=2, default=0, max_digits=10)),
                ('seller', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='sales_analytics', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'verbose_name': 'Analytique vente',
                'verbose_name_plural': 'Analytiques ventes',
                'unique_together': {('seller', 'date')},
            },
        ),
    ]
