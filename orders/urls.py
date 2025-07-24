from django.urls import path
from . import views

app_name = 'orders'

urlpatterns = [
    path('', views.OrderListView.as_view(), name='list'),
    path('<uuid:pk>/', views.OrderDetailView.as_view(), name='detail'),
    path('<uuid:pk>/tracking/', views.order_tracking, name='tracking'),
    path('checkout/', views.checkout, name='checkout'),
    path('<uuid:pk>/cancel/', views.cancel_order, name='cancel'),
    path('<uuid:pk>/update-status/', views.update_order_status, name='update_status'),
]