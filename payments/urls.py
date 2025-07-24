from django.urls import path
from . import views

app_name = 'payments'

urlpatterns = [
    path('qr-scan/<uuid:payment_id>/', views.qr_scan_payment, name='qr_scan'),
    path('process/<uuid:payment_id>/', views.process_payment, name='process'),
    path('stripe/<uuid:payment_id>/', views.process_stripe, name='process_stripe'),
    path('paypal/<uuid:payment_id>/', views.process_paypal, name='process_paypal'),
    path('mobile-money/<uuid:payment_id>/', views.process_mobile_money, name='process_mobile_money'),
]