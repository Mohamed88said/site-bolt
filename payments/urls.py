from django.urls import path
from . import views

app_name = 'payments'

urlpatterns = [
    path('create-stripe/<uuid:order_id>/', views.create_stripe_payment, name='create_stripe_payment'),
    path('create-mobile-money/<uuid:order_id>/', views.create_mobile_money_payment, name='create_mobile_money_payment'),
    path('success/<uuid:payment_id>/', views.payment_success, name='payment_success'),
    path('mobile-money/callback/', views.mobile_money_callback, name='mobile_money_callback'),
    path('confirm/<uuid:payment_id>/', views.confirm_payment, name='confirm_payment'),
    path('confirm-cash/<uuid:payment_id>/', views.confirm_cash_payment, name='confirm_cash_payment'),
    path('dispute/<uuid:payment_id>/', views.dispute_payment, name='dispute_payment'),
    path('dispute/<int:dispute_id>/detail/', views.dispute_detail, name='dispute_detail'),
]