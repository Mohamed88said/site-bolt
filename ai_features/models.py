from django.db import models
from django.contrib.auth import get_user_model
from django.utils.translation import gettext_lazy as _
import json
from decimal import Decimal

User = get_user_model()

class AIRecommendation(models.Model):
    """Recommandations IA"""
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='ai_recommendations')
    product = models.ForeignKey('products.Product', on_delete=models.CASCADE)
    recommendation_type = models.CharField(max_length=20, choices=[
        ('collaborative', _('Filtrage collaboratif')),
        ('content', _('Basé sur le contenu')),
        ('trending', _('Tendances')),
        ('seasonal', _('Saisonnier')),
        ('location', _('Basé sur la localisation')),
        ('price_drop', _('Baisse de prix')),
        ('back_in_stock', _('Retour en stock')),
        ('similar_users', _('Utilisateurs similaires'))
    ], verbose_name=_('Type de recommandation'))
    confidence_score = models.DecimalField(max_digits=3, decimal_places=2, verbose_name=_('Score de confiance'))
    reasoning = models.TextField(blank=True, verbose_name=_('Raisonnement'))
    was_clicked = models.BooleanField(default=False, verbose_name=_('Cliqué'))
    was_purchased = models.BooleanField(default=False, verbose_name=_('Acheté'))
    click_timestamp = models.DateTimeField(null=True, blank=True)
    purchase_timestamp = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = _('Recommandation IA')
        verbose_name_plural = _('Recommandations IA')
        ordering = ['-confidence_score', '-created_at']
    
    def __str__(self):
        return f"Recommandation {self.product.name} pour {self.user.username}"

class CustomerBehavior(models.Model):
    """Analyse du comportement client"""
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='behavior_data')
    session_id = models.CharField(max_length=100, verbose_name=_('ID de session'))
    page_views = models.JSONField(default=list, verbose_name=_('Pages vues'))
    time_spent_seconds = models.IntegerField(default=0, verbose_name=_('Temps passé (secondes)'))
    products_viewed = models.ManyToManyField('products.Product', blank=True, related_name='viewed_by')
    search_queries = models.JSONField(default=list, verbose_name=_('Requêtes de recherche'))
    cart_abandonment = models.BooleanField(default=False, verbose_name=_('Panier abandonné'))
    conversion_funnel_stage = models.CharField(max_length=20, choices=[
        ('awareness', _('Découverte')),
        ('interest', _('Intérêt')),
        ('consideration', _('Considération')),
        ('intent', _('Intention')),
        ('purchase', _('Achat')),
        ('retention', _('Fidélisation'))
    ], default='awareness', verbose_name=_('Étape du funnel'))
    device_type = models.CharField(max_length=20, choices=[
        ('desktop', _('Ordinateur')),
        ('mobile', _('Mobile')),
        ('tablet', _('Tablette'))
    ], default='desktop')
    location_data = models.JSONField(default=dict, verbose_name=_('Données de localisation'))
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = _('Comportement client')
        verbose_name_plural = _('Comportements clients')
        ordering = ['-created_at']
    
    def __str__(self):
        return f"Comportement {self.user.username} - {self.session_id}"

class SalesPredict(models.Model):
    """Prédictions de ventes"""
    seller = models.ForeignKey(User, on_delete=models.CASCADE, related_name='sales_predictions')
    product = models.ForeignKey('products.Product', on_delete=models.CASCADE, null=True, blank=True)
    prediction_date = models.DateField(verbose_name=_('Date de prédiction'))
    predicted_sales_gnf = models.DecimalField(max_digits=12, decimal_places=0, verbose_name=_('Ventes prédites (GNF)'))
    predicted_quantity = models.IntegerField(verbose_name=_('Quantité prédite'))
    confidence_score = models.DecimalField(max_digits=3, decimal_places=2, verbose_name=_('Score de confiance'))
    factors_considered = models.JSONField(default=dict, verbose_name=_('Facteurs considérés'))
    actual_sales_gnf = models.DecimalField(max_digits=12, decimal_places=0, null=True, blank=True)
    actual_quantity = models.IntegerField(null=True, blank=True)
    accuracy_score = models.DecimalField(max_digits=3, decimal_places=2, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = _('Prédiction de ventes')
        verbose_name_plural = _('Prédictions de ventes')
        ordering = ['-created_at']
    
    def __str__(self):
        return f"Prédiction {self.seller.username} - {self.prediction_date}"

class SentimentAnalysis(models.Model):
    """Analyse de sentiment des avis"""
    review = models.OneToOneField('reviews.Review', on_delete=models.CASCADE, related_name='sentiment')
    sentiment_score = models.DecimalField(max_digits=3, decimal_places=2, verbose_name=_('Score de sentiment'))  # -1 à 1
    sentiment_label = models.CharField(max_length=20, choices=[
        ('very_negative', _('Très négatif')),
        ('negative', _('Négatif')),
        ('neutral', _('Neutre')),
        ('positive', _('Positif')),
        ('very_positive', _('Très positif'))
    ], verbose_name=_('Label de sentiment'))
    keywords = models.JSONField(default=list, verbose_name=_('Mots-clés'))
    emotions = models.JSONField(default=dict, verbose_name=_('Émotions détectées'))
    language_detected = models.CharField(max_length=10, default='fr', verbose_name=_('Langue détectée'))
    processed_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = _('Analyse de sentiment')
        verbose_name_plural = _('Analyses de sentiment')
    
    def __str__(self):
        return f"Sentiment {self.review.product.name} - {self.get_sentiment_label_display()}"

class FraudDetection(models.Model):
    """Détection de fraude"""
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='fraud_alerts')
    order = models.ForeignKey('orders.Order', on_delete=models.CASCADE, null=True, blank=True)
    fraud_type = models.CharField(max_length=30, choices=[
        ('suspicious_payment', _('Paiement suspect')),
        ('fake_review', _('Faux avis')),
        ('account_takeover', _('Piratage de compte')),
        ('price_manipulation', _('Manipulation de prix')),
        ('fake_location', _('Fausse localisation')),
        ('bot_activity', _('Activité de bot'))
    ], verbose_name=_('Type de fraude'))
    risk_score = models.DecimalField(max_digits=3, decimal_places=2, verbose_name=_('Score de risque'))  # 0-1
    details = models.JSONField(default=dict, verbose_name=_('Détails'))
    status = models.CharField(max_length=20, choices=[
        ('pending', _('En attente')),
        ('investigating', _('En cours d\'investigation')),
        ('confirmed', _('Confirmé')),
        ('false_positive', _('Faux positif')),
        ('resolved', _('Résolu'))
    ], default='pending')
    investigated_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='investigated_frauds')
    created_at = models.DateTimeField(auto_now_add=True)
    resolved_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        verbose_name = _('Détection de fraude')
        verbose_name_plural = _('Détections de fraude')
        ordering = ['-risk_score', '-created_at']