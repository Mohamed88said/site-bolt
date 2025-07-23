from django.db import models
from django.contrib.auth import get_user_model
from django.core.validators import MinValueValidator, MaxValueValidator
from django.utils.translation import gettext_lazy as _
from django.utils import timezone

User = get_user_model()

class Coupon(models.Model):
    DISCOUNT_TYPES = [
        ('percentage', _('Pourcentage')),
        ('fixed', _('Montant fixe')),
    ]
    
    code = models.CharField(max_length=50, unique=True, verbose_name=_('Code'))
    discount_type = models.CharField(max_length=20, choices=DISCOUNT_TYPES, verbose_name=_('Type de remise'))
    discount_value = models.DecimalField(max_digits=10, decimal_places=2, verbose_name=_('Valeur de remise'))
    minimum_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0, verbose_name=_('Montant minimum'))
    maximum_discount = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True, verbose_name=_('Remise maximum'))
    usage_limit = models.IntegerField(null=True, blank=True, verbose_name=_('Limite d\'utilisation'))
    used_count = models.IntegerField(default=0, verbose_name=_('Nombre d\'utilisations'))
    valid_from = models.DateTimeField(verbose_name=_('Valide à partir de'))
    valid_to = models.DateTimeField(verbose_name=_('Valide jusqu\'à'))
    is_active = models.BooleanField(default=True, verbose_name=_('Actif'))
    created_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='created_coupons')
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = _('Coupon')
        verbose_name_plural = _('Coupons')
    
    def __str__(self):
        return self.code
    
    def is_valid(self):
        now = timezone.now()
        return (
            self.is_active and
            self.valid_from <= now <= self.valid_to and
            (self.usage_limit is None or self.used_count < self.usage_limit)
        )
    
    def calculate_discount(self, amount):
        if not self.is_valid() or amount < self.minimum_amount:
            return 0
        
        if self.discount_type == 'percentage':
            discount = amount * (self.discount_value / 100)
            if self.maximum_discount:
                discount = min(discount, self.maximum_discount)
        else:
            discount = self.discount_value
        
        return min(discount, amount)

class CouponUsage(models.Model):
    coupon = models.ForeignKey(Coupon, on_delete=models.CASCADE, related_name='usages')
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    order = models.ForeignKey('orders.Order', on_delete=models.CASCADE)
    discount_amount = models.DecimalField(max_digits=10, decimal_places=2)
    used_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = _('Utilisation de coupon')
        verbose_name_plural = _('Utilisations de coupons')
    
    def __str__(self):
        return f"{self.coupon.code} - {self.user.username}"