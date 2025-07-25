# Generated by Django 5.2.4 on 2025-07-13 12:40

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('orders', '0001_initial'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='Coupon',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('code', models.CharField(max_length=50, unique=True, verbose_name='Code')),
                ('discount_type', models.CharField(choices=[('percentage', 'Pourcentage'), ('fixed', 'Montant fixe')], max_length=20, verbose_name='Type de remise')),
                ('discount_value', models.DecimalField(decimal_places=2, max_digits=10, verbose_name='Valeur de remise')),
                ('minimum_amount', models.DecimalField(decimal_places=2, default=0, max_digits=10, verbose_name='Montant minimum')),
                ('maximum_discount', models.DecimalField(blank=True, decimal_places=2, max_digits=10, null=True, verbose_name='Remise maximum')),
                ('usage_limit', models.IntegerField(blank=True, null=True, verbose_name="Limite d'utilisation")),
                ('used_count', models.IntegerField(default=0, verbose_name="Nombre d'utilisations")),
                ('valid_from', models.DateTimeField(verbose_name='Valide à partir de')),
                ('valid_to', models.DateTimeField(verbose_name="Valide jusqu'à")),
                ('is_active', models.BooleanField(default=True, verbose_name='Actif')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('created_by', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='created_coupons', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'verbose_name': 'Coupon',
                'verbose_name_plural': 'Coupons',
            },
        ),
        migrations.CreateModel(
            name='CouponUsage',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('discount_amount', models.DecimalField(decimal_places=2, max_digits=10)),
                ('used_at', models.DateTimeField(auto_now_add=True)),
                ('coupon', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='usages', to='coupons.coupon')),
                ('order', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='orders.order')),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'verbose_name': 'Utilisation de coupon',
                'verbose_name_plural': 'Utilisations de coupons',
            },
        ),
    ]
