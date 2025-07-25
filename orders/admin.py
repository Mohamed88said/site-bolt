from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from .models import Order, OrderItem, OrderStatusHistory

class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 0
    readonly_fields = ('total_price',)

class OrderStatusHistoryInline(admin.TabularInline):
    model = OrderStatusHistory
    extra = 0
    readonly_fields = ('created_at',)

@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ('order_number', 'user', 'status', 'payment_status', 'total_with_shipping', 'created_at', 'actions')
    list_filter = ('status', 'payment_status', 'created_at', 'payment_method')
    search_fields = ('user__username', 'user__email', 'shipping_first_name', 'shipping_last_name', 'id')
    readonly_fields = ('id', 'created_at', 'updated_at', 'total_with_shipping')
    inlines = [OrderItemInline, OrderStatusHistoryInline]
    date_hierarchy = 'created_at'
    actions = ['mark_as_confirmed', 'mark_as_processing', 'mark_as_shipped']
    
    fieldsets = (
        ('Informations générales', {
            'fields': ('id', 'user', 'status', 'payment_status', 'payment_method', 'notes')
        }),
        ('Montants', {
            'fields': ('total_amount', 'shipping_cost', 'tax_amount', 'total_with_shipping')
        }),
        ('Adresse de livraison', {
            'fields': ('location_point', 'shipping_first_name', 'shipping_last_name', 
                      'shipping_address', 'shipping_city', 'shipping_postal_code', 
                      'shipping_country', 'shipping_phone')
        }),
        ('Adresse de facturation', {
            'fields': ('billing_first_name', 'billing_last_name', 'billing_address', 
                      'billing_city', 'billing_postal_code', 'billing_country'),
            'classes': ('collapse',)
        }),
        ('Dates', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def order_number(self, obj):
        return f"#{str(obj.id)[:8]}"
    order_number.short_description = "Numéro"
    
    def actions(self, obj):
        links = []
        if hasattr(obj, 'delivery'):
            delivery_url = reverse('admin:deliveries_delivery_change', args=[obj.delivery.id])
            links.append(f'<a href="{delivery_url}">Livraison</a>')
        if hasattr(obj, 'payment'):
            payment_url = reverse('admin:payments_payment_change', args=[obj.payment.id])
            links.append(f'<a href="{payment_url}">Paiement</a>')
        return format_html(' | '.join(links)) if links else '-'
    actions.short_description = "Actions"
    
    def mark_as_confirmed(self, request, queryset):
        updated = queryset.update(status='confirmed')
        self.message_user(request, f'{updated} commande(s) confirmée(s).')
    mark_as_confirmed.short_description = "Marquer comme confirmées"
    
    def mark_as_processing(self, request, queryset):
        updated = queryset.update(status='processing')
        self.message_user(request, f'{updated} commande(s) en traitement.')
    mark_as_processing.short_description = "Marquer comme en traitement"
    
    def mark_as_shipped(self, request, queryset):
        updated = queryset.update(status='shipped')
        self.message_user(request, f'{updated} commande(s) expédiée(s).')
    mark_as_shipped.short_description = "Marquer comme expédiées"

@admin.register(OrderItem)
class OrderItemAdmin(admin.ModelAdmin):
    list_display = ('order', 'product', 'quantity', 'price', 'total_price')
    list_filter = ('order__created_at', 'product__category')
    search_fields = ('product__name', 'order__user__username', 'order__id')

@admin.register(OrderStatusHistory)
class OrderStatusHistoryAdmin(admin.ModelAdmin):
    list_display = ('order', 'status', 'created_by', 'created_at')
    list_filter = ('status', 'created_at')
    search_fields = ('order__user__username', 'comment', 'order__id')