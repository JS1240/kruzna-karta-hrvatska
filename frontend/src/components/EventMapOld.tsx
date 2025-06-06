import React, { useEffect, useRef, useState } from "react";
import mapboxgl from "mapbox-gl";
import "mapbox-gl/dist/mapbox-gl.css";
import {
  Music,
  Dumbbell,
  Users,
  CalendarDays,
  PartyPopper,
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
import type { DateRange } from "react-day-picker";

interface Event {
  id: number;
  title: string;
  description: string;
  category:
    | "concert"
    | "workout"
    | "meetup"
    | "conference"
    | "party"
    | "theater"
    | "festival"
    | "sports"
    | "other";
  location: [number, number];
  date: string;
  time: string;
  image: string;
  ticketLink: string;
  sourceWebsite: string;
  venue: string;
  price: string;
  county: string;
  city: string;
}

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

// Example events data with county and city information
const events: Event[] = [
  {
    id: 1,
    title: "Nina Badrić Concert",
    description:
      "Enjoy the wonderful voice of Nina Badrić in this special summer concert.",
    category: "concert",
    location: [16.4401, 43.5081], // Split
    date: "2025-06-15",
    time: "20:00",
    image: "/event-images/concert.jpg",
    ticketLink: "https://entrio.hr/",
    sourceWebsite: "entrio.hr",
    venue: "Poljud Stadium",
    price: "30-50€",
    county: "Split-Dalmatia",
    city: "Split",
  },
  {
    id: 2,
    title: "Zagreb Bootcamp Challenge",
    description:
      "Join us for an intensive workout session in the heart of Zagreb.",
    category: "workout",
    location: [15.9819, 45.815], // Zagreb
    date: "2025-05-20",
    time: "09:00",
    image: "/event-images/workout.jpg",
    ticketLink: "https://meetup.com/",
    sourceWebsite: "meetup.com",
    venue: "Jarun Lake",
    price: "15€",
    county: "Zagreb",
    city: "Zagreb",
  },
  {
    id: 3,
    title: "Dubrovnik Tech Meetup",
    description:
      "Network with tech professionals and enthusiasts from the region.",
    category: "meetup",
    location: [18.0944, 42.6507], // Dubrovnik
    date: "2025-07-10",
    time: "18:00",
    image: "/event-images/meetup.jpg",
    ticketLink: "https://meetup.com/",
    sourceWebsite: "meetup.com",
    venue: "Hotel Excelsior",
    price: "Free",
    county: "Dubrovnik-Neretva",
    city: "Dubrovnik",
  },
  {
    id: 4,
    title: "Adriatic Business Conference",
    description:
      "Annual conference focusing on business opportunities in the Adriatic region.",
    category: "conference",
    location: [14.4426, 45.3271], // Rijeka
    date: "2025-09-05",
    time: "10:00",
    image: "/event-images/conference.jpg",
    ticketLink: "https://eventim.hr/",
    sourceWebsite: "eventim.hr",
    venue: "Rijeka Convention Center",
    price: "100-200€",
    county: "Primorje-Gorski Kotar",
    city: "Rijeka",
  },
  {
    id: 5,
    title: "Zrće Beach Party",
    description: "The biggest summer party on the famous Zrće beach.",
    category: "party",
    location: [15.0678, 44.5403], // Novalja
    date: "2025-08-01",
    time: "23:00",
    image: "/event-images/party.jpg",
    ticketLink: "https://entrio.hr/",
    sourceWebsite: "entrio.hr",
    venue: "Papaya Club",
    price: "25-40€",
    county: "Lika-Senj",
    city: "Novalja",
  },
  {
    id: 6,
    title: "Zagreb Theater Night",
    description: "A night of drama and performance at the city theater.",
    category: "theater",
    location: [15.978, 45.813], // Zagreb
    date: "2025-06-20",
    time: "19:30",
    image: "/event-images/theater.jpg",
    ticketLink: "https://ulaznice.hr/",
    sourceWebsite: "ulaznice.hr",
    venue: "Zagreb City Theater",
    price: "20-40€",
    county: "Zagreb",
    city: "Zagreb",
  },
  {
    id: 7,
    title: "Split Summer Festival",
    description: "Annual festival with music, food, and fun for all ages.",
    category: "festival",
    location: [16.4402, 43.5083], // Split
    date: "2025-07-15",
    time: "16:00",
    image: "/event-images/festival.jpg",
    ticketLink: "https://festival.hr/",
    sourceWebsite: "festival.hr",
    venue: "Split Riva",
    price: "Free",
    county: "Split-Dalmatia",
    city: "Split",
  },
  {
    id: 8,
    title: "Dubrovnik Sports Day",
    description: "Join the community for a day of sports and activities.",
    category: "sports",
    location: [18.0945, 42.6508], // Dubrovnik
    date: "2025-08-10",
    time: "10:00",
    image: "/event-images/sports.jpg",
    ticketLink: "https://sports.hr/",
    sourceWebsite: "sports.hr",
    venue: "Dubrovnik Sports Center",
    price: "10€",
    county: "Dubrovnik-Neretva",
    city: "Dubrovnik",
  },
  {
    id: 9,
    title: "Istria Art Expo",
    description:
      "A gathering of artists and creators from all over the region.",
    category: "other",
    location: [13.8496, 45.3271], // Pula
    date: "2025-09-12",
    time: "11:00",
    image: "/event-images/other.jpg",
    ticketLink: "https://artexpo.hr/",
    sourceWebsite: "artexpo.hr",
    venue: "Pula Art Center",
    price: "5€",
    county: "Istria",
    city: "Pula",
  },
];

const EventMap = () => {
  const mapContainer = useRef<HTMLDivElement>(null);
  const map = useRef<mapboxgl.Map | null>(null);
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
  // Use a proper DateRange type for selectedDateRangeObj
  const [selectedDateRangeObj, setSelectedDateRangeObj] = useState<
    DateRange | undefined
  >(undefined);
  const [calendarOpen, setCalendarOpen] = useState(false);

  // Get date ranges based on selection
  const getDateRangeFromSelection = (
    selection: string | null,
  ): [Date, Date] | null => {
    if (!selection) return null;

    const today = new Date();
    today.setHours(0, 0, 0, 0);

    const tomorrow = new Date(today);
    tomorrow.setDate(tomorrow.getDate() + 1);

    // Calculate this weekend (closest Saturday and Sunday)
    const thisWeekend = new Date(today);
    const dayOfWeek = today.getDay(); // 0 is Sunday, 6 is Saturday
    const daysUntilWeekend =
      dayOfWeek === 0 || dayOfWeek === 6 ? 0 : 6 - dayOfWeek;
    thisWeekend.setDate(today.getDate() + daysUntilWeekend);

    // Calculate next weekend
    const nextWeekend = new Date(thisWeekend);
    nextWeekend.setDate(nextWeekend.getDate() + 7);

    // Calculate end of month
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

  // Convert date to string format for comparison
  const formatDateForComparison = (date: Date): string => {
    return date.toISOString().split("T")[0];
  };

  // Check if an event date falls within a date range
  const isEventInDateRange = (
    eventDate: string,
    dateRange: [Date, Date],
  ): boolean => {
    const eventDateTime = new Date(eventDate);
    eventDateTime.setHours(0, 0, 0, 0);

    return eventDateTime >= dateRange[0] && eventDateTime <= dateRange[1];
  };

  // Reset city selection when county changes
  useEffect(() => {
    setSelectedCity(null);
  }, [selectedCounty]);

  useEffect(() => {
    // Initialize map only if it hasn't been created yet
    if (map.current) return;

    // Load Mapbox token from environment variable
    mapboxgl.accessToken = import.meta.env.VITE_MAPBOX_TOKEN as string;

    map.current = new mapboxgl.Map({
      container: mapContainer.current!,
      style: "mapbox://styles/mapbox/light-v11",
      center: [16.4, 44.5], // Center of Croatia
      zoom: 7,
      maxBounds: [
        [10.0, 40.0], // Expanded southwest coordinates
        [25.0, 50.0], // Expanded northeast coordinates
      ],
    });

    map.current.on("load", () => {
      if (!map.current) return;

      setMapLoaded(true);
    });

    return () => {
      if (map.current) {
        map.current.remove();
        map.current = null;
      }
    };
  }, []);

  // Add markers when map is loaded and when filters change
  useEffect(() => {
    if (!mapLoaded || !map.current) return;

    // Remove any existing markers
    const existingMarkers = document.querySelectorAll(".mapboxgl-marker");
    existingMarkers.forEach((marker) => marker.remove());

    // Filter events based on selected filters
    let filteredEvents = [...events];

    if (activeCategory) {
      filteredEvents = filteredEvents.filter(
        (event) => event.category === activeCategory,
      );
    }

    // Apply county filter
    if (selectedCounty) {
      filteredEvents = filteredEvents.filter(
        (event) => event.county === selectedCounty,
      );

      // Apply city filter only if a county is selected
      if (selectedCity) {
        filteredEvents = filteredEvents.filter(
          (event) => event.city === selectedCity,
        );
      }
    }

    if (selectedPrice !== null) {
      // Filter events based on the price slider value
      filteredEvents = filteredEvents.filter((event) => {
        if (event.price.toLowerCase().includes("free"))
          return selectedPrice[0] === 0;

        // Extract numeric price value (take the lower bound of ranges like "30-50€")
        const priceMatches = event.price.match(/\d+/g);
        if (priceMatches) {
          const eventMin = parseInt(priceMatches[0]);
          const eventMax = priceMatches[1]
            ? parseInt(priceMatches[1])
            : eventMin;
          return eventMax >= selectedPrice[0] && eventMin <= selectedPrice[1];
        }
        return true;
      });
    }

    // Apply date range filter
    if (selectedDateRange) {
      const dateRange = getDateRangeFromSelection(selectedDateRange);
      if (dateRange) {
        filteredEvents = filteredEvents.filter((event) =>
          isEventInDateRange(event.date, dateRange),
        );
      }
    }

    // Add markers for filtered events
    filteredEvents.forEach((event) => {
      // Create custom marker element
      const el = document.createElement("div");
      el.className = "marker";
      el.style.width = "30px";
      el.style.height = "30px";
      el.style.borderRadius = "50%";
      el.style.cursor = "pointer";
      el.style.backgroundSize = "contain";
      el.style.backgroundRepeat = "no-repeat";
      el.style.backgroundPosition = "center";
      el.style.backgroundColor = "#FFFFFF";
      el.style.boxShadow = "0 2px 10px rgba(0, 0, 0, 0.3)";
      el.style.display = "flex";
      el.style.alignItems = "center";
      el.style.justifyContent = "center";

      // Create icon based on category
      const iconEl = document.createElement("div");
      iconEl.className = "marker-icon";
      iconEl.style.width = "18px";
      iconEl.style.height = "18px";
      iconEl.style.color = "#133E87";

      switch (event.category) {
        case "concert":
          iconEl.innerHTML = `<svg xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="10"/><path d="M12 6v12"/><path d="M6 12h12"/></svg>`;
          break;
        case "workout":
          iconEl.innerHTML = `<svg xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="m6.5 6.5 11 11"/><path d="m21 21-1-1"/><path d="m3 3 1 1"/><path d="m18 22 4-4"/><path d="m2 6 4-4"/><path d="m3 10 7-7"/><path d="m14 21 7-7"/></svg>`;
          break;
        case "meetup":
          iconEl.innerHTML = `<svg xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M18 21a8 8 0 0 0-16 0"/><circle cx="10" cy="8" r="5"/><path d="M22 20c-2 2-4-1-4-3-3 2-3 6 0 6 1.8 0 3-1.5 4-3z"/></svg>`;
          break;
        case "conference":
          iconEl.innerHTML = `<svg xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><rect width="20" height="14" x="2" y="7" rx="2"/><path d="M16 2v5"/><path d="M8 2v5"/><path d="M2 12h20"/></svg>`;
          break;
        case "party":
          iconEl.innerHTML = `<svg xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M5.8 11.3 2 22l10.7-3.79"/><path d="M4 3h.01"/><path d="M22 8h.01"/><path d="M15 2h.01"/><path d="M22 20h.01"/><path d="m22 2-2.24.75a2.9 2.9 0 0 0-1.96 3.12v0c.1.86-.57 1.63-1.45 1.63h-.38c-.86 0-1.6.6-1.76 1.44L14 10"/><path d="m22 13-.82-.33c-.86-.34-1.82.2-1.98 1.11v0c-.11.7-.72 1.22-1.43 1.22H17"/><path d="m11 2 .33.82c.34.86-.2 1.82-1.11 1.98v0C9.52 4.9 9 5.52 9 6.23V7"/><path d="M11 13c1.93 1.93 2.83 4.17 2 5-.83.83-3.07-.07-5-2-1.93-1.93-2.83-4.17-2-5 .83-.83 3.07.07 5 2Z"/></svg>`;
          break;
        case "theater":
          iconEl.innerHTML = `<svg xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><rect x="2" y="7" width="20" height="13" rx="2"/><path d="M8 7V4a4 4 0 0 1 8 0v3"/></svg>`;
          break;
        case "festival":
          iconEl.innerHTML = `<svg xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M2 20h20"/><path d="M6 20V10"/><path d="M18 20V10"/><path d="M12 20V4"/><path d="M2 10h20"/></svg>`;
          break;
        case "sports":
          iconEl.innerHTML = `<svg xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="10"/><path d="M4 12h16"/><path d="M12 4v16"/></svg>`;
          break;
        case "other":
          iconEl.innerHTML = `<svg xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="10"/><path d="M12 8v4l3 3"/></svg>`;
          break;
      }

      el.appendChild(iconEl);

      // Create and add the marker
      const marker = new mapboxgl.Marker(el)
        .setLngLat(event.location)
        .addTo(map.current!);

      // Create popup content
      const popupContent = document.createElement("div");
      popupContent.className = "popup-content";
      popupContent.innerHTML = `
        <div class="mb-3">
          <img src="${event.image}" alt="${event.title}" class="w-full h-40 object-cover rounded-md mb-2" />
          <h3 class="text-lg font-bold text-navy-blue">${event.title}</h3>
          <p class="text-gray-600 text-sm">${event.venue}</p>
        </div>
        <div class="mb-3">
          <p class="text-sm text-gray-700">${event.description}</p>
        </div>
        <div class="flex justify-between items-center text-sm mb-3">
          <div>
            <p class="font-medium">📅 ${new Date(event.date).toLocaleDateString()}</p>
            <p>⏰ ${event.time}</p>
          </div>
          <div>
            <p class="font-medium text-right">💲 ${event.price}</p>
            <p class="text-xs text-gray-500 text-right">Source: ${event.sourceWebsite}</p>
          </div>
        </div>
        <a href="${event.ticketLink}" target="_blank" rel="noopener noreferrer" 
           class="block w-full bg-navy-blue text-white text-center py-2 rounded-md hover:bg-medium-blue transition-colors">
          Buy Tickets / Learn More
        </a>
      `;

      // Create popup
      const popup = new mapboxgl.Popup({
        offset: 25,
        closeButton: false,
        maxWidth: "320px",
      }).setDOMContent(popupContent);

      // Show popup on hover
      el.addEventListener("mouseenter", () => {
        marker.setPopup(popup);
        popup.addTo(map.current!);
      });

      // Optional: Close popup on mouseleave
      el.addEventListener("mouseleave", () => {
        setTimeout(() => {
          if (!popup.isOpen()) return;
          popup.remove();
        }, 300);
      });
    });
  }, [
    mapLoaded,
    activeCategory,
    selectedCounty,
    selectedCity,
    selectedPrice,
    selectedDateRange,
  ]);

  // Functions to handle filter changes
  const handleCategoryChange = (category: string | null) => {
    setActiveCategory(category === activeCategory ? null : category);
  };

  const handleDateRangeChange = (value: string) => {
    setSelectedDateRange(value === selectedDateRange ? null : value);
    setSelectedDateRangeObj(undefined); // Clear custom date range when quick filter is chosen
  };

  // Update price slider change handler
  const handlePriceChange = (value: number[]) => {
    setSelectedPrice([value[0], value[1]]);
  };

  // Handle county selection
  const handleCountyChange = (county: string) => {
    setSelectedCounty(county);
    setSelectedCity(null); // Reset city when county changes
  };

  // Handle city selection
  const handleCityChange = (city: string) => {
    setSelectedCity(city);
  };

  // Handler for custom date range selection from calendar
  const handleCustomDateRange = (range: DateRange | undefined) => {
    setSelectedDateRangeObj(range);
    setSelectedDateRange(null); // Unselect quick range
    if (range && range.from && range.to) {
      setCalendarOpen(false); // Close the calendar popover when both dates are picked
    }
  };

  return (
    <div className="relative my-6">
      {/* Filter controls */}
      <div className="bg-white rounded-lg shadow-md p-4 mb-4 flex flex-wrap gap-4">
        <div className="w-full md:w-auto flex flex-col md:flex-row gap-2">
          <div className="w-full md:w-48">
            <Label
              htmlFor="county-select"
              className="block text-sm font-medium text-gray-700 mb-1"
            >
              County
            </Label>
            <Select
              value={selectedCounty || undefined}
              onValueChange={handleCountyChange}
            >
              <SelectTrigger id="county-select" className="w-full">
                <SelectValue placeholder="Select county" />
              </SelectTrigger>
              <SelectContent>
                {Object.keys(countiesWithCities).map((county) => (
                  <SelectItem key={county} value={county}>
                    {county}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>

          <div className="w-full md:w-48">
            <Label
              htmlFor="city-select"
              className="block text-sm font-medium text-gray-700 mb-1"
            >
              City
            </Label>
            <Select
              value={selectedCity || undefined}
              onValueChange={handleCityChange}
              disabled={!selectedCounty}
            >
              <SelectTrigger id="city-select" className="w-full">
                <SelectValue
                  placeholder={
                    selectedCounty ? "Select city" : "Select county first"
                  }
                />
              </SelectTrigger>
              <SelectContent>
                {selectedCounty &&
                  countiesWithCities[
                    selectedCounty as keyof typeof countiesWithCities
                  ].map((city) => (
                    <SelectItem key={city} value={city}>
                      {city}
                    </SelectItem>
                  ))}
              </SelectContent>
            </Select>
          </div>
        </div>

        <div className="w-full md:w-auto md:flex-1">
          <Label
            htmlFor="price-slider"
            className="block text-sm font-medium text-gray-700 mb-1"
          >
            Price Range:{" "}
            {selectedPrice !== null
              ? `${selectedPrice[0]}€ - ${selectedPrice[1]}€`
              : "Any"}
          </Label>
          <div className="px-2 pt-1">
            <Slider
              id="price-slider"
              defaultValue={[0, 50]}
              value={selectedPrice !== null ? selectedPrice : [0, 50]}
              min={0}
              max={200}
              step={5}
              onValueChange={handlePriceChange}
              className="py-2"
            />
          </div>
        </div>

        <div className="w-full">
          <label className="block text-sm font-medium text-gray-700 mb-1">
            When
          </label>
          <div className="flex flex-wrap gap-2 items-center">
            {/* Existing quick range buttons */}
            <Button
              variant={selectedDateRange === "today" ? "default" : "outline"}
              size="sm"
              onClick={() => handleDateRangeChange("today")}
              className="flex items-center gap-1"
            >
              Today
            </Button>
            <Button
              variant={selectedDateRange === "tomorrow" ? "default" : "outline"}
              size="sm"
              onClick={() => handleDateRangeChange("tomorrow")}
              className="flex items-center gap-1"
            >
              Tomorrow
            </Button>
            <Button
              variant={
                selectedDateRange === "this-weekend" ? "default" : "outline"
              }
              size="sm"
              onClick={() => handleDateRangeChange("this-weekend")}
              className="flex items-center gap-1"
            >
              This Weekend
            </Button>
            <Button
              variant={
                selectedDateRange === "next-weekend" ? "default" : "outline"
              }
              size="sm"
              onClick={() => handleDateRangeChange("next-weekend")}
              className="flex items-center gap-1"
            >
              Next Weekend
            </Button>
            <Button
              variant={
                selectedDateRange === "this-month" ? "default" : "outline"
              }
              size="sm"
              onClick={() => handleDateRangeChange("this-month")}
              className="flex items-center gap-1"
            >
              This Month
            </Button>
            {/* Date range picker */}
            <Popover open={calendarOpen} onOpenChange={setCalendarOpen}>
              <PopoverTrigger asChild>
                <Button
                  variant={
                    selectedDateRangeObj &&
                    selectedDateRangeObj.from &&
                    selectedDateRangeObj.to
                      ? "default"
                      : "outline"
                  }
                  size="sm"
                  className="flex items-center gap-1"
                  onClick={() => setCalendarOpen(true)}
                >
                  {selectedDateRangeObj &&
                  selectedDateRangeObj.from &&
                  selectedDateRangeObj.to
                    ? "Date Range Chosen"
                    : "Pick Date Range"}
                </Button>
              </PopoverTrigger>
              <PopoverContent className="w-auto p-0" align="start">
                <Calendar
                  mode="range"
                  selected={selectedDateRangeObj}
                  onSelect={handleCustomDateRange}
                  numberOfMonths={2}
                />
              </PopoverContent>
            </Popover>
          </div>
        </div>
      </div>

      {/* Map container */}
      <div
        ref={mapContainer}
        className="h-[70vh] rounded-lg shadow-xl overflow-hidden border-4 border-light-blue"
      ></div>

      {/* Category buttons */}
      <div className="flex justify-center mt-6 flex-wrap gap-3">
        <button
          className={`map-category-button flex items-center gap-2 ${activeCategory === "concert" ? "active" : ""}`}
          onClick={() => handleCategoryChange("concert")}
        >
          <span role="img" aria-label="Concert">
            🎵
          </span>{" "}
          Concerts
        </button>
        <button
          className={`map-category-button flex items-center gap-2 ${activeCategory === "workout" ? "active" : ""}`}
          onClick={() => handleCategoryChange("workout")}
        >
          <span role="img" aria-label="Workout">
            💪
          </span>{" "}
          Workouts
        </button>
        <button
          className={`map-category-button flex items-center gap-2 ${activeCategory === "meetup" ? "active" : ""}`}
          onClick={() => handleCategoryChange("meetup")}
        >
          <span role="img" aria-label="Meetup">
            🤝
          </span>{" "}
          Meet-ups
        </button>
        <button
          className={`map-category-button flex items-center gap-2 ${activeCategory === "conference" ? "active" : ""}`}
          onClick={() => handleCategoryChange("conference")}
        >
          <span role="img" aria-label="Conference">
            🎤
          </span>{" "}
          Conferences
        </button>
        <button
          className={`map-category-button flex items-center gap-2 ${activeCategory === "party" ? "active" : ""}`}
          onClick={() => handleCategoryChange("party")}
        >
          <span role="img" aria-label="Party">
            🎉
          </span>{" "}
          Parties
        </button>
        <button
          className={`map-category-button flex items-center gap-2 ${activeCategory === "theater" ? "active" : ""}`}
          onClick={() => handleCategoryChange("theater")}
        >
          <span role="img" aria-label="Theater">
            🎭
          </span>{" "}
          Theaters
        </button>
        <button
          className={`map-category-button flex items-center gap-2 ${activeCategory === "festival" ? "active" : ""}`}
          onClick={() => handleCategoryChange("festival")}
        >
          <span role="img" aria-label="Festival">
            🎪
          </span>{" "}
          Festivals
        </button>
        <button
          className={`map-category-button flex items-center gap-2 ${activeCategory === "sports" ? "active" : ""}`}
          onClick={() => handleCategoryChange("sports")}
        >
          <span role="img" aria-label="Sports">
            🏟️
          </span>{" "}
          Sports
        </button>
        <button
          className={`map-category-button flex items-center gap-2 ${activeCategory === "other" ? "active" : ""}`}
          onClick={() => handleCategoryChange("other")}
        >
          <span role="img" aria-label="Other">
            ✨
          </span>{" "}
          Other
        </button>
      </div>
    </div>
  );
};

export default EventMap;
