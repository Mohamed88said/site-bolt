from django.db import models
from django.contrib.auth import get_user_model
from products.models import Product
from orders.models import Order
from django.utils.translation import gettext_lazy as _

User = get_user_model()

class Review(models.Model):
    RATING_CHOICES = [
        (1, '1 étoile'),
        (2, '2 étoiles'),
        (3, '3 étoiles'),
        (4, '4 étoiles'),
        (5, '5 étoiles'),
    ]
    
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='review_app_reviews')
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='review_app_user_reviews')
    order = models.ForeignKey(Order, on_delete=models.SET_NULL, null=True, blank=True)
    rating = models.IntegerField(choices=RATING_CHOICES, verbose_name=_('Note'))
    title = models.CharField(max_length=200, blank=True, verbose_name=_('Titre'))
    comment = models.TextField(blank=True, verbose_name=_('Commentaire'))
    is_verified = models.BooleanField(default=False, verbose_name=_('Achat vérifié'))
    is_approved = models.BooleanField(default=True, verbose_name=_('Approuvé'))
    helpful_count = models.IntegerField(default=0, verbose_name=_('Votes utiles'))
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_active = models.BooleanField(default=True)  # Ajouté
    
    class Meta:
        verbose_name = _('Avis')
        verbose_name_plural = _('Avis')
        unique_together = ['product', 'user']
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.product.name} - {self.rating} étoiles par {self.user.username}"

class ReviewHelpful(models.Model):
    review = models.ForeignKey(Review, on_delete=models.CASCADE, related_name='helpful_votes')
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    is_helpful = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = ['review', 'user']
    
    def __str__(self):
        return f"{self.user.username} - {self.review}"

class ReviewResponse(models.Model):
    review = models.OneToOneField(Review, on_delete=models.CASCADE, related_name='response')
    seller = models.ForeignKey(User, on_delete=models.CASCADE, limit_choices_to={'user_type': 'seller'})
    response = models.TextField(verbose_name=_('Réponse'))
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = _('Réponse à un avis')
        verbose_name_plural = _('Réponses aux avis')
    
    def __str__(self):
        return f"Réponse à {self.review}"