import React, { useState, useMemo } from "react";
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
import { Button } from "@/components/ui/button";
import { ToggleGroup, ToggleGroupItem } from "@/components/ui/toggle-group";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Alert, AlertDescription } from "@/components/ui/alert";
import { useEvents } from "@/hooks/useEvents";
import { MapFilters } from "@/lib/api";
import { useLanguage } from "@/contexts/LanguageContext";

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

const EventMapDemo = () => {
  const [activeCategory, setActiveCategory] = useState<string | null>(null);
  const [searchTerm, setSearchTerm] = useState("");
  const { t } = useLanguage();

  // API filters based on current selections
  const apiFilters = useMemo(() => {
    const filters: MapFilters = {};
    if (searchTerm) {
      filters.search = searchTerm;
    }
    return filters;
  }, [searchTerm]);

  // Fetch events from API
  const { events, loading, error, total, refetch } = useEvents<MapFilters>({
    filters: apiFilters,
    autoFetch: true,
  });

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

  // Filter events by category
  const filteredEvents = useMemo(() => {
    return events.filter((event) => {
      // Category filter
      if (activeCategory) {
        const eventCategory = inferEventCategory(
          event.name,
          event.description || "",
        );
        if (eventCategory !== activeCategory) return false;
      }
      return true;
    });
  }, [events, activeCategory]);

  const handleCategoryChange = (category: string | null) => {
    setActiveCategory(category === activeCategory ? null : category);
  };

  return (
    <div className="relative w-full h-[600px] bg-gradient-to-br from-blue-50 to-green-50 rounded-lg border-2 border-dashed border-gray-300">
      {/* Demo Map Placeholder */}
      <div className="absolute inset-0 flex items-center justify-center">
        <div className="text-center p-8 bg-white/80 rounded-lg shadow-lg max-w-md">
          <MapPin className="h-12 w-12 text-blue-500 mx-auto mb-4" />
          <h3 className="text-xl font-semibold mb-2">{t("demo.map.title")}</h3>
          <p className="text-gray-600 mb-4">{t("demo.map.description")}</p>
          <Button
            onClick={() => (window.location.href = "/map")}
            className="mb-3"
          >
            {t("demo.map.button")}
          </Button>
          <div className="text-sm text-gray-500">📍 {t("demo.map.events")}</div>
        </div>
      </div>

      {/* Loading Overlay */}
      {loading && (
        <div className="absolute inset-0 bg-white bg-opacity-80 flex items-center justify-center z-50">
          <div className="flex items-center space-x-2">
            <Loader2 className="h-6 w-6 animate-spin" />
            <span>{t("map.loading")}</span>
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
                {t("map.retry")}
              </Button>
            </AlertDescription>
          </Alert>
        </div>
      )}

      {/* Controls Panel */}
      <div className="absolute top-4 left-4 bg-white rounded-lg shadow-lg p-4 space-y-4 max-w-sm z-40">
        {/* Search */}
        <div>
          <Label htmlFor="search">{t("map.search.label")}</Label>
          <Input
            id="search"
            placeholder={t("map.search.placeholder")}
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
          />
        </div>

        {/* Event Categories */}
        <div>
          <Label>{t("map.categories.label")}</Label>
          <ToggleGroup
            type="single"
            value={activeCategory || ""}
            onValueChange={handleCategoryChange}
          >
            {Object.entries(categoryConfig)
              .slice(0, 6)
              .map(([key, config]) => {
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

        {/* Event Count */}
        <div className="text-sm text-gray-600 text-center">
          Showing {filteredEvents.length} of {total} events
        </div>
      </div>

      {/* Events List Panel */}
      <div className="absolute bottom-4 right-4 bg-white rounded-lg shadow-lg p-4 max-w-sm z-40 max-h-80 overflow-y-auto">
        <h3 className="font-semibold mb-3">Croatian Events</h3>
        <div className="space-y-2">
          {filteredEvents.slice(0, 5).map((event) => {
            const category = inferEventCategory(
              event.name,
              event.description || "",
            );
            const config = categoryConfig[category] || categoryConfig.other;
            const IconComponent = config.icon;

            return (
              <div
                key={event.id}
                className="flex items-start space-x-3 p-2 bg-gray-50 rounded"
              >
                <div
                  className="w-8 h-8 rounded-full flex items-center justify-center flex-shrink-0"
                  style={{ backgroundColor: config.color }}
                >
                  <IconComponent className="h-4 w-4 text-white" />
                </div>
                <div className="min-w-0 flex-1">
                  <p className="text-sm font-medium text-gray-900 truncate">
                    {event.name}
                  </p>
                  <p className="text-xs text-gray-500">
                    📍 {event.location} • 📅{" "}
                    {new Date(event.date).toLocaleDateString()}
                  </p>
                  <p className="text-xs text-gray-600 truncate">
                    {event.description?.substring(0, 60)}...
                  </p>
                </div>
              </div>
            );
          })}
          {filteredEvents.length > 5 && (
            <p className="text-xs text-gray-500 text-center pt-2">
              And {filteredEvents.length - 5} more events...
            </p>
          )}
        </div>
      </div>

      {/* Legend */}
      <div className="absolute bottom-4 left-4 bg-white rounded-lg shadow-lg p-4 z-40">
        <h3 className="font-semibold mb-2 text-sm">Event Types</h3>
        <div className="space-y-1">
          {Object.entries(categoryConfig)
            .slice(0, 4)
            .map(([key, config]) => {
              const IconComponent = config.icon;
              return (
                <div key={key} className="flex items-center space-x-2 text-xs">
                  <div
                    className="w-3 h-3 rounded-full flex items-center justify-center"
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

export default EventMapDemo;
