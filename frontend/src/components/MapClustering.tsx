import React, { useRef, useEffect, useState } from 'react';
import mapboxgl from 'mapbox-gl';
import 'mapbox-gl/dist/mapbox-gl.css';

interface Event {
  id: string;
  name: string;
  longitude: number;
  latitude: number;
  category: string;
  price?: string;
  date: string;
  venue: string;
  city: string;
}

interface MapClusteringProps {
  events: Event[];
  onEventClick?: (event: Event) => void;
  className?: string;
}

const MapClustering: React.FC<MapClusteringProps> = ({
  events,
  onEventClick,
  className = 'h-[600px] w-full rounded-lg',
}) => {
  const mapContainer = useRef<HTMLDivElement>(null);
  const map = useRef<mapboxgl.Map | null>(null);
  const [mapLoaded, setMapLoaded] = useState(false);

  // Category colors for markers
  const getCategoryColor = (category: string): string => {
    const colors: Record<string, string> = {
      concert: '#e11d48',
      festival: '#c026d3',
      party: '#ea580c',
      conference: '#2563eb',
      workout: '#16a34a',
      meetup: '#0891b2',
      theater: '#dc2626',
      exhibition: '#4f46e5',
      other: '#6b7280',
    };
    return colors[category] || colors.other;
  };

  useEffect(() => {
    if (!mapContainer.current) return;

    // Initialize map
    mapboxgl.accessToken = import.meta.env.VITE_MAPBOX_ACCESS_TOKEN || '';
    
    map.current = new mapboxgl.Map({
      container: mapContainer.current,
      style: 'mapbox://styles/mapbox/light-v11',
      center: [15.9819, 45.8150], // Croatia center
      zoom: 7,
      maxZoom: 18,
      minZoom: 4,
    });

    map.current.addControl(new mapboxgl.NavigationControl(), 'top-right');
    map.current.addControl(new mapboxgl.FullscreenControl(), 'top-right');

    map.current.on('load', () => {
      setMapLoaded(true);
      setupClusterLayer();
    });

    return () => {
      if (map.current) {
        map.current.remove();
      }
    };
  }, []);

  const setupClusterLayer = () => {
    if (!map.current) return;

    // Convert events to GeoJSON
    const geojsonData: GeoJSON.FeatureCollection = {
      type: 'FeatureCollection',
      features: events.map(event => ({
        type: 'Feature',
        properties: {
          id: event.id,
          name: event.name,
          category: event.category,
          price: event.price,
          date: event.date,
          venue: event.venue,
          city: event.city,
          color: getCategoryColor(event.category),
        },
        geometry: {
          type: 'Point',
          coordinates: [event.longitude, event.latitude],
        },
      })),
    };

    // Add data source
    map.current.addSource('events', {
      type: 'geojson',
      data: geojsonData,
      cluster: true,
      clusterMaxZoom: 14, // Max zoom to cluster points on
      clusterRadius: 50, // Radius of each cluster when clustering points
    });

    // Add cluster circles
    map.current.addLayer({
      id: 'clusters',
      type: 'circle',
      source: 'events',
      filter: ['has', 'point_count'],
      paint: {
        'circle-color': [
          'step',
          ['get', 'point_count'],
          '#51bbd6', // Color for clusters with < 10 points
          10,
          '#f1c40f', // Color for clusters with 10-30 points
          30,
          '#e74c3c', // Color for clusters with > 30 points
        ],
        'circle-radius': [
          'step',
          ['get', 'point_count'],
          20, // Radius for clusters with < 10 points
          10,
          30, // Radius for clusters with 10-30 points
          30,
          40, // Radius for clusters with > 30 points
        ],
        'circle-stroke-width': 2,
        'circle-stroke-color': '#ffffff',
      },
    });

    // Add cluster count labels
    map.current.addLayer({
      id: 'cluster-count',
      type: 'symbol',
      source: 'events',
      filter: ['has', 'point_count'],
      layout: {
        'text-field': ['get', 'point_count_abbreviated'],
        'text-font': ['DIN Offc Pro Medium', 'Arial Unicode MS Bold'],
        'text-size': 12,
      },
      paint: {
        'text-color': '#ffffff',
      },
    });

    // Add individual event points
    map.current.addLayer({
      id: 'unclustered-point',
      type: 'circle',
      source: 'events',
      filter: ['!', ['has', 'point_count']],
      paint: {
        'circle-color': ['get', 'color'],
        'circle-radius': [
          'interpolate',
          ['linear'],
          ['zoom'],
          7, 8,   // At zoom 7, radius is 8
          14, 15, // At zoom 14, radius is 15
        ],
        'circle-stroke-width': 2,
        'circle-stroke-color': '#ffffff',
        'circle-opacity': 0.8,
      },
    });

    // Add event icons
    map.current.addLayer({
      id: 'event-icons',
      type: 'symbol',
      source: 'events',
      filter: ['!', ['has', 'point_count']],
      layout: {
        'icon-image': [
          'case',
          ['==', ['get', 'category'], 'concert'], 'music-15',
          ['==', ['get', 'category'], 'festival'], 'star-15',
          ['==', ['get', 'category'], 'party'], 'bar-15',
          ['==', ['get', 'category'], 'conference'], 'building-15',
          ['==', ['get', 'category'], 'workout'], 'bicycle-15',
          ['==', ['get', 'category'], 'meetup'], 'circle-15',
          ['==', ['get', 'category'], 'theater'], 'theatre-15',
          ['==', ['get', 'category'], 'exhibition'], 'museum-15',
          'marker-15', // Default icon
        ],
        'icon-size': 0.8,
        'icon-allow-overlap': true,
      },
      paint: {
        'icon-color': '#ffffff',
      },
    });

    // Handle cluster clicks (zoom in)
    map.current.on('click', 'clusters', (e) => {
      if (!map.current) return;
      
      const features = map.current.queryRenderedFeatures(e.point, {
        layers: ['clusters'],
      });

      const clusterId = features[0].properties?.cluster_id;
      const source = map.current.getSource('events') as mapboxgl.GeoJSONSource;
      
      source.getClusterExpansionZoom(clusterId, (err, zoom) => {
        if (err || !map.current) return;

        map.current.easeTo({
          center: (features[0].geometry as GeoJSON.Point).coordinates as [number, number],
          zoom: zoom,
          duration: 500,
        });
      });
    });

    // Handle individual event clicks
    map.current.on('click', 'unclustered-point', (e) => {
      if (!e.features?.[0]?.properties) return;
      
      const event = e.features[0].properties as any;
      
      // Create popup
      const popup = new mapboxgl.Popup({
        closeButton: true,
        closeOnClick: true,
        maxWidth: '300px',
      })
        .setLngLat((e.features[0].geometry as GeoJSON.Point).coordinates as [number, number])
        .setHTML(`
          <div class="p-3">
            <h3 class="font-bold text-lg text-navy-blue mb-2">${event.name}</h3>
            <div class="space-y-2 text-sm">
              <div class="flex items-center gap-2">
                <span class="text-gray-600">📅</span>
                <span>${new Date(event.date).toLocaleDateString()}</span>
              </div>
              <div class="flex items-center gap-2">
                <span class="text-gray-600">📍</span>
                <span>${event.venue}, ${event.city}</span>
              </div>
              ${event.price ? `
                <div class="flex items-center gap-2">
                  <span class="text-gray-600">💰</span>
                  <span>${event.price}</span>
                </div>
              ` : ''}
              <div class="mt-3">
                <span class="inline-block px-2 py-1 text-xs font-medium rounded-full" 
                      style="background-color: ${event.color}20; color: ${event.color}">
                  ${event.category}
                </span>
              </div>
            </div>
            <button 
              class="mt-3 w-full px-3 py-2 bg-navy-blue text-white rounded-md text-sm hover:bg-navy-blue/90 transition-colors"
              onclick="window.handleEventClick('${event.id}')"
            >
              View Details
            </button>
          </div>
        `)
        .addTo(map.current);

      // Store event click handler globally
      (window as any).handleEventClick = (eventId: string) => {
        const selectedEvent = events.find(e => e.id === eventId);
        if (selectedEvent && onEventClick) {
          onEventClick(selectedEvent);
        }
        popup.remove();
      };
    });

    // Change cursor on hover
    map.current.on('mouseenter', 'clusters', () => {
      if (map.current) map.current.getCanvas().style.cursor = 'pointer';
    });
    map.current.on('mouseleave', 'clusters', () => {
      if (map.current) map.current.getCanvas().style.cursor = '';
    });
    map.current.on('mouseenter', 'unclustered-point', () => {
      if (map.current) map.current.getCanvas().style.cursor = 'pointer';
    });
    map.current.on('mouseleave', 'unclustered-point', () => {
      if (map.current) map.current.getCanvas().style.cursor = '';
    });
  };

  // Update map data when events change
  useEffect(() => {
    if (!map.current || !mapLoaded) return;

    const geojsonData: GeoJSON.FeatureCollection = {
      type: 'FeatureCollection',
      features: events.map(event => ({
        type: 'Feature',
        properties: {
          id: event.id,
          name: event.name,
          category: event.category,
          price: event.price,
          date: event.date,
          venue: event.venue,
          city: event.city,
          color: getCategoryColor(event.category),
        },
        geometry: {
          type: 'Point',
          coordinates: [event.longitude, event.latitude],
        },
      })),
    };

    const source = map.current.getSource('events') as mapboxgl.GeoJSONSource;
    if (source) {
      source.setData(geojsonData);
    }
  }, [events, mapLoaded]);

  return (
    <div className={`relative ${className}`}>
      <div ref={mapContainer} className="h-full w-full" />
      
      {/* Map Legend */}
      <div className="absolute bottom-4 left-4 bg-white rounded-lg shadow-lg p-3 max-w-xs">
        <h4 className="font-medium text-sm mb-2">Event Categories</h4>
        <div className="grid grid-cols-2 gap-2 text-xs">
          {Object.entries({
            concert: 'Concerts',
            festival: 'Festivals', 
            party: 'Parties',
            conference: 'Conferences',
            workout: 'Workouts',
            meetup: 'Meetups',
          }).map(([key, label]) => (
            <div key={key} className="flex items-center gap-2">
              <div 
                className="w-3 h-3 rounded-full"
                style={{ backgroundColor: getCategoryColor(key) }}
              />
              <span className="text-gray-700">{label}</span>
            </div>
          ))}
        </div>
        <div className="mt-3 pt-2 border-t border-gray-200">
          <div className="flex items-center gap-2 text-xs text-gray-600">
            <div className="w-6 h-6 rounded-full bg-blue-500 text-white text-xs flex items-center justify-center font-bold">
              5
            </div>
            <span>Clustered events</span>
          </div>
        </div>
      </div>

      {/* Loading indicator */}
      {!mapLoaded && (
        <div className="absolute inset-0 bg-gray-100 flex items-center justify-center rounded-lg">
          <div className="text-center">
            <div className="w-8 h-8 border-4 border-navy-blue border-t-transparent rounded-full animate-spin mx-auto mb-2"></div>
            <p className="text-sm text-gray-600">Loading map...</p>
          </div>
        </div>
      )}
    </div>
  );
};

export default MapClustering;