from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.utils.translation import gettext_lazy as _
from .models import User, SellerProfile, DeliveryProfile

@admin.register(User)
class UserAdmin(BaseUserAdmin):
    fieldsets = (
        (None, {'fields': ('username', 'password')}),
        (_('Personal info'), {'fields': ('first_name', 'last_name', 'email', 'phone', 'birth_date', 'avatar')}),
        (_('Address'), {'fields': ('address', 'city', 'postal_code', 'country')}),
        (_('Permissions'), {'fields': ('user_type', 'is_active', 'is_verified', 'is_staff', 'is_superuser', 'groups', 'user_permissions')}),
        (_('Important dates'), {'fields': ('last_login', 'date_joined')}),
    )
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('username', 'email', 'user_type', 'password1', 'password2'),
        }),
    )
    list_display = ('username', 'email', 'user_type', 'is_active', 'is_verified', 'date_joined')
    list_filter = ('user_type', 'is_active', 'is_verified', 'date_joined')
    search_fields = ('username', 'email', 'first_name', 'last_name')
    ordering = ('-date_joined',)

@admin.register(SellerProfile)
class SellerProfileAdmin(admin.ModelAdmin):
    list_display = ('company_name', 'user', 'rating', 'total_sales', 'is_verified', 'created_at')
    list_filter = ('verification_status', 'created_at')  # Remplacement de 'is_verified' par 'verification_status'
    search_fields = ('company_name', 'user__username', 'user__email')
    readonly_fields = ('total_sales', 'rating')

@admin.register(DeliveryProfile)
class DeliveryProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'vehicle_type', 'is_available', 'rating', 'total_deliveries', 'created_at')
    list_filter = ('vehicle_type', 'is_available', 'created_at')
    search_fields = ('user__username', 'user__email', 'license_plate')
    readonly_fields = ('total_deliveries', 'rating')