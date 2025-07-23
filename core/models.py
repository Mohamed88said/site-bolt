from django.db import models
from django.utils.translation import gettext_lazy as _

class FAQ(models.Model):
    CATEGORY_CHOICES = [
        ('general', _('Général')),
        ('account', _('Compte')),
        ('orders', _('Commandes')),
        ('payments', _('Paiements')),
        ('delivery', _('Livraison')),
        ('returns', _('Retours')),
        ('sellers', _('Vendeurs')),
    ]
    
    question = models.CharField(max_length=300, verbose_name=_('Question'))
    answer = models.TextField(verbose_name=_('Réponse'))
    category = models.CharField(max_length=20, choices=CATEGORY_CHOICES, verbose_name=_('Catégorie'))
    order = models.IntegerField(default=0, verbose_name=_('Ordre d\'affichage'))
    is_active = models.BooleanField(default=True, verbose_name=_('Actif'))
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = _('FAQ')
        verbose_name_plural = _('FAQ')
        ordering = ['category', 'order', 'question']
    
    def __str__(self):
        return self.question

class ContactMessage(models.Model):
    name = models.CharField(max_length=100, verbose_name=_('Nom'))
    email = models.EmailField(verbose_name=_('Email'))
    subject = models.CharField(max_length=200, verbose_name=_('Sujet'))
    message = models.TextField(verbose_name=_('Message'))
    is_read = models.BooleanField(default=False, verbose_name=_('Lu'))
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = _('Message de contact')
        verbose_name_plural = _('Messages de contact')
        ordering = ['-created_at']
    
    def __str__(self):
        return self.subject  # Correction : ajout du bloc indenté