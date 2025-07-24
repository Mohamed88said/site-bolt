from django.urls import path
from . import views

app_name = 'deliveries'

urlpatterns = [
    path('', views.DeliveryListView.as_view(), name='list'),
    path('dashboard/', views.delivery_dashboard, name='delivery_dashboard'),
    path('toggle-availability/', views.toggle_availability, name='toggle_availability'),
    path('<int:pk>/', views.DeliveryDetailView.as_view(), name='detail'),
    path('available/', views.available_deliveries, name='available'),
    path('request/<int:delivery_id>/', views.request_delivery, name='request'),
    path('propose/<int:delivery_id>/', views.propose_delivery_cost, name='propose'),
    path('requests/<int:delivery_id>/', views.delivery_requests, name='delivery_requests'),
    path('confirm-cost/<int:delivery_id>/', views.confirm_delivery_cost, name='confirm_delivery_cost'),
    path('start/<int:delivery_id>/', views.start_delivery, name='start'),
    path('complete/<int:delivery_id>/', views.complete_delivery, name='complete'),
    path('rate/<int:delivery_id>/', views.rate_delivery, name='rate'),
    path('select-location/<int:delivery_id>/', views.select_delivery_location, name='select_location'),
    path('share-qr/<int:delivery_id>/', views.share_qr_code, name='share_qr_code'),
    path('assign/<int:delivery_id>/', views.assign_delivery_person, name='assign_delivery_person'),
    path('accept/<int:request_id>/', views.accept_delivery_request, name='accept'),
    path('<int:delivery_id>/negotiate/', views.negotiate_delivery, name='negotiate'),
]