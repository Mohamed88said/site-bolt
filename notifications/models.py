from django.db import models
from django.contrib.auth import get_user_model
from django.utils.translation import gettext_lazy as _

User = get_user_model()

class Notification(models.Model):
    NOTIFICATION_TYPES = [
        ('order_placed', _('Commande passée')),
        ('order_confirmed', _('Commande confirmée')),
        ('order_shipped', _('Commande expédiée')),
        ('order_delivered', _('Commande livrée')),
        ('order_cancelled', _('Commande annulée')),
        ('payment_received', _('Paiement reçu')),
        ('product_low_stock', _('Stock faible')),
        ('new_review', _('Nouvel avis')),
        ('delivery_request', _('Demande de livraison')),
        ('delivery_accepted', _('Livraison acceptée')),
        ('promotion', _('Promotion')),
        ('system', _('Système')),
    ]
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='notifications')
    title = models.CharField(max_length=200, verbose_name=_('Titre'))
    message = models.TextField(verbose_name=_('Message'))
    notification_type = models.CharField(max_length=20, choices=NOTIFICATION_TYPES, verbose_name=_('Type'))
    is_read = models.BooleanField(default=False, verbose_name=_('Lu'))
    url = models.URLField(blank=True, verbose_name=_('Lien'))
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = _('Notification')
        verbose_name_plural = _('Notifications')
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.title} - {self.user.username}"
    
    def mark_as_read(self):
        self.is_read = True
        self.save()