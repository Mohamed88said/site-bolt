// Utilitaires pour les cartes Leaflet
let map;
let markers = [];

function initMap(containerId, centerLat = 9.6412, centerLng = -13.5784, zoom = 10) {
    if (map) {
        map.remove();
    }
    
    map = L.map(containerId).setView([centerLat, centerLng], zoom);
    
    L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
        attribution: '© OpenStreetMap contributors'
    }).addTo(map);
    
    return map;
}

function addMarker(lat, lng, popupContent = '', iconClass = 'fa-map-marker') {
    const marker = L.marker([lat, lng]).addTo(map);
    
    if (popupContent) {
        marker.bindPopup(popupContent);
    }
    
    markers.push(marker);
    return marker;
}

function clearMarkers() {
    markers.forEach(marker => {
        map.removeLayer(marker);
    });
    markers = [];
}

function fitMapToMarkers() {
    if (markers.length > 0) {
        const group = new L.featureGroup(markers);
        map.fitBounds(group.getBounds().pad(0.1));
    }
}

function calculateDistance(lat1, lng1, lat2, lng2) {
    const R = 6371; // Rayon de la Terre en km
    const dLat = (lat2 - lat1) * Math.PI / 180;
    const dLng = (lng2 - lng1) * Math.PI / 180;
    const a = Math.sin(dLat/2) * Math.sin(dLat/2) +
              Math.cos(lat1 * Math.PI / 180) * Math.cos(lat2 * Math.PI / 180) *
              Math.sin(dLng/2) * Math.sin(dLng/2);
    const c = 2 * Math.atan2(Math.sqrt(a), Math.sqrt(1-a));
    return R * c;
}

function getCurrentLocation(callback) {
    if (navigator.geolocation) {
        navigator.geolocation.getCurrentPosition(
            function(position) {
                callback(position.coords.latitude, position.coords.longitude);
            },
            function(error) {
                console.error('Erreur géolocalisation:', error);
                // Fallback sur Conakry
                callback(9.6412, -13.5784);
            }
        );
    } else {
        // Fallback sur Conakry
        callback(9.6412, -13.5784);
    }
}