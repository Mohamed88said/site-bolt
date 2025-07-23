from django.contrib import admin
from .models import (
    GuineaRegion, GuineaPrefecture, GuineaCommune, 
    LocationPoint, UserLocation, LocationVerification, DeliveryZone
)

@admin.register(GuineaRegion)
class GuineaRegionAdmin(admin.ModelAdmin):
    list_display = ('name', 'code', 'is_active')
    list_filter = ('is_active',)
    search_fields = ('name', 'code')

@admin.register(GuineaPrefecture)
class GuineaPrefectureAdmin(admin.ModelAdmin):
    list_display = ('name', 'region', 'code', 'is_active')
    list_filter = ('region', 'is_active')
    search_fields = ('name', 'code')

@admin.register(GuineaCommune)
class GuineaCommuneAdmin(admin.ModelAdmin):
    list_display = ('name', 'prefecture', 'code', 'is_active')
    list_filter = ('prefecture__region', 'prefecture', 'is_active')
    search_fields = ('name', 'code')

@admin.register(LocationPoint)
class LocationPointAdmin(admin.ModelAdmin):
    list_display = ('name', 'region', 'prefecture', 'commune', 'verified_by_locals', 'verification_count', 'is_active')
    list_filter = ('region', 'prefecture', 'verified_by_locals', 'is_active')
    search_fields = ('name', 'description', 'landmark')
    readonly_fields = ('verification_count', 'created_at', 'updated_at')

@admin.register(UserLocation)
class UserLocationAdmin(admin.ModelAdmin):
    list_display = ('user', 'location_point', 'is_primary', 'label', 'created_at')
    list_filter = ('is_primary', 'created_at')
    search_fields = ('user__username', 'location_point__name', 'label')

@admin.register(LocationVerification)
class LocationVerificationAdmin(admin.ModelAdmin):
    list_display = ('location_point', 'verified_by', 'is_accurate', 'created_at')
    list_filter = ('is_accurate', 'created_at')
    search_fields = ('location_point__name', 'verified_by__username')

@admin.register(DeliveryZone)
class DeliveryZoneAdmin(admin.ModelAdmin):
    list_display = ('name', 'base_delivery_cost', 'estimated_delivery_days', 'is_active')
    list_filter = ('is_active',)
    search_fields = ('name',)
    filter_horizontal = ('regions', 'prefectures', 'communes')