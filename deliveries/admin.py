from django.contrib import admin
from .models import Delivery, DeliveryRequest, DeliveryRating, DeliveryPerson

@admin.register(DeliveryPerson)
class DeliveryPersonAdmin(admin.ModelAdmin):
    list_display = ('user', 'phone_number', 'availability_status', 'created_at')
    list_filter = ('availability_status', 'created_at')
    search_fields = ('user__username', 'phone_number')
    readonly_fields = ('created_at', 'updated_at')

@admin.register(Delivery)
class DeliveryAdmin(admin.ModelAdmin):
    list_display = ('tracking_number', 'order', 'delivery_person', 'status', 'delivery_cost', 'paid_by', 'created_at')
    list_filter = ('status', 'paid_by', 'created_at')
    search_fields = ('tracking_number', 'order__user__username', 'delivery_person__username')
    readonly_fields = ('tracking_number', 'created_at', 'updated_at')

@admin.register(DeliveryRequest)
class DeliveryRequestAdmin(admin.ModelAdmin):
    list_display = ('delivery', 'delivery_person', 'proposed_cost', 'is_accepted', 'created_at')
    list_filter = ('is_accepted', 'created_at')
    search_fields = ('delivery__tracking_number', 'delivery_person__username')

@admin.register(DeliveryRating)
class DeliveryRatingAdmin(admin.ModelAdmin):
    list_display = ('delivery', 'rating', 'created_by', 'created_at')
    list_filter = ('rating', 'created_at')
    search_fields = ('delivery__tracking_number', 'created_by__username')