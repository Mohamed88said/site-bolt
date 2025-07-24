from django.urls import path
from . import views

app_name = 'geolocation'

urlpatterns = [
    path('', views.location_list, name='location_list'),
    path('picker/', views.location_picker, name='location_picker'),
    path('save/', views.save_location, name='save_location'),
    path('delete/<int:location_id>/', views.delete_location, name='delete_location'),
    path('api/prefectures/', views.api_prefectures, name='api_prefectures'),
    path('api/communes/', views.api_communes, name='api_communes'),
]