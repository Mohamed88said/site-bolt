import math
import requests
from django.core.cache import cache
from django.conf import settings
import logging

logger = logging.getLogger(__name__)

class DistanceCalculator:
    """Calculateur de distance avec plusieurs méthodes"""
    
    @staticmethod
    def haversine_distance(lat1, lon1, lat2, lon2):
        """
        Calcule la distance à vol d'oiseau entre deux points GPS
        Retourne la distance en kilomètres
        """
        # Convertir en radians
        lat1, lon1, lat2, lon2 = map(math.radians, [lat1, lon1, lat2, lon2])
        
        # Formule de Haversine
        dlat = lat2 - lat1
        dlon = lon2 - lon1
        a = math.sin(dlat/2)**2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon/2)**2
        c = 2 * math.asin(math.sqrt(a))
        
        # Rayon de la Terre en kilomètres
        r = 6371
        
        return c * r
    
    @staticmethod
    def osrm_distance(lat1, lon1, lat2, lon2):
        """
        Calcule la distance routière avec OSRM
        Retourne la distance en kilomètres et la durée en minutes
        """
        cache_key = f"osrm_distance_{lat1}_{lon1}_{lat2}_{lon2}"
        cached_result = cache.get(cache_key)
        
        if cached_result:
            return cached_result
        
        try:
            url = f"http://router.project-osrm.org/route/v1/driving/{lon1},{lat1};{lon2},{lat2}"
            params = {
                'overview': 'false',
                'alternatives': 'false',
                'steps': 'false'
            }
            
            response = requests.get(url, params=params, timeout=10)
            response.raise_for_status()
            
            data = response.json()
            
            if data['code'] == 'Ok' and data['routes']:
                route = data['routes'][0]
                distance_km = route['distance'] / 1000  # Convertir en km
                duration_min = route['duration'] / 60    # Convertir en minutes
                
                result = {
                    'distance_km': round(distance_km, 2),
                    'duration_min': round(duration_min, 0),
                    'success': True
                }
                
                # Cache pour 1 heure
                cache.set(cache_key, result, 3600)
                return result
            else:
                logger.warning(f"OSRM: Pas de route trouvée entre {lat1},{lon1} et {lat2},{lon2}")
                return {'success': False, 'error': 'Pas de route trouvée'}
                
        except requests.RequestException as e:
            logger.error(f"Erreur OSRM: {e}")
            # Fallback sur la distance à vol d'oiseau
            distance = DistanceCalculator.haversine_distance(lat1, lon1, lat2, lon2)
            return {
                'distance_km': round(distance, 2),
                'duration_min': round(distance * 3, 0),  # Estimation: 20km/h moyenne
                'success': True,
                'fallback': True
            }
    
    @staticmethod
    def mapbox_distance(lat1, lon1, lat2, lon2):
        """
        Calcule la distance avec l'API Mapbox
        """
        if not hasattr(settings, 'MAPBOX_API_KEY') or not settings.MAPBOX_API_KEY:
            return DistanceCalculator.osrm_distance(lat1, lon1, lat2, lon2)
        
        cache_key = f"mapbox_distance_{lat1}_{lon1}_{lat2}_{lon2}"
        cached_result = cache.get(cache_key)
        
        if cached_result:
            return cached_result
        
        try:
            url = f"https://api.mapbox.com/directions/v5/mapbox/driving/{lon1},{lat1};{lon2},{lat2}"
            params = {
                'access_token': settings.MAPBOX_API_KEY,
                'overview': 'false',
                'alternatives': 'false',
                'steps': 'false'
            }
            
            response = requests.get(url, params=params, timeout=10)
            response.raise_for_status()
            
            data = response.json()
            
            if data['code'] == 'Ok' and data['routes']:
                route = data['routes'][0]
                distance_km = route['distance'] / 1000
                duration_min = route['duration'] / 60
                
                result = {
                    'distance_km': round(distance_km, 2),
                    'duration_min': round(duration_min, 0),
                    'success': True
                }
                
                cache.set(cache_key, result, 3600)
                return result
            else:
                # Fallback sur OSRM
                return DistanceCalculator.osrm_distance(lat1, lon1, lat2, lon2)
                
        except requests.RequestException as e:
            logger.error(f"Erreur Mapbox: {e}")
            return DistanceCalculator.osrm_distance(lat1, lon1, lat2, lon2)
    
    @staticmethod
    def calculate_delivery_cost(distance_km, base_cost=5.0, cost_per_km=1.0, max_cost=50.0):
        """
        Calcule le coût de livraison basé sur la distance
        """
        if distance_km <= 0:
            return base_cost
        
        total_cost = base_cost + (distance_km * cost_per_km)
        return min(total_cost, max_cost)
    
    @staticmethod
    def get_best_distance(lat1, lon1, lat2, lon2):
        """
        Obtient la meilleure estimation de distance disponible
        Essaie Mapbox, puis OSRM, puis Haversine
        """
        # Essayer Mapbox en premier si disponible
        if hasattr(settings, 'MAPBOX_API_KEY') and settings.MAPBOX_API_KEY:
            result = DistanceCalculator.mapbox_distance(lat1, lon1, lat2, lon2)
            if result['success']:
                return result
        
        # Fallback sur OSRM
        result = DistanceCalculator.osrm_distance(lat1, lon1, lat2, lon2)
        if result['success']:
            return result
        
        # Dernier recours: distance à vol d'oiseau
        distance = DistanceCalculator.haversine_distance(lat1, lon1, lat2, lon2)
        return {
            'distance_km': round(distance, 2),
            'duration_min': round(distance * 3, 0),
            'success': True,
            'method': 'haversine'
        }