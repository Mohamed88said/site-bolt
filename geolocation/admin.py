from django.contrib import admin
from django.utils.html import format_html
from .models import (
    GuineaRegion, GuineaPrefecture, GuineaCommune, 
    LocationPoint, UserLocation, LocationVerification, DeliveryZone
)

@admin.register(GuineaRegion)
class GuineaRegionAdmin(admin.ModelAdmin):
    list_display = ('name', 'code', 'prefecture_count', 'is_active')
    list_filter = ('is_active',)
    search_fields = ('name', 'code')
    actions = ['activate_regions', 'deactivate_regions']
    
    def prefecture_count(self, obj):
        return obj.prefectures.count()
    prefecture_count.short_description = "Préfectures"
    
    def activate_regions(self, request, queryset):
        updated = queryset.update(is_active=True)
        self.message_user(request, f'{updated} région(s) activée(s).')
    activate_regions.short_description = "Activer les régions sélectionnées"
    
    def deactivate_regions(self, request, queryset):
        updated = queryset.update(is_active=False)
        self.message_user(request, f'{updated} région(s) désactivée(s).')
    deactivate_regions.short_description = "Désactiver les régions sélectionnées"

@admin.register(GuineaPrefecture)
class GuineaPrefectureAdmin(admin.ModelAdmin):
    list_display = ('name', 'region', 'code', 'commune_count', 'is_active')
    list_filter = ('region', 'is_active')
    search_fields = ('name', 'code')
    
    def commune_count(self, obj):
        return obj.communes.count()
    commune_count.short_description = "Communes"

@admin.register(GuineaCommune)
class GuineaCommuneAdmin(admin.ModelAdmin):
    list_display = ('name', 'prefecture', 'region_name', 'code', 'is_active')
    list_filter = ('prefecture__region', 'prefecture', 'is_active')
    search_fields = ('name', 'code')
    
    def region_name(self, obj):
        return obj.prefecture.region.name
    region_name.short_description = "Région"

@admin.register(LocationPoint)
class LocationPointAdmin(admin.ModelAdmin):
    list_display = ('name', 'region', 'prefecture', 'commune', 'verified_by_locals', 'verification_count', 'is_active', 'created_at')
    list_filter = ('region', 'prefecture', 'verified_by_locals', 'is_active', 'created_at')
    search_fields = ('name', 'description', 'landmark', 'address')
    readonly_fields = ('verification_count', 'created_at', 'updated_at', 'google_maps_link')
    actions = ['verify_locations', 'activate_locations']
    
    fieldsets = (
        ('Informations générales', {
            'fields': ('name', 'description', 'user')
        }),
        ('Coordonnées GPS', {
            'fields': ('latitude', 'longitude', 'google_maps_link')
        }),
        ('Division administrative', {
            'fields': ('region', 'prefecture', 'commune')
        }),
        ('Adresse', {
            'fields': ('address', 'city', 'postal_code', 'country')
        }),
        ('Points de repère', {
            'fields': ('landmark', 'access_instructions')
        }),
        ('Vérification', {
            'fields': ('verified_by_locals', 'verification_count', 'is_active')
        }),
        ('Dates', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def google_maps_link(self, obj):
        if obj.latitude and obj.longitude:
            return format_html('<a href="{}" target="_blank">Voir sur Google Maps</a>', obj.google_maps_url)
        return "Coordonnées manquantes"
    google_maps_link.short_description = "Google Maps"
    
    def verify_locations(self, request, queryset):
        updated = queryset.update(verified_by_locals=True)
        self.message_user(request, f'{updated} localisation(s) vérifiée(s).')
    verify_locations.short_description = "Marquer comme vérifiées"
    
    def activate_locations(self, request, queryset):
        updated = queryset.update(is_active=True)
        self.message_user(request, f'{updated} localisation(s) activée(s).')
    activate_locations.short_description = "Activer les localisations sélectionnées"

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
    list_display = ('name', 'base_delivery_cost', 'cost_per_km', 'estimated_delivery_time', 'is_active')
    list_filter = ('is_active',)
    search_fields = ('name',)
    filter_horizontal = ('regions', 'prefectures', 'communes')
    actions = ['activate_zones', 'deactivate_zones']
    
    def activate_zones(self, request, queryset):
        updated = queryset.update(is_active=True)
        self.message_user(request, f'{updated} zone(s) activée(s).')
    activate_zones.short_description = "Activer les zones sélectionnées"
    
    def deactivate_zones(self, request, queryset):
        updated = queryset.update(is_active=False)
        self.message_user(request, f'{updated} zone(s) désactivée(s).')
    deactivate_zones.short_description = "Désactiver les zones sélectionnées"