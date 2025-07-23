# geolocation/routing.py
from django.urls import path
from . import consumers

websocket_urlpatterns = [
    path('ws/delivery_locations/', consumers.DeliveryLocationConsumer.as_asgi()),
]