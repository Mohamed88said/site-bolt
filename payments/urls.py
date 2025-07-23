from django.urls import path
from . import views

app_name = 'payments'

urlpatterns = [
    path('confirm/<uuid:payment_id>/', views.confirm_payment, name='confirm_payment'),
    path('confirm-cash/<uuid:payment_id>/', views.confirm_cash_payment, name='confirm_cash_payment'),
    path('dispute/<uuid:payment_id>/', views.dispute_payment, name='dispute_payment'),
    path('dispute/<int:dispute_id>/detail/', views.dispute_detail, name='dispute_detail'),
]