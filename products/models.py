from django.db import models
from django.utils.translation import gettext_lazy as _
from django.urls import reverse
from django.utils.text import slugify
from django.core.exceptions import ValidationError
from geolocation.models import DeliveryZone, GuineaCommune

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

    def clean(self):
        if self.parent and self.parent == self:
            raise ValidationError(_("Une catégorie ne peut pas être son propre parent"))
        
        if not self.slug:
            self.slug = slugify(self.name)
        
        # Vérification de l'unicité du slug
        qs = Category.objects.filter(slug=self.slug)
        if self.pk:
            qs = qs.exclude(pk=self.pk)
        if qs.exists():
            raise ValidationError(_("Un slug avec ce nom existe déjà"))

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)

class Product(models.Model):
    seller = models.ForeignKey('accounts.User', on_delete=models.CASCADE, related_name='products', 
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
    is_active = models.BooleanField(default=True, verbose_name=_('Actif'))
    is_featured = models.BooleanField(default=False, verbose_name=_('Mis en avant'))
    views = models.IntegerField(default=0, verbose_name=_('Vues'))
    rating = models.DecimalField(max_digits=3, decimal_places=2, default=0.00, verbose_name=_('Note'))
    stock_alert_threshold = models.IntegerField(default=5, verbose_name=_('Seuil d\'alerte stock'))
    seller_pays_delivery = models.BooleanField(default=False, verbose_name=_('Le vendeur prend en charge la livraison'))
    delivery_included_price = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True, verbose_name=_('Prix avec livraison incluse'))
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = _('Produit')
        verbose_name_plural = _('Produits')
        ordering = ['-created_at']
    
    def __str__(self):
        return self.name
    
    def clean(self):
        """Validation pour s'assurer que le slug est toujours valide."""
        if not self.slug:
            raise ValidationError(_("Le slug du produit ne peut pas être vide."))
        if not self.name:
            raise ValidationError(_("Le nom du produit ne peut pas être vide."))
        
        # Validation du prix
        if self.discount_price and self.discount_price >= self.price:
            raise ValidationError(_("Le prix réduit doit être inférieur au prix normal"))
    
    def save(self, *args, **kwargs):
        """Générer un slug unique si aucun slug n'est défini."""
        if not self.slug or self.slug == '':
            if not self.name:
                raise ValidationError(_("Le nom du produit est requis pour générer un slug."))
            base_slug = slugify(self.name)
            unique_slug = base_slug
            counter = 1
            while Product.objects.filter(slug=unique_slug).exclude(id=self.id).exists():
                unique_slug = f"{base_slug}-{counter}"
                counter += 1
            self.slug = unique_slug
        self.full_clean()  # Appelle la méthode clean pour valider
        super().save(*args, **kwargs)
    
    def get_absolute_url(self):
        if not self.slug:
            raise ValueError(f"Le produit '{self.name}' n'a pas de slug valide.")
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
        return self.is_active and self.seller.seller_profile.is_verified
    
    @property
    def is_low_stock(self):
        return self.stock <= self.stock_alert_threshold
    
    def is_available_in_zone(self, user_location):
        """Vérifie si le produit est livrable dans la zone de l'utilisateur."""
        if not user_location or not user_location.location_point.commune:
            return False
        seller_zones = self.seller.delivery_zones.filter(delivery_zone__is_active=True)
        if not seller_zones.exists():
            return False
        user_commune = GuineaCommune.objects.filter(id=user_location.location_point.commune.id).first()
        if not user_commune:
            return False
        for zone in seller_zones:
            if user_commune in zone.delivery_zone.communes.all():
                return True
        return False

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
        # S'assurer qu'il n'y a qu'une seule image principale
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
    
    @property
    def current_price(self):
        return self.product.current_price + self.price_adjustment

class Review(models.Model):
    RATING_CHOICES = [
        (1, '1 étoile'),
        (2, '2 étoiles'),
        (3, '3 étoiles'),
        (4, '4 étoiles'),
        (5, '5 étoiles'),
    ]
    
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='reviews')
    user = models.ForeignKey('accounts.User', on_delete=models.CASCADE, related_name='reviews')
    rating = models.IntegerField(choices=RATING_CHOICES, verbose_name=_('Note'))
    title = models.CharField(max_length=200, blank=True, verbose_name=_('Titre'))
    comment = models.TextField(blank=True, verbose_name=_('Commentaire'))
    is_verified = models.BooleanField(default=False, verbose_name=_('Achat vérifié'))
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_active = models.BooleanField(default=True, verbose_name=_('Actif'))
    
    class Meta:
        verbose_name = _('Avis')
        verbose_name_plural = _('Avis')
        unique_together = ['product', 'user']
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.product.name} - {self.rating} étoiles par {self.user.username}"
    
    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        # Mettre à jour la note moyenne du produit
        self.product.rating = self.product.reviews.aggregate(models.Avg('rating'))['rating__avg'] or 0
        self.product.save()