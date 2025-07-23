from django.db import models
from django.contrib.auth import get_user_model
from products.models import Product
from orders.models import Order
from django.utils.translation import gettext_lazy as _

User = get_user_model()

class ProductView(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='product_views')
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    ip_address = models.GenericIPAddressField()
    user_agent = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = _('Vue produit')
        verbose_name_plural = _('Vues produits')
    
    def __str__(self):
        return f"{self.product.name} - {self.created_at}"

class SearchQuery(models.Model):
    query = models.CharField(max_length=200)
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    results_count = models.IntegerField(default=0)
    ip_address = models.GenericIPAddressField()
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = _('Recherche')
        verbose_name_plural = _('Recherches')
    
    def __str__(self):
        return f"{self.query} - {self.results_count} résultats"

class SalesAnalytics(models.Model):
    seller = models.ForeignKey(User, on_delete=models.CASCADE, related_name='sales_analytics')
    date = models.DateField()
    total_sales = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    total_orders = models.IntegerField(default=0)
    total_products_sold = models.IntegerField(default=0)
    average_order_value = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    
    class Meta:
        verbose_name = _('Analytique vente')
        verbose_name_plural = _('Analytiques ventes')
        unique_together = ['seller', 'date']
    
    def __str__(self):
        return f"{self.seller.username} - {self.date}"