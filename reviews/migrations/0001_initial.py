# Generated by Django 5.2.4 on 2025-07-13 12:40

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('orders', '0001_initial'),
        ('products', '0001_initial'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='Review',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('rating', models.IntegerField(choices=[(1, '1 étoile'), (2, '2 étoiles'), (3, '3 étoiles'), (4, '4 étoiles'), (5, '5 étoiles')], verbose_name='Note')),
                ('title', models.CharField(blank=True, max_length=200, verbose_name='Titre')),
                ('comment', models.TextField(blank=True, verbose_name='Commentaire')),
                ('is_verified', models.BooleanField(default=False, verbose_name='Achat vérifié')),
                ('is_approved', models.BooleanField(default=True, verbose_name='Approuvé')),
                ('helpful_count', models.IntegerField(default=0, verbose_name='Votes utiles')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('is_active', models.BooleanField(default=True)),
                ('order', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to='orders.order')),
                ('product', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='review_app_reviews', to='products.product')),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='review_app_user_reviews', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'verbose_name': 'Avis',
                'verbose_name_plural': 'Avis',
                'ordering': ['-created_at'],
                'unique_together': {('product', 'user')},
            },
        ),
        migrations.CreateModel(
            name='ReviewResponse',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('response', models.TextField(verbose_name='Réponse')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('review', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name='response', to='reviews.review')),
                ('seller', models.ForeignKey(limit_choices_to={'user_type': 'seller'}, on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'verbose_name': 'Réponse à un avis',
                'verbose_name_plural': 'Réponses aux avis',
            },
        ),
        migrations.CreateModel(
            name='ReviewHelpful',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('is_helpful', models.BooleanField(default=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('review', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='helpful_votes', to='reviews.review')),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'unique_together': {('review', 'user')},
            },
        ),
    ]
