from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from .models import Payment, PaymentDispute

@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = ('payment_id', 'order_link', 'payment_method', 'amount', 'status', 'confirmation_code', 'created_at', 'qr_code_preview')
    list_filter = ('payment_method', 'status', 'created_at')
    search_fields = ('order__user__username', 'order__id', 'confirmation_code', 'id')
    readonly_fields = ('id', 'confirmation_code', 'qr_code_image', 'created_at', 'confirmed_at', 'qr_code_preview')
    actions = ['mark_as_completed', 'mark_as_failed', 'regenerate_qr_codes']
    
    fieldsets = (
        ('Informations générales', {
            'fields': ('id', 'order', 'payment_method', 'amount', 'status')
        }),
        ('Confirmation', {
            'fields': ('confirmation_code', 'confirmation_attempts', 'qr_code_expires_at')
        }),
        ('QR Code', {
            'fields': ('qr_code_image', 'qr_code_preview')
        }),
        ('Processeurs externes', {
            'fields': ('stripe_payment_intent_id', 'paypal_order_id', 'mobile_money_transaction_id', 
                      'mobile_money_provider', 'mobile_money_phone'),
            'classes': ('collapse',)
        }),
        ('Dates', {
            'fields': ('created_at', 'confirmed_at')
        }),
    )
    
    def payment_id(self, obj):
        return str(obj.id)[:8]
    payment_id.short_description = "ID Paiement"
    
    def order_link(self, obj):
        url = reverse('admin:orders_order_change', args=[obj.order.id])
        return format_html('<a href="{}">{}</a>', url, obj.order)
    order_link.short_description = "Commande"
    
    def qr_code_preview(self, obj):
        if obj.qr_code_image:
            return format_html('<img src="{}" style="width: 100px; height: 100px;" />', obj.qr_code_image.url)
        return "Pas de QR code"
    qr_code_preview.short_description = "Aperçu QR Code"
    
    def mark_as_completed(self, request, queryset):
        from django.utils import timezone
        updated = 0
        for payment in queryset.filter(status='pending'):
            payment.status = 'completed'
            payment.confirmed_at = timezone.now()
            payment.save()
            # Mettre à jour la commande
            payment.order.payment_status = 'completed'
            payment.order.save()
            updated += 1
        self.message_user(request, f'{updated} paiement(s) marqué(s) comme terminé(s).')
    mark_as_completed.short_description = "Marquer comme terminés"
    
    def mark_as_failed(self, request, queryset):
        updated = queryset.update(status='failed')
        self.message_user(request, f'{updated} paiement(s) marqué(s) comme échoué(s).')
    mark_as_failed.short_description = "Marquer comme échoués"
    
    def regenerate_qr_codes(self, request, queryset):
        updated = 0
        for payment in queryset:
            payment.qr_code_image.delete()
            payment.generate_qr_code_image()
            payment.save()
            updated += 1
        self.message_user(request, f'{updated} QR code(s) régénéré(s).')
    regenerate_qr_codes.short_description = "Régénérer les QR codes"

@admin.register(PaymentDispute)
class PaymentDisputeAdmin(admin.ModelAdmin):
    list_display = ('payment', 'user', 'status', 'created_at', 'resolved_at')
    list_filter = ('status', 'created_at')
    search_fields = ('payment__order__user__username', 'user__username', 'reason')
    readonly_fields = ('created_at',)
    actions = ['resolve_disputes', 'reject_disputes']
    
    def resolve_disputes(self, request, queryset):
        from django.utils import timezone
        updated = queryset.filter(status='pending').update(status='resolved', resolved_at=timezone.now())
        self.message_user(request, f'{updated} litige(s) résolu(s).')
    resolve_disputes.short_description = "Résoudre les litiges sélectionnés"
    
    def reject_disputes(self, request, queryset):
        from django.utils import timezone
        updated = queryset.filter(status='pending').update(status='rejected', resolved_at=timezone.now())
        self.message_user(request, f'{updated} litige(s) rejeté(s).')
    reject_disputes.short_description = "Rejeter les litiges sélectionnés"