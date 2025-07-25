# Generated by Django 5.2.4 on 2025-07-16 14:20

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('deliveries', '0001_initial'),
        ('geolocation', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='delivery',
            name='delivery_zone',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='deliveries', to='geolocation.deliveryzone', verbose_name='Zone de livraison'),
        ),
        migrations.AddField(
            model_name='delivery',
            name='location_point',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='deliveries', to='geolocation.locationpoint', verbose_name='Point de localisation'),
        ),
    ]
