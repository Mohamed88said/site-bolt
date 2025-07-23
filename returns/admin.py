from django.contrib import admin
from .models import ReturnRequest, ReturnItem, ReturnShipping

class ReturnItemInline(admin.TabularInline):
    model = ReturnItem
    extra = 0

@admin.register(ReturnRequest)
class ReturnRequestAdmin(admin.ModelAdmin):
    list_display = ('id', 'order', 'user', 'status', 'reason', 'refund_amount', 'created_at')
    list_filter = ('status', 'reason', 'created_at')
    search_fields = ('order__id', 'user__username', 'description')
    readonly_fields = ('created_at', 'updated_at')
    inlines = [ReturnItemInline]

@admin.register(ReturnShipping)
class ReturnShippingAdmin(admin.ModelAdmin):
    list_display = ('return_request', 'tracking_number', 'pickup_date', 'delivered_date')
    list_filter = ('pickup_date', 'delivered_date')
    search_fields = ('return_request__id', 'tracking_number')