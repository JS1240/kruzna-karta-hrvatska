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
}

interface EventMapProps {
  className?: string;
}

const EventMap: React.FC<EventMapProps> = ({ className }) => {
  const mapContainer = useRef<HTMLDivElement>(null);
  const map = useRef<mapboxgl.Map | null>(null);
  const markersRef = useRef<mapboxgl.Marker[]>([]);

  const [mapLoaded, setMapLoaded] = useState(false);
  const filters = useMapFilters();

  const apiFilters = filters.apiFilters;

  // Fetch events from API
  const { events, loading, error, total, refetch } = useEvents<ApiMapFilters>({
    filters: apiFilters,
    autoFetch: true,
  });

  // Transform API events to map events with coordinates
  const mapEvents = useMemo(() => {
    const eventsWithCoords: MapEvent[] = [];
    const locationCounts: Record<string, number> = {};

    events.forEach((event) => {
      const coords = getCoordinatesForLocation(event.location);
      if (coords) {
        // Count events at the same location for jittering
        const locationKey = `${coords.lat},${coords.lng}`;
        const count = locationCounts[locationKey] || 0;
        locationCounts[locationKey] = count + 1;

        eventsWithCoords.push({
          ...event,
          coordinates: addCoordinateJitter(coords, count),
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

  // Helper function to get SVG paths for different icons
  const getIconSvg = (category: string): string => {
    const iconMap: Record<string, string> = {
      concert: '<path d="m12 1-8 5v14l8-5 8 5V6l-8-5Z"/><path d="M8 6v10"/><path d="M16 6v10"/>',  // Mic
      music: '<path d="9 18V5l12-2v13M9 18c0 1.657-1.343 3-3 3s-3-1.343-3-3 1.343-3 3-3 3 1.343 3 3zM21 16c0 1.657-1.343 3-3 3s-3-1.343-3-3 1.343-3 3-3 3 1.343 3 3z"/>',  // Music
      festival: '<path d="M6 3h12l4 6-10 13L2 9l4-6z"/><path d="M11 3 8 9l4 13 4-13-3-6"/><path d="M2 9h20"/>',  // Crown
      conference: '<rect width="20" height="14" x="2" y="7" rx="2" ry="2"/><path d="M16 21V5a2 2 0 0 0-2-2h-4a2 2 0 0 0-2 2v16"/>',  // Briefcase
      theater: '<path d="M2 16.1A5 5 0 0 1 5.9 20M6.3 20.1a5 5 0 0 1-2.8-5.2"/><path d="M21.8 16.1A5 5 0 0 0 18 20M17.7 20.1a5 5 0 0 0 2.8-5.2"/><path d="M7 8a3 3 0 1 1 6 0c0 1.55-.59 2.96-1.56 4.03L12 16l.56-3.97A5.002 5.002 0 0 0 15 8a3 3 0 1 1 0-6c-4 0-8 1.5-8 6Z"/>',  // Theater
      culture: '<circle cx="18" cy="7" r="4"/><path d="m14.5 9.5-5 5"/><circle cx="8" cy="17" r="4"/>',  // Palette
      party: '<path d="M5.8 11.3 2 22l10.7-3.79M4 3h.01M22 8h.01M15 2h.01M22 20h.01M22 2l-2.24.75a2.9 2.9 0 0 0-1.96 3.12v0c.1.86-.57 1.63-1.45 1.63h-.38c-.86 0-1.6.6-1.76 1.44L14 10"/>',  // PartyPopper
      meetup: '<path d="M16 21v-2a4 4 0 0 0-4-4H6a4 4 0 0 0-4 4v2M9 7a4 4 0 1 0 0-8 4 4 0 0 0 0 8zM22 21v-2a4 4 0 0 0-3-3.87M16 3.13a4 4 0 0 1 0 7.75"/>',  // Users
      workout: '<path d="M21 8a2 2 0 0 1-1 1.73l-7 4a2 2 0 0 1-2 0l-7-4A2 2 0 0 1 3 8a2 2 0 0 1 1-1.73l7-4a2 2 0 0 1 2 0l7 4A2 2 0 0 1 21 8z"/><path d="m3.3 7 8.7 5 8.7-5"/><path d="M12 22V12"/>',  // Trophy
      sports: '<path d="M21 8a2 2 0 0 1-1 1.73l-7 4a2 2 0 0 1-2 0l-7-4A2 2 0 0 1 3 8a2 2 0 0 1 1-1.73l7-4a2 2 0 0 1 2 0l7 4A2 2 0 0 1 21 8z"/><path d="m3.3 7 8.7 5 8.7-5"/><path d="M12 22V12"/>',  // Trophy
      other: '<circle cx="12" cy="12" r="1"/><circle cx="19" cy="12" r="1"/><circle cx="5" cy="12" r="1"/>',  // MoreHorizontal
    };
    
    return iconMap[category] || iconMap.other;
  };

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

  // Update markers when events change
  useEffect(() => {
    if (!mapLoaded || !map.current) return;

    // Clear existing markers
    markersRef.current.forEach((marker) => marker.remove());
    markersRef.current = [];

    // Add new markers
    filteredEvents.forEach((event, index) => {
      if (!event.coordinates) return;

      const eventTitle = (event as any).title || event.name || "";
      const category = inferEventCategory(eventTitle, event.description || "");
      const config = getCategoryConfig(category);
      const IconComponent = config.icon;

      // Create marker element
      const el = document.createElement("div");
      el.className = "event-marker";
      el.style.cssText = `
        width: 32px;
        height: 32px;
        background-color: ${config.color};
        border: 2px solid white;
        border-radius: 50%;
        display: flex;
        align-items: center;
        justify-content: center;
        cursor: pointer;
        box-shadow: 0 2px 8px rgba(0,0,0,0.3);
        transition: all 0.2s ease;
      `;

      // Generate SVG icon dynamically
      const iconSvg = getIconSvg(category);
      el.innerHTML = `
        <svg width="16" height="16" viewBox="0 0 24 24" fill="white" stroke="white" stroke-width="2">
          ${iconSvg}
        </svg>
      `;

      // Hover effects - only change shadow and border, not position
      el.addEventListener("mouseenter", () => {
        el.style.boxShadow = "0 4px 12px rgba(0,0,0,0.5)";
        el.style.borderWidth = "3px";
      });

      el.addEventListener("mouseleave", () => {
        el.style.boxShadow = "0 2px 8px rgba(0,0,0,0.3)";
        el.style.borderWidth = "2px";
      });

      // Create marker
      const marker = new mapboxgl.Marker(el)
        .setLngLat([event.coordinates.lng, event.coordinates.lat])
        .addTo(map.current!);

      // Create popup
      const popup = new mapboxgl.Popup({
        offset: [0, -10],
        closeButton: false,
        closeOnClick: false,
        maxWidth: "320px",
        className: "event-popup",
      });

      const popupEventTitle = (event as any).title || event.name || "Unknown Event";
      const eventDescription = event.description?.substring(0, 120) + (event.description && event.description.length > 120 ? "..." : "");

      const popupContent = `
        <div class="p-3 bg-white rounded-lg shadow-lg">
          ${event.image ? `<img src="${event.image}" alt="${popupEventTitle}" class="w-full h-24 object-cover rounded mb-2" onerror="this.style.display='none'">` : ""}
          <h3 class="font-bold text-base mb-1 text-gray-900 line-clamp-2">${popupEventTitle}</h3>
          ${eventDescription ? `<p class="text-xs text-gray-600 mb-2 line-clamp-2">${eventDescription}</p>` : ""}
          <div class="space-y-1 text-xs text-gray-700">
            <p><span class="font-medium">📅</span> ${new Date(event.date).toLocaleDateString()} at ${event.time}</p>
            <p><span class="font-medium">📍</span> ${event.location}</p>
            <p><span class="font-medium">💰</span> ${event.price || "Contact organizer"}</p>
          </div>
          ${event.link ? `<a href="${event.link}" target="_blank" class="inline-block mt-2 px-2 py-1 bg-blue-500 text-white rounded hover:bg-blue-600 text-xs transition-colors">View Details</a>` : ""}
        </div>
      `;

      popup.setHTML(popupContent);

      // Show popup on hover
      el.addEventListener("mouseenter", () => {
        // Close all other popups
        document.querySelectorAll(".mapboxgl-popup").forEach((p) => p.remove());
        marker.setPopup(popup);
        popup.addTo(map.current!);
      });

      // Hide popup when mouse leaves marker
      el.addEventListener("mouseleave", () => {
        setTimeout(() => {
          if (!popup.getElement()?.querySelector(':hover')) {
            popup.remove();
          }
        }, 100);
      });

      // Keep popup open when hovering over it
      popup.on('open', () => {
        const popupEl = popup.getElement();
        if (popupEl) {
          popupEl.addEventListener('mouseenter', () => {
            // Keep popup open
          });
          popupEl.addEventListener('mouseleave', () => {
            popup.remove();
          });
        }
      });

      markersRef.current.push(marker);
    });
  }, [mapLoaded, filteredEvents]);


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
        <h3 className="font-semibold mb-3 text-sm">Event Types</h3>
        <div className="grid grid-cols-2 gap-2">
          {getAllCategories().map((key) => {
            const config = categoryConfig[key];
            const IconComponent = config.icon;
            return (
              <div key={key} className="flex items-center space-x-2 text-xs">
                <div
                  className="w-5 h-5 rounded-full flex items-center justify-center flex-shrink-0"
                  style={{ backgroundColor: config.color }}
                >
                  <IconComponent className="h-2.5 w-2.5 text-white" />
                </div>
                <span className="truncate">{config.label}</span>
              </div>
            );
          })}
        </div>
      </div>
    </div>
  );
};

export default EventMap;
