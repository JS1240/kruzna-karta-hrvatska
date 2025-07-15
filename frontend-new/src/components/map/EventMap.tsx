import React, { useEffect, useRef, useState, useMemo } from 'react';
import mapboxgl from 'mapbox-gl';
import { Loader2, AlertCircle, MapIcon } from 'lucide-react';
import { Event, MapBounds } from '@/types/event';
import { format } from 'date-fns';
import clsx from 'clsx';

interface EventMapProps {
  events: Event[];
  loading?: boolean;
  onEventClick?: (event: Event) => void;
  onMapMove?: (bounds: MapBounds, zoom: number) => void;
  className?: string;
  height?: string;
  showZoomControls?: boolean;
  initialCenter?: [number, number];
  initialZoom?: number;
}

// Default Croatian coordinates (Zagreb)
const DEFAULT_CENTER: [number, number] = [15.9819, 45.8150];
const DEFAULT_ZOOM = 7;

// Category configuration for colors
const categoryConfig = {
  concert: { color: '#e74c3c', label: 'Concert' },
  music: { color: '#e74c3c', label: 'Music' },
  festival: { color: '#f39c12', label: 'Festival' },
  party: { color: '#9b59b6', label: 'Party' },
  conference: { color: '#3498db', label: 'Conference' },
  theater: { color: '#2ecc71', label: 'Theater' },
  culture: { color: '#e67e22', label: 'Culture' },
  workout: { color: '#1abc9c', label: 'Workout' },
  sports: { color: '#e74c3c', label: 'Sports' },
  meetup: { color: '#34495e', label: 'Meetup' },
  other: { color: '#95a5a6', label: 'Other' },
};

// Simple category inference
const inferEventCategory = (title: string, description: string): string => {
  const text = `${title} ${description}`.toLowerCase();
  
  if (text.includes('concert') || text.includes('music') || text.includes('band')) return 'concert';
  if (text.includes('festival') || text.includes('fest')) return 'festival';
  if (text.includes('party') || text.includes('zabava')) return 'party';
  if (text.includes('conference') || text.includes('konferencija')) return 'conference';
  if (text.includes('theater') || text.includes('theatre')) return 'theater';
  if (text.includes('culture') || text.includes('kultura') || text.includes('art')) return 'culture';
  if (text.includes('workout') || text.includes('fitness')) return 'workout';
  if (text.includes('sport') || text.includes('football')) return 'sports';
  if (text.includes('meetup') || text.includes('meeting')) return 'meetup';
  
  return 'other';
};

export const EventMap: React.FC<EventMapProps> = ({
  events,
  loading = false,
  onEventClick,
  onMapMove,
  className,
  height = '600px',
  showZoomControls = true,
  initialCenter = DEFAULT_CENTER,
  initialZoom = DEFAULT_ZOOM,
}) => {
  const mapContainer = useRef<HTMLDivElement>(null);
  const map = useRef<mapboxgl.Map | null>(null);
  const [mapLoaded, setMapLoaded] = useState(false);
  const [mapError, setMapError] = useState<string | null>(null);

  // Filter events that have valid coordinates
  const validEvents = useMemo(() => {
    return events.filter(event => 
      event.latitude && 
      event.longitude && 
      !isNaN(event.latitude) && 
      !isNaN(event.longitude)
    );
  }, [events]);

  // Initialize map (only once)
  useEffect(() => {
    if (!mapContainer.current || map.current) return;

    const mapboxToken = import.meta.env.VITE_MAPBOX_ACCESS_TOKEN;
    if (!mapboxToken) {
      setMapError('Mapbox access token is required');
      return;
    }

    // Set token
    mapboxgl.accessToken = mapboxToken;

    try {
      // Create map instance
      map.current = new mapboxgl.Map({
        container: mapContainer.current,
        style: 'mapbox://styles/mapbox/light-v11',
        center: initialCenter,
        zoom: initialZoom,
        attributionControl: false,
      });

      // Add navigation controls
      if (showZoomControls) {
        map.current.addControl(new mapboxgl.NavigationControl(), 'bottom-right');
      }

      // Set up event handlers
      map.current.on('load', () => {
        console.log('Map loaded successfully');
        setMapLoaded(true);
        setMapError(null);
      });

      map.current.on('error', (e) => {
        console.error('Map error:', e);
        setMapError('Failed to load map');
      });

      // Add map move handler
      if (onMapMove) {
        map.current.on('moveend', () => {
          if (map.current) {
            const bounds = map.current.getBounds();
            const mapBounds: MapBounds = {
              north: bounds.getNorth(),
              south: bounds.getSouth(),
              east: bounds.getEast(),
              west: bounds.getWest(),
            };
            onMapMove(mapBounds, map.current.getZoom());
          }
        });
      }

    } catch (error) {
      console.error('Failed to initialize map:', error);
      setMapError('Failed to initialize map');
    }

    // Cleanup function
    return () => {
      if (map.current) {
        map.current.remove();
        map.current = null;
      }
    };
  }, []); // Empty dependency array - initialize only once

  // Update map data when events change
  useEffect(() => {
    if (!mapLoaded || !map.current || validEvents.length === 0) return;

    // Convert events to GeoJSON
    const eventsGeoJSON: GeoJSON.FeatureCollection = {
      type: 'FeatureCollection',
      features: validEvents.map(event => {
        const category = inferEventCategory(event.title, event.description || '');
        const categoryColor = categoryConfig[category as keyof typeof categoryConfig]?.color || categoryConfig.other.color;
        
        return {
          type: 'Feature',
          properties: {
            id: event.id,
            title: event.title,
            description: event.description || '',
            date: event.date,
            time: event.time,
            location: event.location,
            price: event.price || 'Contact organizer',
            category,
            color: categoryColor,
          },
          geometry: {
            type: 'Point',
            coordinates: [event.longitude!, event.latitude!],
          },
        };
      }),
    };

    try {
      // Remove existing source and layers if they exist
      if (map.current.getSource('events')) {
        if (map.current.getLayer('event-points')) {
          map.current.removeLayer('event-points');
        }
        map.current.removeSource('events');
      }

      // Add new source
      map.current.addSource('events', {
        type: 'geojson',
        data: eventsGeoJSON,
      });

      // Add points layer
      map.current.addLayer({
        id: 'event-points',
        type: 'circle',
        source: 'events',
        paint: {
          'circle-color': ['get', 'color'],
          'circle-radius': 8,
          'circle-stroke-width': 2,
          'circle-stroke-color': '#ffffff',
        },
      });

      // Add click handler
      map.current.on('click', 'event-points', (e) => {
        if (!e.features || e.features.length === 0) return;
        
        const feature = e.features[0];
        const coordinates = (feature.geometry as GeoJSON.Point).coordinates as [number, number];
        const props = feature.properties;

        // Create popup
        const popup = new mapboxgl.Popup({
          closeButton: true,
          closeOnClick: true,
          maxWidth: '300px',
        })
          .setLngLat(coordinates)
          .setHTML(`
            <div class="p-3">
              <h3 class="font-semibold text-lg mb-2">${props?.title || 'Event'}</h3>
              <div class="space-y-1 text-sm">
                <p><strong>Date:</strong> ${props?.date || 'TBD'}</p>
                <p><strong>Time:</strong> ${props?.time || 'TBD'}</p>
                <p><strong>Location:</strong> ${props?.location || 'TBD'}</p>
                <p><strong>Price:</strong> ${props?.price || 'Contact organizer'}</p>
              </div>
            </div>
          `)
          .addTo(map.current!);

        // Call event click handler
        if (onEventClick) {
          const originalEvent = validEvents.find(event => event.id === props?.id);
          if (originalEvent) {
            onEventClick(originalEvent);
          }
        }
      });

      // Change cursor on hover
      map.current.on('mouseenter', 'event-points', () => {
        if (map.current) map.current.getCanvas().style.cursor = 'pointer';
      });

      map.current.on('mouseleave', 'event-points', () => {
        if (map.current) map.current.getCanvas().style.cursor = '';
      });

    } catch (error) {
      console.error('Failed to add events to map:', error);
    }
  }, [mapLoaded, validEvents, onEventClick]);

  // Fit map to show all events
  const fitMapToEvents = () => {
    if (map.current && validEvents.length > 0) {
      const bounds = new mapboxgl.LngLatBounds();
      validEvents.forEach(event => {
        bounds.extend([event.longitude!, event.latitude!]);
      });
      map.current.fitBounds(bounds, { padding: 50 });
    }
  };

  if (loading) {
    return (
      <div 
        className={clsx(
          'flex items-center justify-center bg-gray-100 rounded-xl',
          className
        )}
        style={{ height }}
      >
        <div className="flex flex-col items-center space-y-2">
          <Loader2 className="h-8 w-8 animate-spin text-primary-500" />
          <p className="text-sm text-gray-600">Loading map...</p>
        </div>
      </div>
    );
  }

  if (mapError) {
    return (
      <div 
        className={clsx(
          'flex items-center justify-center bg-gray-100 rounded-xl',
          className
        )}
        style={{ height }}
      >
        <div className="flex flex-col items-center space-y-2 text-center p-4">
          <AlertCircle className="h-8 w-8 text-red-500" />
          <p className="text-sm text-gray-600">{mapError}</p>
          <p className="text-xs text-gray-500">Please check your configuration.</p>
        </div>
      </div>
    );
  }

  return (
    <div className={clsx('relative rounded-xl overflow-hidden', className)}>
      <div 
        ref={mapContainer} 
        style={{ 
          height: height,
          width: '100%',
          minHeight: '400px',
        }} 
      />
      
      {validEvents.length > 0 && mapLoaded && (
        <div className="absolute top-4 right-4 bg-white rounded-lg shadow-lg p-2">
          <button
            onClick={fitMapToEvents}
            className="flex items-center gap-2 px-3 py-1 text-sm text-gray-700 hover:text-primary-600 transition-colors"
          >
            <MapIcon className="w-4 h-4" />
            Fit to events
          </button>
        </div>
      )}
    </div>
  );
};

export default EventMap;