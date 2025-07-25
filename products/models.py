from django.db import models
from django.utils.translation import gettext_lazy as _
from django.urls import reverse
from django.utils.text import slugify
from django.contrib.auth import get_user_model
from django.db.models import Avg

User = get_user_model()

class Category(models.Model):
    name = models.CharField(max_length=100, verbose_name=_('Nom'))
    slug = models.SlugField(unique=True, verbose_name=_('Slug'))
    description = models.TextField(blank=True, verbose_name=_('Description'))
    image = models.ImageField(upload_to='categories/', blank=True, verbose_name=_('Image'))
    parent = models.ForeignKey('self', on_delete=models.CASCADE, null=True, blank=True, 
                             verbose_name=_('Catégorie parent'))
    is_active = models.BooleanField(default=True, verbose_name=_('Actif'))
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = _('Catégorie')
        verbose_name_plural = _('Catégories')
        ordering = ['name']
    
    def __str__(self):
        return self.name
    
    def get_absolute_url(self):
        return reverse('products:category', kwargs={'slug': self.slug})

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)

class Product(models.Model):
    seller = models.ForeignKey(User, on_delete=models.CASCADE, related_name='products', 
                             limit_choices_to={'user_type': 'seller'})
    name = models.CharField(max_length=200, verbose_name=_('Nom'))
    slug = models.SlugField(unique=True, verbose_name=_('Slug'))
    description = models.TextField(verbose_name=_('Description'))
    short_description = models.TextField(max_length=300, blank=True, verbose_name=_('Description courte'))
    category = models.ForeignKey(Category, on_delete=models.CASCADE, related_name='products', 
                               verbose_name=_('Catégorie'))
    price = models.DecimalField(max_digits=10, decimal_places=2, verbose_name=_('Prix'))
    discount_price = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True, 
                                       verbose_name=_('Prix réduit'))
    stock = models.IntegerField(default=0, verbose_name=_('Stock'))
    sku = models.CharField(max_length=100, unique=True, verbose_name=_('SKU'))
    weight = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True, 
                               verbose_name=_('Poids (kg)'))
    dimensions = models.CharField(max_length=100, blank=True, verbose_name=_('Dimensions'))
    
    # Gestion des frais de livraison
    seller_pays_delivery = models.BooleanField(default=False, verbose_name=_('Le vendeur prend en charge la livraison'))
    delivery_included_price = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True, 
                                                verbose_name=_('Prix avec livraison incluse'))
    
    is_active = models.BooleanField(default=True, verbose_name=_('Actif'))
    is_featured = models.BooleanField(default=False, verbose_name=_('Mis en avant'))
    views = models.IntegerField(default=0, verbose_name=_('Vues'))
    rating = models.DecimalField(max_digits=3, decimal_places=2, default=0.00, verbose_name=_('Note'))
    stock_alert_threshold = models.IntegerField(default=5, verbose_name=_('Seuil d\'alerte stock'))
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = _('Produit')
        verbose_name_plural = _('Produits')
        ordering = ['-created_at']
    
    def __str__(self):
        return self.name
    
    def save(self, *args, **kwargs):
        if not self.slug:
            base_slug = slugify(self.name)
            unique_slug = base_slug
            counter = 1
            while Product.objects.filter(slug=unique_slug).exclude(id=self.id).exists():
                unique_slug = f"{base_slug}-{counter}"
                counter += 1
            self.slug = unique_slug
        
        # Calculer la note moyenne
        if self.pk:
            avg_rating = self.reviews.aggregate(avg=models.Avg('rating'))['avg']
            self.rating = avg_rating or 0.00
        
        super().save(*args, **kwargs)
    
    def get_absolute_url(self):
        return reverse('products:detail', kwargs={'slug': self.slug})
    
    @property
    def current_price(self):
        return self.discount_price if self.discount_price else self.price
    
    @property
    def discount_percentage(self):
        if self.discount_price and self.price > 0:
            return round(((self.price - self.discount_price) / self.price) * 100)
        return 0
    
    @property
    def is_in_stock(self):
        return self.stock > 0
    
    @property
    def main_image(self):
        return self.images.filter(is_main=True).first() or self.images.first()
    
    @property
    def is_visible(self):
        return self.is_active and hasattr(self.seller, 'seller_profile') and self.seller.seller_profile.is_verified

class ProductImage(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='images')
    image = models.ImageField(upload_to='products/', verbose_name=_('Image'))
    alt_text = models.CharField(max_length=200, blank=True, verbose_name=_('Texte alternatif'))
    is_main = models.BooleanField(default=False, verbose_name=_('Image principale'))
    order = models.IntegerField(default=0, verbose_name=_('Ordre'))
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = _('Image de produit')
        verbose_name_plural = _('Images de produits')
        ordering = ['order']
    
    def __str__(self):
        return f"{self.product.name} - Image {self.order}"
    
    def save(self, *args, **kwargs):
        if self.is_main:
            ProductImage.objects.filter(product=self.product).exclude(pk=self.pk).update(is_main=False)
        super().save(*args, **kwargs)

class ProductVariant(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='variants')
    name = models.CharField(max_length=100, verbose_name=_('Nom'))
    value = models.CharField(max_length=100, verbose_name=_('Valeur'))
    price_adjustment = models.DecimalField(max_digits=10, decimal_places=2, default=0.00, 
                                         verbose_name=_('Ajustement de prix'))
    stock = models.IntegerField(default=0, verbose_name=_('Stock'))
    sku = models.CharField(max_length=100, unique=True, verbose_name=_('SKU'))
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = _('Variante de produit')
        verbose_name_plural = _('Variantes de produits')
        unique_together = ['product', 'name', 'value']
    
    def __str__(self):
        return f"{self.product.name} - {self.name}: {self.value}"