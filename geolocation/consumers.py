import json
from channels.generic.websocket import AsyncWebsocketConsumer
from django.contrib.auth import get_user_model
from .models import LocationPoint

User = get_user_model()

class DeliveryLocationConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.group_name = 'delivery_locations'
        await self.channel_layer.group_add(self.group_name, self.channel_name)
        await self.accept()

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard(self.group_name, self.channel_name)

    async def receive(self, text_data):
        data = json.loads(text_data)
        user_id = data.get('user_id')
        latitude = data.get('latitude')
        longitude = data.get('longitude')

        if user_id and latitude and longitude:
            try:
                user = User.objects.get(id=user_id, is_delivery=True)
                location = LocationPoint.objects.filter(user=user).first()
                if location:
                    location.latitude = latitude
                    location.longitude = longitude
                    location.save()
                else:
                    location = LocationPoint.objects.create(
                        user=user,
                        latitude=latitude,
                        longitude=longitude,
                        type='delivery'
                    )

                await self.channel_layer.group_send(
                    self.group_name,
                    {
                        'type': 'location_update',
                        'user_id': user_id,
                        'latitude': latitude,
                        'longitude': longitude,
                        'phone': user.phone or '',
                        'full_name': user.get_full_name() or user.username
                    }
                )
            except User.DoesNotExist:
                await self.send(text_data=json.dumps({
                    'error': 'Utilisateur non trouvé ou non livreur'
                }))
            except ValueError:
                await self.send(text_data=json.dumps({
                    'error': 'Coordonnées invalides'
                }))

    async def location_update(self, event):
        await self.send(text_data=json.dumps({
            'user_id': event['user_id'],
            'latitude': event['latitude'],
            'longitude': event['longitude'],
            'phone': event['phone'],
            'full_name': event['full_name']
        }))