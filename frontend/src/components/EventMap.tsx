import React, { useEffect, useRef, useState, useMemo } from "react";
import mapboxgl from "mapbox-gl";
import "mapbox-gl/dist/mapbox-gl.css";
import {
  Loader2,
  AlertCircle,
} from "lucide-react";
import {
  Popover,
  PopoverContent,
  PopoverTrigger,
} from "@/components/ui/popover";
import { Button } from "@/components/ui/button";
import { ToggleGroup, ToggleGroupItem } from "@/components/ui/toggle-group";
import { Alert, AlertDescription } from "@/components/ui/alert";
import MapFilters from "./MapFilters";
import { useMapFilters } from "@/hooks/useMapFilters";
import { useEvents } from "@/hooks/useEvents";
import { Event, MapFilters as ApiMapFilters } from "@/lib/api";
import {
  getCoordinatesForLocation,
  addCoordinateJitter,
  Coordinates,
} from "@/lib/geocoding";
import { categoryConfig, getCategoryConfig, getAllCategories } from "@/lib/eventCategories";
import { inferEventCategory, extractPriceValue } from "@/lib/filterUtils";
import { logger } from "@/lib/logger";
import { cn } from "@/lib/utils";

interface MapEvent extends Event {
  coordinates?: Coordinates;
  category?: string;
}

interface EventMapProps {
  className?: string;
}

const EventMap: React.FC<EventMapProps> = React.memo(({ className }) => {
  const mapContainer = useRef<HTMLDivElement>(null);
  const map = useRef<mapboxgl.Map | null>(null);
  const markersRef = useRef<mapboxgl.Marker[]>([]);
  const sourceInitialized = useRef<boolean>(false);

  const [mapLoaded, setMapLoaded] = useState(false);
  const filters = useMapFilters();

  const apiFilters = filters.apiFilters;

  // Fetch events from API with larger page size for better performance
  const { events, loading, error, total, refetch } = useEvents<ApiMapFilters>({
    filters: { ...apiFilters, size: 100 }, // Fetch more events per request
    autoFetch: true,
  });

  // Transform API events to map events with coordinates and category
  const mapEvents = useMemo(() => {
    const eventsWithCoords: MapEvent[] = [];

    events.forEach((event) => {
      // Use event's latitude/longitude if available, otherwise geocode location
      let coords: Coordinates | null = null;
      
      if (event.latitude && event.longitude) {
        coords = {
          lat: parseFloat(event.latitude.toString()),
          lng: parseFloat(event.longitude.toString()),
        };
      } else {
        coords = getCoordinatesForLocation(event.location);
      }

      if (coords) {
        const eventTitle = (event as any).title || event.name || "";
        const category = inferEventCategory(eventTitle, event.description || "");

        eventsWithCoords.push({
          ...event,
          coordinates: coords,
          category,
        });
      } else {
        logger.warn(
          `Could not geocode location: ${event.location} for event: ${(event as any).title || event.name}`,
        );
      }
    });

    return eventsWithCoords;
  }, [events]);

  // Filter events by category and price
  const filteredEvents = useMemo(() => {
    return mapEvents.filter((event) => {
      // Category filter
      if (filters.activeCategory) {
        const eventTitle = (event as any).title || event.name || "";
        const eventCategory = inferEventCategory(
          eventTitle,
          event.description || "",
        );
        if (eventCategory !== filters.activeCategory) return false;
      }

      // Price filter
      if (filters.selectedPrice) {
        const eventPrice = extractPriceValue(event.price || "");
        if (eventPrice !== null) {
          const [minPrice, maxPrice] = filters.selectedPrice;
          if (eventPrice < minPrice || eventPrice > maxPrice) return false;
        }
      }

      return true;
    });
  }, [mapEvents, filters.activeCategory, filters.selectedPrice]);


  // Note: inferEventCategory and extractPriceValue moved to @/lib/filterUtils

  // Helper function to get category color
  const getCategoryColor = (category: string): string => {
    const config = getCategoryConfig(category);
    return config.color;
  };

  // Convert filtered events to GeoJSON for clustering (optimized)
  const eventsGeoJSON = useMemo((): GeoJSON.FeatureCollection => {
    // Limit events for performance if there are too many
    const eventsToRender = filteredEvents.length > 1000 
      ? filteredEvents.slice(0, 1000) 
      : filteredEvents;

    return {
      type: 'FeatureCollection',
      features: eventsToRender.map((event) => {
        const category = event.category || 'other';
        return {
          type: 'Feature',
          properties: {
            id: (event as any).id || Math.random().toString(),
            title: (event as any).title || event.name || "",
            description: event.description ? event.description.substring(0, 200) : "", // Limit description length
            date: event.date,
            time: event.time,
            location: event.location,
            price: event.price || "Contact organizer",
            image: event.image,
            link: event.link,
            category,
            color: getCategoryColor(category),
          },
          geometry: {
            type: 'Point',
            coordinates: [event.coordinates!.lng, event.coordinates!.lat],
          },
        };
      }),
    };
  }, [filteredEvents]);


  // Initialize map
  useEffect(() => {
    if (!mapContainer.current) return;

    const mapboxToken = import.meta.env.VITE_MAPBOX_ACCESS_TOKEN;
    if (!mapboxToken) {
      logger.error("Mapbox access token is required");
      return;
    }

    mapboxgl.accessToken = mapboxToken;

    map.current = new mapboxgl.Map({
      container: mapContainer.current,
      style: "mapbox://styles/mapbox/light-v11",
      center: [15.9819, 45.815], // Zagreb center
      zoom: 7,
      attributionControl: false,
    });

    map.current.on("load", () => {
      setMapLoaded(true);
    });

    return () => {
      if (map.current) {
        map.current.remove();
      }
    };
  }, []);

  // Setup clustering layers and update data when events change
  useEffect(() => {
    if (!mapLoaded || !map.current) return;

    // Initialize source and layers on first load
    if (!sourceInitialized.current) {
      setupClusteringLayers();
      sourceInitialized.current = true;
    } else {
      // Update existing source data
      updateMapData();
    }
  }, [mapLoaded, eventsGeoJSON]);

  const setupClusteringLayers = () => {
    if (!map.current) return;

    // Add data source with clustering enabled
    map.current.addSource('events', {
      type: 'geojson',
      data: eventsGeoJSON,
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

    // Add individual event points (colored by category)
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
          11, 12, // At zoom 11, radius is 12
          14, 16, // At zoom 14, radius is 16
        ],
        'circle-stroke-width': 2,
        'circle-stroke-color': '#ffffff',
        'circle-opacity': [
          'interpolate',
          ['linear'],
          ['zoom'],
          7, 0.8,   // At zoom 7, opacity is 0.8
          11, 0.6,  // At zoom 11, fade to 0.6
          13, 0.3,  // At zoom 13, fade to 0.3
          14, 0.0,  // At zoom 14+, fully transparent (icons take over)
        ],
      },
    });

    // Add category icons for high zoom levels
    map.current.addLayer({
      id: 'event-icons',
      type: 'symbol',
      source: 'events',
      filter: ['!', ['has', 'point_count']],
      layout: {
        'icon-image': [
          'case',
          ['==', ['get', 'category'], 'concert'], 'music-15',
          ['==', ['get', 'category'], 'music'], 'music-15',
          ['==', ['get', 'category'], 'festival'], 'star-15',
          ['==', ['get', 'category'], 'party'], 'bar-15',
          ['==', ['get', 'category'], 'conference'], 'building-15',
          ['==', ['get', 'category'], 'theater'], 'theatre-15',
          ['==', ['get', 'category'], 'culture'], 'museum-15',
          ['==', ['get', 'category'], 'workout'], 'bicycle-15',
          ['==', ['get', 'category'], 'sports'], 'pitch-15',
          ['==', ['get', 'category'], 'meetup'], 'circle-15',
          'marker-15', // Default icon for 'other' category
        ],
        'icon-size': [
          'interpolate',
          ['linear'],
          ['zoom'],
          11, 0.6,  // At zoom 11, size is 0.6
          13, 0.8,  // At zoom 13, size is 0.8
          14, 1.0,  // At zoom 14+, full size
        ],
        'icon-opacity': [
          'interpolate',
          ['linear'],
          ['zoom'],
          11, 0.0,  // At zoom 11-, fully transparent
          13, 0.5,  // At zoom 13, half opacity
          14, 1.0,  // At zoom 14+, fully opaque
        ],
        'icon-allow-overlap': true,
        'icon-ignore-placement': true,
      },
      paint: {
        'icon-color': '#ffffff',
      },
    });

    setupClusterEventHandlers();
  };

  const updateMapData = () => {
    if (!map.current) return;
    
    const source = map.current.getSource('events') as mapboxgl.GeoJSONSource;
    if (source) {
      source.setData(eventsGeoJSON);
    }
  };

  const setupClusterEventHandlers = () => {
    if (!map.current) return;

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

    // Handle individual event clicks (both circles and icons)
    const handleEventClick = (e: any) => {
      if (!e.features?.[0]?.properties) return;
      
      const event = e.features[0].properties;
      const coordinates = (e.features[0].geometry as GeoJSON.Point).coordinates as [number, number];
      
      // Create popup
      const popup = new mapboxgl.Popup({
        closeButton: true,
        closeOnClick: true,
        maxWidth: '320px',
      })
        .setLngLat(coordinates)
        .setHTML(`
          <div class="p-3 bg-white rounded-lg shadow-lg">
            ${event.image ? `<img src="${event.image}" alt="${event.title}" class="w-full h-24 object-cover rounded mb-2" onerror="this.style.display='none'">` : ""}
            <h3 class="font-bold text-base mb-1 text-gray-900 line-clamp-2">${event.title}</h3>
            ${event.description ? `<p class="text-xs text-gray-600 mb-2 line-clamp-2">${event.description.substring(0, 120)}${event.description.length > 120 ? '...' : ''}</p>` : ""}
            <div class="space-y-1 text-xs text-gray-700">
              <p><span class="font-medium">📅</span> ${new Date(event.date).toLocaleDateString()} at ${event.time}</p>
              <p><span class="font-medium">📍</span> ${event.location}</p>
              <p><span class="font-medium">💰</span> ${event.price}</p>
            </div>
            <div class="mt-2">
              <span class="inline-block px-2 py-1 text-xs font-medium rounded-full" 
                    style="background-color: ${event.color}20; color: ${event.color}">
                ${event.category}
              </span>
            </div>
            ${event.link ? `<a href="${event.link}" target="_blank" class="inline-block mt-2 px-2 py-1 bg-blue-500 text-white rounded hover:bg-blue-600 text-xs transition-colors">View Details</a>` : ""}
          </div>
        `)
        .addTo(map.current!);
    };

    map.current.on('click', 'unclustered-point', handleEventClick);
    map.current.on('click', 'event-icons', handleEventClick);

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
    map.current.on('mouseenter', 'event-icons', () => {
      if (map.current) map.current.getCanvas().style.cursor = 'pointer';
    });
    map.current.on('mouseleave', 'event-icons', () => {
      if (map.current) map.current.getCanvas().style.cursor = '';
    });
  };


  return (
    <div className={cn("relative w-full h-screen", className)}>
      {/* Map Container */}
      <div ref={mapContainer} className="w-full h-full" />

      {/* Loading Overlay */}
      {loading && (
        <div className="absolute inset-0 bg-white bg-opacity-80 flex items-center justify-center z-50">
          <div className="flex items-center space-x-2">
            <Loader2 className="h-6 w-6 animate-spin" />
            <span>Loading events...</span>
          </div>
        </div>
      )}

      {/* Error Alert */}
      {error && (
        <div className="absolute top-4 left-4 right-4 z-50">
          <Alert variant="destructive">
            <AlertCircle className="h-4 w-4" />
            <AlertDescription>
              {error}
              <Button
                variant="outline"
                size="sm"
                className="ml-2"
                onClick={refetch}
              >
                Retry
              </Button>
            </AlertDescription>
          </Alert>
        </div>
      )}

      {/* Controls Panel */}
      <MapFilters
        filters={filters}
        filteredCount={filteredEvents.length}
        total={total}
        error={error}
      />

      {/* Legend */}
      <div className="absolute bottom-4 right-4 bg-white rounded-lg shadow-lg p-4 z-40 max-w-xs">
        <h3 className="font-semibold mb-3 text-sm">Map Legend</h3>
        
        {/* Clustering explanation */}
        <div className="mb-4 pb-3 border-b border-gray-200">
          <div className="flex items-center space-x-2 text-xs mb-2">
            <div className="w-6 h-6 rounded-full bg-blue-500 text-white text-xs flex items-center justify-center font-bold">
              15
            </div>
            <span className="text-gray-700">Clustered events (zoom to expand)</span>
          </div>
          <p className="text-xs text-gray-600">Click clusters to zoom in. Individual icons show at high zoom levels.</p>
        </div>

        {/* Event categories */}
        <h4 className="font-medium mb-2 text-xs">Event Categories</h4>
        <div className="grid grid-cols-2 gap-2">
          {getAllCategories().map((key) => {
            const config = categoryConfig[key];
            const IconComponent = config.icon;
            return (
              <div key={key} className="flex items-center space-x-2 text-xs">
                <div
                  className="w-4 h-4 rounded-full flex items-center justify-center flex-shrink-0"
                  style={{ backgroundColor: config.color }}
                >
                  <IconComponent className="h-2 w-2 text-white" />
                </div>
                <span className="truncate text-gray-700">{config.label}</span>
              </div>
            );
          })}
        </div>
        
        {/* Event count */}
        <div className="mt-3 pt-2 border-t border-gray-200">
          <p className="text-xs text-gray-600">
            Showing {Math.min(filteredEvents.length, 1000)} of {total} events
          </p>
          {filteredEvents.length > 1000 && (
            <p className="text-xs text-amber-600 mt-1">
              ⚡ Limited to 1000 events for performance
            </p>
          )}
        </div>
      </div>
    </div>
  );
});

export default EventMap;
