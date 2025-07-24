"""
ANALYTIQUES AVANCÉES
- Prédictions de ventes
- Analyse de sentiment
- Recommandations IA
"""

from django.db import models
from django.contrib.auth import get_user_model
import json

User = get_user_model()

class SalesPredict(models.Model):
    """Prédictions de ventes"""
    seller = models.ForeignKey(User, on_delete=models.CASCADE)
    product = models.ForeignKey('products.Product', on_delete=models.CASCADE, null=True, blank=True)
    prediction_date = models.DateField()
    predicted_sales = models.DecimalField(max_digits=10, decimal_places=2)
    predicted_quantity = models.IntegerField()
    confidence_score = models.DecimalField(max_digits=3, decimal_places=2)  # 0-1
    actual_sales = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

class CustomerBehavior(models.Model):
    """Analyse du comportement client"""
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    session_id = models.CharField(max_length=100)
    page_views = models.JSONField(default=list)
    time_spent = models.IntegerField()  # en secondes
    products_viewed = models.ManyToManyField('products.Product')
    search_queries = models.JSONField(default=list)
    conversion_funnel_stage = models.CharField(max_length=20, choices=[
        ('awareness', 'Découverte'),
        ('interest', 'Intérêt'),
        ('consideration', 'Considération'),
        ('purchase', 'Achat'),
        ('retention', 'Fidélisation')
    ])
    created_at = models.DateTimeField(auto_now_add=True)

class AIRecommendation(models.Model):
    """Recommandations IA"""
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    product = models.ForeignKey('products.Product', on_delete=models.CASCADE)
    recommendation_type = models.CharField(max_length=20, choices=[
        ('collaborative', 'Filtrage collaboratif'),
        ('content', 'Basé sur le contenu'),
        ('trending', 'Tendances'),
        ('seasonal', 'Saisonnier'),
        ('location', 'Basé sur la localisation')
    ])
    confidence_score = models.DecimalField(max_digits=3, decimal_places=2)
    was_clicked = models.BooleanField(default=False)
    was_purchased = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

class SentimentAnalysis(models.Model):
    """Analyse de sentiment des avis"""
    review = models.OneToOneField('reviews.Review', on_delete=models.CASCADE)
    sentiment_score = models.DecimalField(max_digits=3, decimal_places=2)  # -1 à 1
    sentiment_label = models.CharField(max_length=20, choices=[
        ('very_negative', 'Très négatif'),
        ('negative', 'Négatif'),
        ('neutral', 'Neutre'),
        ('positive', 'Positif'),
        ('very_positive', 'Très positif')
    ])
    keywords = models.JSONField(default=list)
    processed_at = models.DateTimeField(auto_now_add=True)