from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.db.models import Q
from .models import LocationPoint, UserLocation, LocationVerification, GuineaRegion, GuineaPrefecture, GuineaCommune
from .forms import LocationForm
from geopy.geocoders import Nominatim
from geopy.distance import geodesic
from django.core.cache import cache
from django_ratelimit.decorators import ratelimit
from deliveries.models import Delivery, DeliveryPerson, DeliveryRequest
from django.utils.translation import gettext_lazy as _
import json
from django.conf import settings
from django.urls import reverse

@login_required
def location_picker(request):
    """Interface de sélection de localisation avec carte"""
    regions = GuineaRegion.objects.filter(is_active=True)
    return render(request, 'geolocation/location_picker.html', {
        'regions': regions,
        'mapbox_api_key': settings.MAPBOX_API_KEY
    })

@login_required
@require_POST
@ratelimit(key='user', rate='10/m')
def save_location(request):
    """Sauvegarder une nouvelle localisation"""
    try:
        data = json.loads(request.body)
        form = LocationForm(data)
        
        if not form.is_valid():
            return JsonResponse({
                'success': False,
                'message': 'Données invalides',
                'errors': form.errors
            })

        # Vérification des coordonnées avec Nominatim
        geolocator = Nominatim(user_agent="ecommerce_app")
        coordinates = f"{form.cleaned_data['latitude']},{form.cleaned_data['longitude']}"
        location = cache.get(coordinates)
        
        if not location:
            location = geolocator.reverse(coordinates, language='fr')
            cache.set(coordinates, location, timeout=86400)  # Cache pour 24h

        if not location:
            return JsonResponse({
                'success': False,
                'message': 'Impossible de valider les coordonnées'
            })

        # Créer le point de localisation
        location_point = LocationPoint.objects.create(
            name=form.cleaned_data['name'],
            description=form.cleaned_data['description'],
            latitude=form.cleaned_data['latitude'],
            longitude=form.cleaned_data['longitude'],
            region=form.cleaned_data['region'],
            prefecture=form.cleaned_data['prefecture'],
            commune=form.cleaned_data['commune'],
            address_details=form.cleaned_data['address_details'],
            landmark=form.cleaned_data['landmark'],
            access_instructions=form.cleaned_data['access_instructions'],
            created_by=request.user
        )
        
        # Associer à l'utilisateur
        UserLocation.objects.create(
            user=request.user,
            location_point=location_point,
            is_primary=data.get('is_primary', False),
            label=data.get('label', ''),
            additional_info=data.get('additional_info', '')
        )
        
        return JsonResponse({
            'success': True,
            'location_id': location_point.id,
            'message': 'Localisation sauvegardée avec succès!'
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': f'Erreur lors de la sauvegarde: {str(e)}'
        })

@login_required
def verify_location(request, location_id):
    """Vérifier une localisation existante"""
    location_point = get_object_or_404(LocationPoint, id=location_id)
    
    if request.method == 'POST':
        is_accurate = request.POST.get('is_accurate') == 'true'
        suggested_correction = request.POST.get('suggested_correction', '')
        local_description = request.POST.get('local_description', '')
        
        # Créer ou mettre à jour la vérification
        verification, created = LocationVerification.objects.get_or_create(
            location_point=location_point,
            verified_by=request.user,
            defaults={
                'is_accurate': is_accurate,
                'suggested_correction': suggested_correction,
                'local_description': local_description
            }
        )
        
        if not created:
            verification.is_accurate = is_accurate
            verification.suggested_correction = suggested_correction
            verification.local_description = local_description
            verification.save()
        
        # Mettre à jour le compteur de vérifications
        location_point.verification_count = location_point.verifications.count()
        accurate_count = location_point.verifications.filter(is_accurate=True).count()
        location_point.verified_by_locals = accurate_count >= 3
        location_point.save()
        
        messages.success(request, 'Merci pour votre vérification!')
        return redirect('geolocation:location_detail', location_id=location_id)
    
    return render(request, 'geolocation/verify_location.html', {
        'location_point': location_point
    })

def location_detail(request, location_id):
    """Détails d'une localisation"""
    location_point = get_object_or_404(LocationPoint, id=location_id)
    verifications = location_point.verifications.all()[:10]
    
    return render(request, 'geolocation/location_detail.html', {
        'location_point': location_point,
        'verifications': verifications
    })

def search_locations(request):
    """Recherche de localisations"""
    query = request.GET.get('q', '')
    locations = []
    
    if query:
        locations = LocationPoint.objects.filter(
            Q(name__icontains=query) |
            Q(description__icontains=query) |
            Q(landmark__icontains=query) |
            Q(address_details__icontains=query),
            is_active=True
        )[:20]
    
    return render(request, 'geolocation/search_results.html', {
        'locations': locations,
        'query': query
    })

@login_required
def delivery_person_map(request, delivery_id):
    """Afficher une carte avec les livreurs disponibles à proximité"""
    try:
        delivery = get_object_or_404(Delivery, id=delivery_id)
        
        # Vérifier si l'utilisateur est le vendeur de la commande
        if not delivery.order.items.exists() or delivery.order.items.first().product.seller != request.user:
            messages.error(request, _("Vous n'êtes pas autorisé à voir les livreurs pour cette livraison."))
            return redirect('deliveries:detail', pk=delivery_id)
        
        if delivery.status != 'pending':
            messages.error(request, _("Vous ne pouvez voir les livreurs que pour les livraisons en attente."))
            return redirect('deliveries:detail', pk=delivery_id)
        
        # Récupérer les livreurs disponibles
        delivery_persons = DeliveryPerson.objects.filter(
            availability_status='available',
            user__delivery_profile__verification_status='approved',
            location_point__isnull=False
        ).select_related('location_point', 'user__delivery_profile')
        
        # Filtrer par distance (10 km)
        max_distance_km = 10
        filtered_delivery_persons = []
        delivery_location = delivery.location_point or delivery.order.get_shipping_location()
        
        if delivery_location and delivery_location.latitude and delivery_location.longitude:
            delivery_coords = (delivery_location.latitude, delivery_location.longitude)
            cache_key = f"delivery_persons_{delivery_id}_10km"
            cached_data = cache.get(cache_key)
            
            if cached_data:
                filtered_delivery_persons = cached_data
            else:
                for dp in delivery_persons:
                    if dp.location_point and dp.location_point.latitude and dp.location_point.longitude:
                        dp_coords = (dp.location_point.latitude, dp.location_point.longitude)
                        try:
                            distance = geodesic(delivery_coords, dp_coords).kilometers
                            if distance <= max_distance_km:
                                filtered_delivery_persons.append({
                                    'id': dp.user.id,
                                    'username': dp.user.username,
                                    'phone_number': dp.phone_number,
                                    'latitude': dp.location_point.latitude,
                                    'longitude': dp.location_point.longitude,
                                    'distance': round(distance, 2),
                                    'rating': dp.rating or 0,
                                    'vehicle_type': dp.get_vehicle_type_display() if dp.vehicle_type else 'Non spécifié',
                                    'requests': dp.delivery_requests.filter(delivery=delivery)
                                })
                        except Exception as e:
                            print(f"Erreur calcul distance pour {dp.user.username}: {e}")
                            continue
                cache.set(cache_key, filtered_delivery_persons, timeout=3600)
        
        # Préparer les données pour la carte
        map_center = {
            'latitude': delivery_location.latitude if delivery_location else 9.6412,
            'longitude': delivery_location.longitude if delivery_location else -13.5784
        }
        
        return render(request, 'geolocation/delivery_person_map.html', {
            'delivery': delivery,
            'delivery_persons': filtered_delivery_persons,
            'map_center': map_center,
            'mapbox_api_key': settings.MAPBOX_API_KEY
        })
    except Delivery.DoesNotExist:
        messages.error(request, _("Aucune livraison trouvée avec cet ID."))
        return redirect('deliveries:list')

# API endpoints pour AJAX
def api_prefectures(request):
    """API pour récupérer les préfectures d'une région"""
    region_id = request.GET.get('region_id')
    prefectures = GuineaPrefecture.objects.filter(region_id=region_id, is_active=True)
    
    data = [{'id': p.id, 'name': p.name} for p in prefectures]
    return JsonResponse({'prefectures': data})

def api_communes(request):
    """API pour récupérer les communes d'une préfecture"""
    prefecture_id = request.GET.get('prefecture_id')
    communes = GuineaCommune.objects.filter(prefecture_id=prefecture_id, is_active=True)
    
    data = [{'id': c.id, 'name': c.name} for c in communes]
    return JsonResponse({'communes': data})