from django.contrib import admin
from django.utils.html import format_html
from .models import Notification

@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = ('title', 'user', 'notification_type', 'is_read', 'created_at', 'url_link')
    list_filter = ('notification_type', 'is_read', 'created_at')
    search_fields = ('title', 'message', 'user__username')
    readonly_fields = ('created_at',)
    actions = ['mark_as_read', 'mark_as_unread', 'delete_old_notifications']
    date_hierarchy = 'created_at'
    
    def url_link(self, obj):
        if obj.url:
            return format_html('<a href="{}" target="_blank">Voir</a>', obj.url)
        return '-'
    url_link.short_description = "Lien"
    
    def mark_as_read(self, request, queryset):
        updated = queryset.update(is_read=True)
        self.message_user(request, f'{updated} notification(s) marquée(s) comme lue(s).')
    mark_as_read.short_description = "Marquer comme lues"
    
    def mark_as_unread(self, request, queryset):
        updated = queryset.update(is_read=False)
        self.message_user(request, f'{updated} notification(s) marquée(s) comme non lue(s).')
    mark_as_unread.short_description = "Marquer comme non lues"
    
    def delete_old_notifications(self, request, queryset):
        from django.utils import timezone
        from datetime import timedelta
        
        old_date = timezone.now() - timedelta(days=30)
        deleted = queryset.filter(created_at__lt=old_date, is_read=True).delete()[0]
        self.message_user(request, f'{deleted} ancienne(s) notification(s) supprimée(s).')
    delete_old_notifications.short_description = "Supprimer les anciennes notifications lues"