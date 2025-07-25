from django.contrib import admin
from django.utils.html import format_html
from .models import Category, Product, ProductImage, ProductVariant

class ProductImageInline(admin.TabularInline):
    model = ProductImage
    extra = 1
    readonly_fields = ('image_preview',)
    
    def image_preview(self, obj):
        if obj.image:
            return format_html('<img src="{}" style="width: 50px; height: 50px; object-fit: cover;" />', obj.image.url)
        return "Pas d'image"
    image_preview.short_description = "Aperçu"

class ProductVariantInline(admin.TabularInline):
    model = ProductVariant
    extra = 1

@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'parent', 'is_active', 'product_count', 'created_at')
    list_filter = ('is_active', 'parent', 'created_at')
    search_fields = ('name', 'description')
    prepopulated_fields = {'slug': ('name',)}
    
    def product_count(self, obj):
        return obj.products.filter(is_active=True).count()
    product_count.short_description = "Produits actifs"

@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ('name', 'seller', 'category', 'current_price', 'stock', 'is_active', 'is_featured', 'rating', 'created_at')
    list_filter = ('category', 'is_active', 'is_featured', 'seller_pays_delivery', 'created_at', 'seller')
    search_fields = ('name', 'description', 'sku', 'seller__username')
    prepopulated_fields = {'slug': ('name',)}
    inlines = [ProductImageInline, ProductVariantInline]
    readonly_fields = ('views', 'rating', 'created_at', 'updated_at')
    actions = ['activate_products', 'deactivate_products', 'feature_products']
    
    fieldsets = (
        ('Informations générales', {
            'fields': ('name', 'slug', 'seller', 'category', 'description', 'short_description')
        }),
        ('Prix et stock', {
            'fields': ('price', 'discount_price', 'stock', 'sku', 'weight', 'dimensions')
        }),
        ('Livraison', {
            'fields': ('seller_pays_delivery', 'delivery_included_price')
        }),
        ('Options', {
            'fields': ('is_active', 'is_featured', 'stock_alert_threshold')
        }),
        ('Statistiques', {
            'fields': ('views', 'rating', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def current_price(self, obj):
        price = obj.discount_price if obj.discount_price else obj.price
        if obj.discount_price:
            return format_html('<span style="color: red; font-weight: bold;">{} GNF</span> <s>{} GNF</s>', 
                             obj.discount_price, obj.price)
        return f"{price} GNF"
    current_price.short_description = "Prix actuel"
    
    def activate_products(self, request, queryset):
        updated = queryset.update(is_active=True)
        self.message_user(request, f'{updated} produit(s) activé(s).')
    activate_products.short_description = "Activer les produits sélectionnés"
    
    def deactivate_products(self, request, queryset):
        updated = queryset.update(is_active=False)
        self.message_user(request, f'{updated} produit(s) désactivé(s).')
    deactivate_products.short_description = "Désactiver les produits sélectionnés"
    
    def feature_products(self, request, queryset):
        updated = queryset.update(is_featured=True)
        self.message_user(request, f'{updated} produit(s) mis en avant.')
    feature_products.short_description = "Mettre en avant les produits sélectionnés"

@admin.register(ProductImage)
class ProductImageAdmin(admin.ModelAdmin):
    list_display = ('product', 'is_main', 'order', 'image_preview', 'created_at')
    list_filter = ('is_main', 'created_at')
    search_fields = ('product__name', 'alt_text')
    
    def image_preview(self, obj):
        if obj.image:
            return format_html('<img src="{}" style="width: 50px; height: 50px; object-fit: cover;" />', obj.image.url)
        return "Pas d'image"
    image_preview.short_description = "Aperçu"

@admin.register(ProductVariant)
class ProductVariantAdmin(admin.ModelAdmin):
    list_display = ('product', 'name', 'value', 'price_adjustment', 'stock', 'created_at')
    list_filter = ('created_at',)
    search_fields = ('product__name', 'name', 'value', 'sku')