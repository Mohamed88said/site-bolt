"""
COMMERCE SOCIAL GUINÉEN
- Groupes d'achat communautaires
- Recommandations entre amis
- Achats groupés pour réductions
"""

from django.db import models
from django.contrib.auth import get_user_model

User = get_user_model()

class CommunityGroup(models.Model):
    """Groupes d'achat communautaires"""
    name = models.CharField(max_length=100)
    description = models.TextField()
    creator = models.ForeignKey(User, on_delete=models.CASCADE, related_name='created_groups')
    members = models.ManyToManyField(User, through='GroupMembership')
    region = models.ForeignKey('geolocation.GuineaRegion', on_delete=models.CASCADE)
    is_active = models.BooleanField(default=True)
    min_members_for_discount = models.IntegerField(default=5)
    group_discount_percentage = models.DecimalField(max_digits=5, decimal_places=2, default=10)
    created_at = models.DateTimeField(auto_now_add=True)

class GroupMembership(models.Model):
    """Adhésion aux groupes"""
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    group = models.ForeignKey(CommunityGroup, on_delete=models.CASCADE)
    role = models.CharField(max_length=20, choices=[
        ('member', 'Membre'),
        ('moderator', 'Modérateur'),
        ('admin', 'Administrateur')
    ], default='member')
    joined_at = models.DateTimeField(auto_now_add=True)

class GroupOrder(models.Model):
    """Commandes groupées"""
    group = models.ForeignKey(CommunityGroup, on_delete=models.CASCADE)
    product = models.ForeignKey('products.Product', on_delete=models.CASCADE)
    target_quantity = models.IntegerField()
    current_quantity = models.IntegerField(default=0)
    discount_percentage = models.DecimalField(max_digits=5, decimal_places=2)
    deadline = models.DateTimeField()
    is_active = models.BooleanField(default=True)
    created_by = models.ForeignKey(User, on_delete=models.CASCADE)

class SocialRecommendation(models.Model):
    """Recommandations sociales"""
    recommender = models.ForeignKey(User, on_delete=models.CASCADE, related_name='recommendations_made')
    recommended_to = models.ForeignKey(User, on_delete=models.CASCADE, related_name='recommendations_received')
    product = models.ForeignKey('products.Product', on_delete=models.CASCADE)
    message = models.TextField(blank=True)
    is_purchased = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)