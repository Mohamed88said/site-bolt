from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from .models import Delivery, DeliveryRequest, DeliveryRating

@admin.register(Delivery)
class DeliveryAdmin(admin.ModelAdmin):
    list_display = ('tracking_number', 'order_link', 'delivery_person', 'status', 'delivery_cost', 'paid_by', 'created_at', 'actions')
    list_filter = ('status', 'paid_by', 'created_at', 'delivery_zone')
    search_fields = ('tracking_number', 'order__user__username', 'delivery_person__username', 'order__id')
    readonly_fields = ('tracking_number', 'created_at', 'updated_at')
    date_hierarchy = 'created_at'
    actions = ['assign_to_delivery_person', 'mark_as_in_progress', 'mark_as_completed']
    
    fieldsets = (
        ('Informations générales', {
            'fields': ('tracking_number', 'order', 'delivery_person', 'status')
        }),
        ('Localisation', {
            'fields': ('location_point', 'delivery_zone')
        }),
        ('Coûts et paiement', {
            'fields': ('delivery_cost', 'paid_by')
        }),
        ('Informations vendeur', {
            'fields': ('seller_address', 'seller_phone', 'seller_instructions')
        }),
        ('Timing', {
            'fields': ('estimated_delivery_time', 'actual_delivery_time')
        }),
        ('Notes', {
            'fields': ('delivery_notes',)
        }),
        ('Dates', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def order_link(self, obj):
        url = reverse('admin:orders_order_change', args=[obj.order.id])
        return format_html('<a href="{}">{}</a>', url, obj.order)
    order_link.short_description = "Commande"
    
    def actions(self, obj):
        links = []
        if obj.order and hasattr(obj.order, 'payment'):
            payment_url = reverse('admin:payments_payment_change', args=[obj.order.payment.id])
            links.append(f'<a href="{payment_url}">Paiement</a>')
        return format_html(' | '.join(links)) if links else '-'
    actions.short_description = "Actions"
    
    def assign_to_delivery_person(self, request, queryset):
        # Cette action nécessiterait une interface pour choisir le livreur
        self.message_user(request, "Utilisez l'interface de gestion pour assigner des livreurs.")
    assign_to_delivery_person.short_description = "Assigner à un livreur"
    
    def mark_as_in_progress(self, request, queryset):
        updated = queryset.filter(status='assigned').update(status='in_progress')
        self.message_user(request, f'{updated} livraison(s) marquée(s) en cours.')
    mark_as_in_progress.short_description = "Marquer comme en cours"
    
    def mark_as_completed(self, request, queryset):
        from django.utils import timezone
        updated = 0
        for delivery in queryset.filter(status='in_progress'):
            delivery.status = 'completed'
            delivery.actual_delivery_time = timezone.now()
            delivery.save()
            # Mettre à jour la commande
            delivery.order.status = 'delivered'
            delivery.order.save()
            updated += 1
        self.message_user(request, f'{updated} livraison(s) marquée(s) comme terminée(s).')
    mark_as_completed.short_description = "Marquer comme terminées"

@admin.register(DeliveryRequest)
class DeliveryRequestAdmin(admin.ModelAdmin):
    list_display = ('delivery', 'delivery_person', 'proposed_cost', 'is_accepted', 'created_at')
    list_filter = ('is_accepted', 'created_at')
    search_fields = ('delivery__tracking_number', 'delivery_person__username')
    actions = ['accept_requests', 'reject_requests']
    
    def accept_requests(self, request, queryset):
        for req in queryset.filter(is_accepted=False):
            req.is_accepted = True
            req.save()
            # Assigner le livreur à la livraison
            delivery = req.delivery
            delivery.delivery_person = req.delivery_person
            delivery.delivery_cost = req.proposed_cost
            delivery.status = 'assigned'
            delivery.save()
            # Supprimer les autres demandes
            DeliveryRequest.objects.filter(delivery=delivery).exclude(id=req.id).delete()
        self.message_user(request, f'{queryset.count()} demande(s) acceptée(s).')
    accept_requests.short_description = "Accepter les demandes sélectionnées"
    
    def reject_requests(self, request, queryset):
        deleted = queryset.delete()[0]
        self.message_user(request, f'{deleted} demande(s) supprimée(s).')
    reject_requests.short_description = "Supprimer les demandes sélectionnées"

@admin.register(DeliveryRating)
class DeliveryRatingAdmin(admin.ModelAdmin):
    list_display = ('delivery', 'rating', 'created_by', 'created_at')
    list_filter = ('rating', 'created_at')
    search_fields = ('delivery__tracking_number', 'created_by__username')
    readonly_fields = ('created_at',)