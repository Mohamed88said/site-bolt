from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.utils.translation import gettext_lazy as _
from .models import User, SellerProfile, DeliveryProfile, SellerDeliveryZone

@admin.register(User)
class UserAdmin(BaseUserAdmin):
    fieldsets = (
        (None, {'fields': ('username', 'password')}),
        (_('Personal info'), {'fields': ('first_name', 'last_name', 'email', 'phone', 'birth_date', 'avatar')}),
        (_('Address'), {'fields': ('address', 'city', 'postal_code', 'country')}),
        (_('Permissions'), {'fields': ('user_type', 'is_active', 'is_verified', 'is_staff', 'is_superuser', 'groups', 'user_permissions')}),
        (_('Important dates'), {'fields': ('last_login', 'date_joined')}),
        (_('Subscription'), {'fields': ('subscription_type', 'subscription_expires_at', 'subscription_auto_renew')}),
    )
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('username', 'email', 'user_type', 'password1', 'password2'),
        }),
    )
    list_display = ('username', 'email', 'user_type', 'is_active', 'is_verified', 'date_joined')
    list_filter = ('user_type', 'is_active', 'is_verified', 'subscription_type', 'date_joined')
    search_fields = ('username', 'email', 'first_name', 'last_name')
    ordering = ('-date_joined',)

@admin.register(SellerProfile)
class SellerProfileAdmin(admin.ModelAdmin):
    list_display = ('company_name', 'user', 'rating', 'total_sales', 'verification_status', 'created_at')
    list_filter = ('verification_status', 'created_at', 'accepts_cash_on_delivery')
    search_fields = ('company_name', 'user__username', 'user__email')
    readonly_fields = ('total_sales', 'rating', 'created_at')
    actions = ['approve_sellers', 'reject_sellers']
    
    def approve_sellers(self, request, queryset):
        updated = queryset.update(verification_status='approved', verified_by=request.user, verified_at=timezone.now())
        self.message_user(request, f'{updated} vendeur(s) approuvé(s).')
    approve_sellers.short_description = "Approuver les vendeurs sélectionnés"
    
    def reject_sellers(self, request, queryset):
        updated = queryset.update(verification_status='rejected')
        self.message_user(request, f'{updated} vendeur(s) rejeté(s).')
    reject_sellers.short_description = "Rejeter les vendeurs sélectionnés"

@admin.register(DeliveryProfile)
class DeliveryProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'vehicle_type', 'is_available', 'rating', 'total_deliveries', 'verification_status', 'created_at')
    list_filter = ('vehicle_type', 'is_available', 'verification_status', 'created_at')
    search_fields = ('user__username', 'user__email', 'license_plate')
    readonly_fields = ('total_deliveries', 'rating', 'created_at')
    actions = ['approve_deliverers', 'reject_deliverers']
    
    def approve_deliverers(self, request, queryset):
        updated = queryset.update(verification_status='approved', verified_by=request.user, verified_at=timezone.now())
        self.message_user(request, f'{updated} livreur(s) approuvé(s).')
    approve_deliverers.short_description = "Approuver les livreurs sélectionnés"
    
    def reject_deliverers(self, request, queryset):
        updated = queryset.update(verification_status='rejected')
        self.message_user(request, f'{updated} livreur(s) rejeté(s).')
    reject_deliverers.short_description = "Rejeter les livreurs sélectionnés"

@admin.register(SellerDeliveryZone)
class SellerDeliveryZoneAdmin(admin.ModelAdmin):
    list_display = ('seller', 'delivery_zone', 'created_at')
    list_filter = ('delivery_zone', 'created_at')
    search_fields = ('seller__username', 'delivery_zone__name')