from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from .models import LocationPoint, UserLocation, GuineaRegion, GuineaPrefecture, GuineaCommune
import json

@login_required
def location_picker(request):
    """Interface de sélection de localisation"""
    regions = GuineaRegion.objects.filter(is_active=True)
    
    # Récupérer les paramètres de l'URL si présents
    region_id = request.GET.get('region_id')
    prefecture_id = request.GET.get('prefecture_id')
    commune_id = request.GET.get('commune_id')
    lat = request.GET.get('lat')
    lng = request.GET.get('lng')
    
    context = {
        'regions': regions,
        'initial_region_id': region_id,
        'initial_prefecture_id': prefecture_id,
        'initial_commune_id': commune_id,
        'initial_lat': lat,
        'initial_lng': lng,
    }
    
    return render(request, 'geolocation/location_picker.html', context)

@login_required
@require_POST
def save_location(request):
    """Sauvegarder une nouvelle localisation"""
    try:
        data = json.loads(request.body)
        
        # Créer le point de localisation
        location_point = LocationPoint.objects.create(
            user=request.user,
            name=data['name'],
            latitude=data['latitude'],
            longitude=data['longitude'],
            region_id=data.get('region_id'),
            prefecture_id=data.get('prefecture_id'),
            commune_id=data.get('commune_id'),
            address=data.get('address', ''),
            city=data.get('city', ''),
            postal_code=data.get('postal_code', ''),
            country=data.get('country', 'Guinée'),
            landmark=data.get('landmark', ''),
            access_instructions=data.get('access_instructions', '')
        )
        
        # Associer à l'utilisateur
        user_location = UserLocation.objects.create(
            user=request.user,
            location_point=location_point,
            is_primary=data.get('is_primary', False),
            label=data.get('label', '')
        )
        
        return JsonResponse({
            'success': True,
            'location_id': location_point.id,
            'message': 'Localisation sauvegardée avec succès!'
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': f'Erreur: {str(e)}'
        })

def location_list(request):
    """Liste des localisations"""
    if request.user.is_authenticated:
        user_locations = UserLocation.objects.filter(user=request.user).select_related('location_point')
    else:
        user_locations = []
    
    return render(request, 'geolocation/location_list.html', {
        'user_locations': user_locations
    })

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

@login_required
@require_POST
def delete_location(request, location_id):
    """Supprimer une localisation"""
    try:
        user_location = get_object_or_404(UserLocation, id=location_id, user=request.user)
        location_point = user_location.location_point
        
        # Supprimer la relation utilisateur
        user_location.delete()
        
        # Supprimer le point de localisation s'il n'est plus utilisé
        if not UserLocation.objects.filter(location_point=location_point).exists():
            location_point.delete()
        
        return JsonResponse({'success': True})
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})