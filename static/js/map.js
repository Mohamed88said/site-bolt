mapboxgl.accessToken = 'pk.eyJ1IjoibW9oYW1lZGY2IiwiYSI6ImNtZGVoNG1lNDAyYXQya3NnMXdzZjU5YXgifQ.CAxUtdD9bEe97CxTZg1-Lg';

const map = new mapboxgl.Map({
    container: 'map',
    style: 'mapbox://styles/mapbox/streets-v11',
    center: [0, 0],
    zoom: 2
});

map.addControl(new mapboxgl.NavigationControl());

map.on('load', () => {
    map.addSource('delivery-persons', {
        type: 'geojson',
        data: {
            type: 'FeatureCollection',
            features: []
        },
        cluster: true,
        clusterMaxZoom: 14,
        clusterRadius: 50
    });

    map.addLayer({
        id: 'clusters',
        type: 'circle',
        source: 'delivery-persons',
        filter: ['has', 'point_count'],
        paint: {
            'circle-color': [
                'step',
                ['get', 'point_count'],
                '#D4AF37',
                10,
                '#FF6B35',
                30,
                '#8B4513'
            ],
            'circle-radius': [
                'step',
                ['get', 'point_count'],
                20,
                10,
                30,
                30,
                40
            ]
        }
    });

    map.addLayer({
        id: 'cluster-count',
        type: 'symbol',
        source: 'delivery-persons',
        filter: ['has', 'point_count'],
        layout: {
            'text-field': '{point_count_abbreviated}',
            'text-font': ['DIN Offc Pro Medium', 'Arial Unicode MS Bold'],
            'text-size': 12
        }
    });

    map.addLayer({
        id: 'unclustered-point',
        type: 'circle',
        source: 'delivery-persons',
        filter: ['!', ['has', 'point_count']],
        paint: {
            'circle-color': '#D4AF37',
            'circle-radius': 10,
            'circle-stroke-width': 2,
            'circle-stroke-color': '#fff'
        }
    });

    map.on('click', 'clusters', (e) => {
        const features = map.queryRenderedFeatures(e.point, { layers: ['clusters'] });
        const clusterId = features[0].properties.cluster_id;
        map.getSource('delivery-persons').getClusterExpansionZoom(clusterId, (err, zoom) => {
            if (err) return;
            map.easeTo({
                center: features[0].geometry.coordinates,
                zoom: zoom
            });
        });
    });

    map.on('click', 'unclustered-point', (e) => {
        const coordinates = e.features[0].geometry.coordinates.slice();
        const { full_name, phone } = e.features[0].properties;
        new mapboxgl.Popup()
            .setLngLat(coordinates)
            .setHTML(`
                <div class="popup-african">
                    <h6>${full_name}</h6>
                    <p><i class="fas fa-phone"></i> ${phone}</p>
                    <a href="/deliveries/assign/${e.features[0].properties.user_id}" class="btn btn-sm btn-primary">Choisir ce livreur</a>
                </div>
            `)
            .addTo(map);
    });

    map.on('mouseenter', 'clusters', () => {
        map.getCanvas().style.cursor = 'pointer';
    });
    map.on('mouseleave', 'clusters', () => {
        map.getCanvas().style.cursor = '';
    });

    const ws = new WebSocket(`wss://${window.location.host}/ws/delivery_locations/`);
    ws.onmessage = (e) => {
        const data = JSON.parse(e.data);
        if (!data.error) {
            const source = map.getSource('delivery-persons');
            const features = source._data.features;
            const existingFeature = features.find(f => f.properties.user_id === data.user_id);
            if (existingFeature) {
                existingFeature.geometry.coordinates = [data.longitude, data.latitude];
                existingFeature.properties = { ...existingFeature.properties, ...data };
            } else {
                features.push({
                    type: 'Feature',
                    geometry: {
                        type: 'Point',
                        coordinates: [data.longitude, data.latitude]
                    },
                    properties: data
                });
            }
            source.setData({
                type: 'FeatureCollection',
                features: features
            });
        }
    };

    // Charger les livreurs initiaux
    fetch('/api/delivery-persons/')
        .then(response => response.json())
        .then(data => {
            map.getSource('delivery-persons').setData({
                type: 'FeatureCollection',
                features: data.map(person => ({
                    type: 'Feature',
                    geometry: {
                        type: 'Point',
                        coordinates: [person.longitude, person.latitude]
                    },
                    properties: {
                        user_id: person.user_id,
                        full_name: person.full_name,
                        phone: person.phone
                    }
                }))
            });
        });
});