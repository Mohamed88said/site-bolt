from django.contrib import admin
from .models import ProductView, SearchQuery, SalesAnalytics

@admin.register(ProductView)
class ProductViewAdmin(admin.ModelAdmin):
    list_display = ('product', 'user', 'ip_address', 'created_at')
    list_filter = ('created_at',)
    search_fields = ('product__name', 'user__username', 'ip_address')

@admin.register(SearchQuery)
class SearchQueryAdmin(admin.ModelAdmin):
    list_display = ('query', 'user', 'results_count', 'created_at')
    list_filter = ('created_at',)
    search_fields = ('query', 'user__username')

@admin.register(SalesAnalytics)
class SalesAnalyticsAdmin(admin.ModelAdmin):
    list_display = ('seller', 'date', 'total_sales', 'total_orders', 'average_order_value')
    list_filter = ('date',)
    search_fields = ('seller__username',)