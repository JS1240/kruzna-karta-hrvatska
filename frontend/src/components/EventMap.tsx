import React, { useEffect, useRef, useState, useMemo } from "react";
import mapboxgl from "mapbox-gl";
import "mapbox-gl/dist/mapbox-gl.css";
import {
  Music,
  Dumbbell,
  Users,
  CalendarDays,
  PartyPopper,
  MapPin,
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
import { Slider } from "@/components/ui/slider";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { Calendar } from "@/components/ui/calendar";
import { Alert, AlertDescription } from "@/components/ui/alert";
import type { DateRange } from "react-day-picker";
import { useEvents } from "@/hooks/useEvents";
import { Event } from "@/lib/api";
import {
  getCoordinatesForLocation,
  addCoordinateJitter,
  Coordinates,
} from "@/lib/geocoding";
import { logger } from "@/lib/logger";

// Croatian counties and their cities
const countiesWithCities = {
  "Split-Dalmatia": ["Split", "Makarska", "Trogir", "Omiš", "Hvar"],
  Zagreb: ["Zagreb", "Velika Gorica", "Samobor", "Zaprešić"],
  "Dubrovnik-Neretva": ["Dubrovnik", "Metković", "Ploče", "Korčula"],
  "Primorje-Gorski Kotar": ["Rijeka", "Opatija", "Crikvenica", "Krk"],
  Zadar: ["Zadar", "Biograd", "Pag", "Nin"],
  Istria: ["Pula", "Rovinj", "Poreč", "Umag"],
  "Lika-Senj": ["Gospić", "Senj", "Otočac", "Novalja"],
};

// Event category mapping and icons
const categoryConfig = {
  concert: { icon: Music, color: "#e11d48", label: "Concerts" },
  music: { icon: Music, color: "#e11d48", label: "Music" },
  workout: { icon: Dumbbell, color: "#059669", label: "Sports & Fitness" },
  sports: { icon: Dumbbell, color: "#059669", label: "Sports" },
  meetup: { icon: Users, color: "#7c3aed", label: "Meetups" },
  conference: { icon: CalendarDays, color: "#dc2626", label: "Conferences" },
  party: { icon: PartyPopper, color: "#ea580c", label: "Parties" },
  festival: { icon: Music, color: "#db2777", label: "Festivals" },
  theater: { icon: CalendarDays, color: "#0891b2", label: "Theater" },
  culture: { icon: CalendarDays, color: "#0891b2", label: "Culture" },
  other: { icon: CalendarDays, color: "#6b7280", label: "Other" },
};

interface MapEvent extends Event {
  coordinates?: Coordinates;
}

const EventMap = () => {
  const mapContainer = useRef<HTMLDivElement>(null);
  const map = useRef<mapboxgl.Map | null>(null);
  const markersRef = useRef<mapboxgl.Marker[]>([]);

  const [mapLoaded, setMapLoaded] = useState(false);
  const [activeCategory, setActiveCategory] = useState<string | null>(null);
  const [selectedCounty, setSelectedCounty] = useState<string | null>(null);
  const [selectedCity, setSelectedCity] = useState<string | null>(null);
  const [selectedPrice, setSelectedPrice] = useState<[number, number] | null>(
    null,
  );
  const [selectedDateRange, setSelectedDateRange] = useState<string | null>(
    null,
  );
  const [selectedDateRangeObj, setSelectedDateRangeObj] = useState<
    DateRange | undefined
  >(undefined);
  const [calendarOpen, setCalendarOpen] = useState(false);
  const [searchTerm, setSearchTerm] = useState("");

  // API filters based on current selections
  const apiFilters = useMemo(() => {
    const filters: any = {};

    if (searchTerm) {
      filters.search = searchTerm;
    }

    if (selectedCity) {
      filters.location = selectedCity;
    } else if (selectedCounty) {
      filters.location = selectedCounty;
    }

    // Date filtering
    const dateRange = getDateRangeFromSelection(selectedDateRange);
    if (dateRange) {
      filters.date_from = dateRange[0].toISOString().split("T")[0];
      filters.date_to = dateRange[1].toISOString().split("T")[0];
    } else if (selectedDateRangeObj?.from) {
      filters.date_from = selectedDateRangeObj.from.toISOString().split("T")[0];
      if (selectedDateRangeObj.to) {
        filters.date_to = selectedDateRangeObj.to.toISOString().split("T")[0];
      }
    }

    return filters;
  }, [
    searchTerm,
    selectedCity,
    selectedCounty,
    selectedDateRange,
    selectedDateRangeObj,
  ]);

  // Fetch events from API
  const { events, loading, error, total, refetch } = useEvents({
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
          `Could not geocode location: ${event.location} for event: ${event.name}`,
        );
      }
    });

    return eventsWithCoords;
  }, [events]);

  // Filter events by category and price
  const filteredEvents = useMemo(() => {
    return mapEvents.filter((event) => {
      // Category filter
      if (activeCategory) {
        const eventCategory = inferEventCategory(
          event.name,
          event.description || "",
        );
        if (eventCategory !== activeCategory) return false;
      }

      // Price filter
      if (selectedPrice) {
        const eventPrice = extractPriceValue(event.price || "");
        if (eventPrice !== null) {
          const [minPrice, maxPrice] = selectedPrice;
          if (eventPrice < minPrice || eventPrice > maxPrice) return false;
        }
      }

      return true;
    });
  }, [mapEvents, activeCategory, selectedPrice]);

  // Get date ranges based on selection
  const getDateRangeFromSelection = (
    selection: string | null,
  ): [Date, Date] | null => {
    if (!selection) return null;

    const today = new Date();
    today.setHours(0, 0, 0, 0);

    const tomorrow = new Date(today);
    tomorrow.setDate(tomorrow.getDate() + 1);

    const thisWeekend = new Date(today);
    const dayOfWeek = today.getDay();
    const daysUntilWeekend =
      dayOfWeek === 0 || dayOfWeek === 6 ? 0 : 6 - dayOfWeek;
    thisWeekend.setDate(today.getDate() + daysUntilWeekend);

    const nextWeekend = new Date(thisWeekend);
    nextWeekend.setDate(nextWeekend.getDate() + 7);

    const endOfMonth = new Date(today.getFullYear(), today.getMonth() + 1, 0);

    switch (selection) {
      case "today":
        return [today, today];
      case "tomorrow":
        return [tomorrow, tomorrow];
      case "this-weekend": {
        const weekendEnd = new Date(thisWeekend);
        weekendEnd.setDate(thisWeekend.getDate() + 1);
        return [thisWeekend, weekendEnd];
      }
      case "next-weekend": {
        const nextWeekendEnd = new Date(nextWeekend);
        nextWeekendEnd.setDate(nextWeekend.getDate() + 1);
        return [nextWeekend, nextWeekendEnd];
      }
      case "this-month":
        return [today, endOfMonth];
      default:
        return null;
    }
  };

  // Infer event category from name and description
  const inferEventCategory = (name: string, description: string): string => {
    const text = `${name} ${description}`.toLowerCase();

    if (
      text.includes("concert") ||
      text.includes("glazba") ||
      text.includes("muzik")
    )
      return "concert";
    if (
      text.includes("sport") ||
      text.includes("fitness") ||
      text.includes("workout") ||
      text.includes("trening")
    )
      return "workout";
    if (
      text.includes("meetup") ||
      text.includes("networking") ||
      text.includes("meet")
    )
      return "meetup";
    if (
      text.includes("conference") ||
      text.includes("konferencija") ||
      text.includes("business")
    )
      return "conference";
    if (
      text.includes("party") ||
      text.includes("zabava") ||
      text.includes("festival")
    )
      return "party";
    if (
      text.includes("theater") ||
      text.includes("kazalište") ||
      text.includes("predstava")
    )
      return "theater";
    if (text.includes("festival")) return "festival";

    return "other";
  };

  // Extract numeric price value
  const extractPriceValue = (price: string): number | null => {
    if (!price) return null;
    if (
      price.toLowerCase().includes("free") ||
      price.toLowerCase().includes("besplatno")
    )
      return 0;

    const match = price.match(/(\d+)/);
    return match ? parseInt(match[1]) : null;
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

      const category = inferEventCategory(event.name, event.description || "");
      const config = categoryConfig[category] || categoryConfig.other;
      const IconComponent = config.icon;

      // Create marker element
      const el = document.createElement("div");
      el.className = "event-marker";
      el.style.cssText = `
        width: 40px;
        height: 40px;
        background-color: ${config.color};
        border: 3px solid white;
        border-radius: 50%;
        display: flex;
        align-items: center;
        justify-content: center;
        cursor: pointer;
        box-shadow: 0 2px 8px rgba(0,0,0,0.3);
        transition: transform 0.2s;
      `;

      // Add icon
      el.innerHTML = `
        <svg width="20" height="20" viewBox="0 0 24 24" fill="white" stroke="white" stroke-width="2">
          ${
            IconComponent === Music
              ? '<path d="9 18V5l12-2v13M9 18c0 1.657-1.343 3-3 3s-3-1.343-3-3 1.343-3 3-3 3 1.343 3 3zM21 16c0 1.657-1.343 3-3 3s-3-1.343-3-3 1.343-3 3-3 3 1.343 3 3z"/>'
              : IconComponent === Dumbbell
                ? '<path d="m6.5 6.5 11 11M21 21l-1-1M3 3l1 1M18 22H6M22 18V6M2 18V6"/>'
                : IconComponent === Users
                  ? '<path d="M16 21v-2a4 4 0 0 0-4-4H6a4 4 0 0 0-4 4v2M9 7a4 4 0 1 0 0-8 4 4 0 0 0 0 8zM22 21v-2a4 4 0 0 0-3-3.87M16 3.13a4 4 0 0 1 0 7.75"/>'
                  : IconComponent === PartyPopper
                    ? '<path d="M5.8 11.3 2 22l10.7-3.79M4 3h.01M22 8h.01M15 2h.01M22 20h.01M22 2l-2.24.75a2.9 2.9 0 0 0-1.96 3.12v0c.1.86-.57 1.63-1.45 1.63h-.38c-.86 0-1.6.6-1.76 1.44L14 10"/>'
                    : '<rect x="3" y="4" width="18" height="18" rx="2" ry="2"/><line x1="16" y1="2" x2="16" y2="6"/><line x1="8" y1="2" x2="8" y2="6"/><line x1="3" y1="10" x2="21" y2="10"/>'
          }
        </svg>
      `;

      // Hover effects
      el.addEventListener("mouseenter", () => {
        el.style.transform = "scale(1.1)";
      });

      el.addEventListener("mouseleave", () => {
        el.style.transform = "scale(1)";
      });

      // Create marker
      const marker = new mapboxgl.Marker(el)
        .setLngLat([event.coordinates.lng, event.coordinates.lat])
        .addTo(map.current!);

      // Create popup
      const popup = new mapboxgl.Popup({
        offset: 25,
        closeButton: true,
        closeOnClick: false,
        maxWidth: "300px",
      });

      const popupContent = `
        <div class="p-3">
          ${event.image ? `<img src="${event.image}" alt="${event.name}" class="w-full h-32 object-cover rounded mb-2" onerror="this.style.display='none'">` : ""}
          <h3 class="font-bold text-lg mb-1">${event.name}</h3>
          <p class="text-sm text-gray-600 mb-2">${event.description?.substring(0, 100)}${event.description && event.description.length > 100 ? "..." : ""}</p>
          <div class="space-y-1 text-sm">
            <p><strong>📅 Date:</strong> ${new Date(event.date).toLocaleDateString()} at ${event.time}</p>
            <p><strong>📍 Location:</strong> ${event.location}</p>
            <p><strong>💰 Price:</strong> ${event.price || "Contact organizer"}</p>
          </div>
          ${event.link ? `<a href="${event.link}" target="_blank" class="inline-block mt-2 px-3 py-1 bg-blue-500 text-white rounded hover:bg-blue-600 text-sm">View Details</a>` : ""}
        </div>
      `;

      popup.setHTML(popupContent);

      // Show popup on click
      el.addEventListener("click", () => {
        // Close all other popups
        document.querySelectorAll(".mapboxgl-popup").forEach((p) => p.remove());
        marker.setPopup(popup);
        popup.addTo(map.current!);
      });

      markersRef.current.push(marker);
    });
  }, [mapLoaded, filteredEvents]);

  // Functions to handle filter changes
  const handleCategoryChange = (category: string | null) => {
    setActiveCategory(category === activeCategory ? null : category);
  };

  const handleDateRangeChange = (value: string) => {
    setSelectedDateRange(value === selectedDateRange ? null : value);
    setSelectedDateRangeObj(undefined);
  };

  const handleCountyChange = (county: string) => {
    setSelectedCounty(county === selectedCounty ? "" : county);
    setSelectedCity(null);
  };

  const handleCityChange = (city: string) => {
    setSelectedCity(city === selectedCity ? "" : city);
  };

  const handlePriceRangeChange = (values: number[]) => {
    setSelectedPrice([values[0], values[1]]);
  };

  const clearAllFilters = () => {
    setActiveCategory(null);
    setSelectedCounty(null);
    setSelectedCity(null);
    setSelectedPrice(null);
    setSelectedDateRange(null);
    setSelectedDateRangeObj(undefined);
    setSearchTerm("");
  };

  const getAvailableCities = () => {
    if (!selectedCounty) return [];
    return (
      countiesWithCities[selectedCounty as keyof typeof countiesWithCities] ||
      []
    );
  };

  return (
    <div className="relative w-full h-screen">
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
      <div className="absolute top-4 left-4 bg-white rounded-lg shadow-lg p-4 space-y-4 max-w-sm z-40">
        {/* Search */}
        <div>
          <Label htmlFor="search">Search Events</Label>
          <Input
            id="search"
            placeholder="Search by name or description..."
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
          />
        </div>

        {/* Event Categories */}
        <div>
          <Label>Event Categories</Label>
          <ToggleGroup
            type="single"
            value={activeCategory || ""}
            onValueChange={handleCategoryChange}
          >
            {Object.entries(categoryConfig).map(([key, config]) => {
              const IconComponent = config.icon;
              return (
                <ToggleGroupItem
                  key={key}
                  value={key}
                  aria-label={config.label}
                >
                  <IconComponent
                    className="h-4 w-4"
                    style={{ color: config.color }}
                  />
                </ToggleGroupItem>
              );
            })}
          </ToggleGroup>
        </div>

        {/* Location Filters */}
        <div className="space-y-2">
          <Label>Location</Label>
          <Select
            value={selectedCounty || ""}
            onValueChange={handleCountyChange}
          >
            <SelectTrigger>
              <SelectValue placeholder="Select County" />
            </SelectTrigger>
            <SelectContent>
              {Object.keys(countiesWithCities).map((county) => (
                <SelectItem key={county} value={county}>
                  {county}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>

          {selectedCounty && (
            <Select value={selectedCity || ""} onValueChange={handleCityChange}>
              <SelectTrigger>
                <SelectValue placeholder="Select City" />
              </SelectTrigger>
              <SelectContent>
                {getAvailableCities().map((city) => (
                  <SelectItem key={city} value={city}>
                    {city}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          )}
        </div>

        {/* Date Range Filter */}
        <div>
          <Label>Date Range</Label>
          <ToggleGroup
            type="single"
            value={selectedDateRange || ""}
            onValueChange={handleDateRangeChange}
          >
            <ToggleGroupItem value="today">Today</ToggleGroupItem>
            <ToggleGroupItem value="tomorrow">Tomorrow</ToggleGroupItem>
            <ToggleGroupItem value="this-weekend">Weekend</ToggleGroupItem>
            <ToggleGroupItem value="this-month">This Month</ToggleGroupItem>
          </ToggleGroup>

          <Popover open={calendarOpen} onOpenChange={setCalendarOpen}>
            <PopoverTrigger asChild>
              <Button variant="outline" className="w-full mt-2">
                {selectedDateRangeObj?.from
                  ? selectedDateRangeObj.to
                    ? `${selectedDateRangeObj.from.toLocaleDateString()} - ${selectedDateRangeObj.to.toLocaleDateString()}`
                    : selectedDateRangeObj.from.toLocaleDateString()
                  : "Pick custom dates"}
              </Button>
            </PopoverTrigger>
            <PopoverContent className="w-auto p-0" align="start">
              <Calendar
                initialFocus
                mode="range"
                defaultMonth={selectedDateRangeObj?.from}
                selected={selectedDateRangeObj}
                onSelect={setSelectedDateRangeObj}
                numberOfMonths={2}
              />
            </PopoverContent>
          </Popover>
        </div>

        {/* Price Range Filter */}
        <div>
          <Label>Price Range (EUR)</Label>
          <div className="px-2 py-4">
            <Slider
              defaultValue={[0, 200]}
              max={500}
              step={10}
              value={selectedPrice || [0, 500]}
              onValueChange={handlePriceRangeChange}
            />
            <div className="flex justify-between text-xs text-gray-500 mt-1">
              <span>{selectedPrice?.[0] || 0}€</span>
              <span>{selectedPrice?.[1] || 500}€</span>
            </div>
          </div>
        </div>

        {/* Clear Filters */}
        <Button variant="outline" onClick={clearAllFilters} className="w-full">
          Clear All Filters
        </Button>

        {/* Event Count */}
        <div className="text-sm text-gray-600 text-center">
          Showing {filteredEvents.length} of {total} events
        </div>
      </div>

      {/* Legend */}
      <div className="absolute bottom-4 right-4 bg-white rounded-lg shadow-lg p-4 z-40">
        <h3 className="font-semibold mb-2">Event Types</h3>
        <div className="space-y-1">
          {Object.entries(categoryConfig).map(([key, config]) => {
            const IconComponent = config.icon;
            return (
              <div key={key} className="flex items-center space-x-2 text-sm">
                <div
                  className="w-4 h-4 rounded-full flex items-center justify-center"
                  style={{ backgroundColor: config.color }}
                >
                  <IconComponent className="h-2 w-2 text-white" />
                </div>
                <span>{config.label}</span>
              </div>
            );
          })}
        </div>
      </div>
    </div>
  );
};

export default EventMap;
