from django.conf import settings
from products.models import Category
from notifications.models import Notification

def site_settings(request):
    """Add site-wide context variables."""
    context = {
        'site_name': 'E-Commerce Pro',
        'site_description': 'Votre marketplace de confiance',
        'categories': Category.objects.filter(is_active=True, parent=None)[:8],
    }
    
    if request.user.is_authenticated:
        context['unread_notifications'] = Notification.objects.filter(
            user=request.user, 
            is_read=False
        ).count()
    
    return context