from django.urls import path
from . import views

app_name = 'deliveries'

urlpatterns = [
    path('', views.DeliveryListView.as_view(), name='list'),
    path('<int:pk>/', views.DeliveryDetailView.as_view(), name='detail'),
    path('available/', views.available_deliveries, name='available'),
    path('map/<int:delivery_id>/', views.delivery_map, name='delivery_map'),
    path('request/<int:delivery_id>/', views.request_delivery, name='request'),
    path('accept/<int:request_id>/', views.accept_delivery_request, name='accept'),
    path('start/<int:delivery_id>/', views.start_delivery, name='start'),
    path('complete/<int:delivery_id>/', views.complete_delivery, name='complete'),
    path('rate/<int:delivery_id>/', views.rate_delivery, name='rate'),
]