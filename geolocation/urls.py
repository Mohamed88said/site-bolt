from django.urls import path
from . import views

app_name = 'geolocation'

urlpatterns = [
    path('picker/', views.location_picker, name='location_picker'),
    path('save/', views.save_location, name='save_location'),
    path('verify/<int:location_id>/', views.verify_location, name='verify_location'),
    path('detail/<int:location_id>/', views.location_detail, name='location_detail'),
    path('search/', views.search_locations, name='search_locations'),
    path('delivery-person-map/<int:delivery_id>/', views.delivery_person_map, name='delivery_person_map'),  # Changé uuid en int
    path('api/prefectures/', views.api_prefectures, name='api_prefectures'),
    path('api/communes/', views.api_communes, name='api_communes'),
]