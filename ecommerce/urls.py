# ecommerce/urls.py
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('core.urls')),
    path('api/', include('api.urls')),
    path('accounts/', include('accounts.urls')),
    path('products/', include('products.urls')),
    path('orders/', include('orders.urls')),
    path('deliveries/', include('deliveries.urls')),
    path('favorites/', include('favorites.urls')),
    path('cart/', include('cart.urls')),
    path('notifications/', include('notifications.urls')),
    path('messaging/', include('messaging.urls')),
    path('returns/', include('returns.urls')),
    path('payments/', include('payments.urls')),
    path('geolocation/', include('geolocation.urls')),
    path('analytics/', include('analytics.urls')),
]

# Serve media files in development
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)

handler404 = 'core.views.handler404'
handler500 = 'core.views.handler500'

# Admin site customization
admin.site.site_header = "Administration E-Commerce"
admin.site.site_title = "E-Commerce Admin"
admin.site.index_title = "Panneau d'administration"