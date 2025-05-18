
import React, { useEffect, useRef, useState } from 'react';
import mapboxgl from 'mapbox-gl';
import 'mapbox-gl/dist/mapbox-gl.css';
import { Music, Dumbbell, Users, CalendarDays, PartyPopper } from 'lucide-react';
import { Popover, PopoverContent, PopoverTrigger } from "@/components/ui/popover";

interface Event {
  id: number;
  title: string;
  description: string;
  category: 'concert' | 'workout' | 'meetup' | 'conference' | 'party';
  location: [number, number];
  date: string;
  time: string;
  image: string;
  ticketLink: string;
  sourceWebsite: string;
  venue: string;
  price: string;
}

const EventMap = () => {
  const mapContainer = useRef<HTMLDivElement>(null);
  const map = useRef<mapboxgl.Map | null>(null);
  const [mapLoaded, setMapLoaded] = useState(false);
  const [activeCategory, setActiveCategory] = useState<string | null>(null);
  const [selectedLocation, setSelectedLocation] = useState<string | null>(null);
  const [selectedPrice, setSelectedPrice] = useState<string | null>(null);
  const [selectedDate, setSelectedDate] = useState<string | null>(null);
  
  // Example events data
  const events: Event[] = [
    {
      id: 1,
      title: "Nina Badrić Concert",
      description: "Enjoy the wonderful voice of Nina Badrić in this special summer concert.",
      category: "concert",
      location: [16.4401, 43.5081], // Split
      date: "2025-06-15",
      time: "20:00",
      image: "/event-images/concert.jpg",
      ticketLink: "https://entrio.hr/",
      sourceWebsite: "entrio.hr",
      venue: "Poljud Stadium",
      price: "30-50€"
    },
    {
      id: 2,
      title: "Zagreb Bootcamp Challenge",
      description: "Join us for an intensive workout session in the heart of Zagreb.",
      category: "workout",
      location: [15.9819, 45.8150], // Zagreb
      date: "2025-05-20",
      time: "09:00",
      image: "/event-images/workout.jpg",
      ticketLink: "https://meetup.com/",
      sourceWebsite: "meetup.com",
      venue: "Jarun Lake",
      price: "15€"
    },
    {
      id: 3,
      title: "Dubrovnik Tech Meetup",
      description: "Network with tech professionals and enthusiasts from the region.",
      category: "meetup",
      location: [18.0944, 42.6507], // Dubrovnik
      date: "2025-07-10",
      time: "18:00",
      image: "/event-images/meetup.jpg",
      ticketLink: "https://meetup.com/",
      sourceWebsite: "meetup.com",
      venue: "Hotel Excelsior",
      price: "Free"
    },
    {
      id: 4,
      title: "Adriatic Business Conference",
      description: "Annual conference focusing on business opportunities in the Adriatic region.",
      category: "conference",
      location: [14.4426, 45.3271], // Rijeka
      date: "2025-09-05",
      time: "10:00",
      image: "/event-images/conference.jpg",
      ticketLink: "https://eventim.hr/",
      sourceWebsite: "eventim.hr",
      venue: "Rijeka Convention Center",
      price: "100-200€"
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
      price: "25-40€"
    }
  ];
  
  useEffect(() => {
    // Initialize map only if it hasn't been created yet
    if (map.current) return;
    
    // For demo purposes, you'd need to add your Mapbox token here
    // In a production app, this would be stored securely in environment variables
    mapboxgl.accessToken = 'pk.YOUR_MAPBOX_TOKEN';
    
    map.current = new mapboxgl.Map({
      container: mapContainer.current!,
      style: 'mapbox://styles/mapbox/light-v11',
      center: [16.4, 44.5], // Center of Croatia
      zoom: 7,
      maxBounds: [
        [13.2, 42.1], // Southwest coordinates
        [19.4, 46.9]  // Northeast coordinates
      ]
    });
    
    map.current.on('load', () => {
      if (!map.current) return;
      
      // Add Croatia outline
      map.current.addSource('croatia-outline', {
        type: 'geojson',
        data: {
          type: 'Feature',
          geometry: {
            type: 'Polygon',
            // This is a simplified polygon for Croatia's borders
            coordinates: [[
              [13.6569, 45.1583],
              [16.2, 46.8],
              [19.4, 46.4],
              [19.3, 45.2],
              [18.8, 45.1],
              [19.0, 44.8],
              [19.4, 44.3],
              [19.2, 44.0],
              [18.8, 43.2],
              [18.0, 42.6],
              [17.5, 42.9],
              [16.1, 43.5],
              [15.2, 44.2],
              [14.3, 45.2],
              [13.6, 44.8],
              [13.6569, 45.1583]
            ]]
          },
          properties: {}
        }
      });
      
      map.current.addLayer({
        id: 'croatia-fill',
        type: 'fill',
        source: 'croatia-outline',
        paint: {
          'fill-color': 'rgba(203, 220, 235, 0.5)', // Light blue from your palette with transparency
          'fill-outline-color': '#133E87' // Navy blue from your palette
        }
      });
      
      // Add a black overlay for areas outside Croatia
      map.current.addLayer({
        id: 'outside-croatia',
        type: 'background',
        paint: {
          'background-color': 'rgba(0, 0, 0, 0.5)'
        },
        filter: ['!=', 'name', 'Croatia']
      }, 'croatia-fill');
      
      // Now Croatia's fill will be visible above the black background
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
    const existingMarkers = document.querySelectorAll('.mapboxgl-marker');
    existingMarkers.forEach((marker) => marker.remove());
    
    // Filter events based on selected filters
    let filteredEvents = [...events];
    
    if (activeCategory) {
      filteredEvents = filteredEvents.filter(event => event.category === activeCategory);
    }
    
    if (selectedLocation) {
      // This is simplified - in a real app, you'd match by city or region
      filteredEvents = filteredEvents.filter(event => {
        const [lng, lat] = event.location;
        // Example: check if near Zagreb (simplified)
        return selectedLocation === 'Zagreb' ? lat > 45.5 : true;
      });
    }
    
    if (selectedPrice) {
      // Simple price filter for demo
      filteredEvents = filteredEvents.filter(event => {
        if (selectedPrice === 'free') return event.price.toLowerCase().includes('free');
        if (selectedPrice === 'under25') return !event.price.includes('Free') && parseInt(event.price) < 25;
        if (selectedPrice === 'over25') return parseInt(event.price) >= 25;
        return true;
      });
    }
    
    if (selectedDate) {
      // Simple date filter
      filteredEvents = filteredEvents.filter(event => event.date === selectedDate);
    }
    
    // Add markers for filtered events
    filteredEvents.forEach(event => {
      // Create custom marker element
      const el = document.createElement('div');
      el.className = 'marker';
      el.style.width = '30px';
      el.style.height = '30px';
      el.style.borderRadius = '50%';
      el.style.cursor = 'pointer';
      el.style.backgroundSize = 'contain';
      el.style.backgroundRepeat = 'no-repeat';
      el.style.backgroundPosition = 'center';
      el.style.backgroundColor = '#FFFFFF';
      el.style.boxShadow = '0 2px 10px rgba(0, 0, 0, 0.3)';
      el.style.display = 'flex';
      el.style.alignItems = 'center';
      el.style.justifyContent = 'center';
      
      // Create icon based on category
      const iconEl = document.createElement('div');
      iconEl.className = 'marker-icon';
      iconEl.style.width = '18px';
      iconEl.style.height = '18px';
      iconEl.style.color = '#133E87';
      
      switch (event.category) {
        case 'concert':
          iconEl.innerHTML = `<svg xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="10"/><path d="M12 6v12"/><path d="M6 12h12"/></svg>`;
          break;
        case 'workout':
          iconEl.innerHTML = `<svg xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="m6.5 6.5 11 11"/><path d="m21 21-1-1"/><path d="m3 3 1 1"/><path d="m18 22 4-4"/><path d="m2 6 4-4"/><path d="m3 10 7-7"/><path d="m14 21 7-7"/></svg>`;
          break;
        case 'meetup':
          iconEl.innerHTML = `<svg xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M18 21a8 8 0 0 0-16 0"/><circle cx="10" cy="8" r="5"/><path d="M22 20c-2 2-4-1-4-3-3 2-3 6 0 6 1.8 0 3-1.5 4-3z"/></svg>`;
          break;
        case 'conference':
          iconEl.innerHTML = `<svg xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><rect width="20" height="14" x="2" y="7" rx="2"/><path d="M16 2v5"/><path d="M8 2v5"/><path d="M2 12h20"/></svg>`;
          break;
        case 'party':
          iconEl.innerHTML = `<svg xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M5.8 11.3 2 22l10.7-3.79"/><path d="M4 3h.01"/><path d="M22 8h.01"/><path d="M15 2h.01"/><path d="M22 20h.01"/><path d="m22 2-2.24.75a2.9 2.9 0 0 0-1.96 3.12v0c.1.86-.57 1.63-1.45 1.63h-.38c-.86 0-1.6.6-1.76 1.44L14 10"/><path d="m22 13-.82-.33c-.86-.34-1.82.2-1.98 1.11v0c-.11.7-.72 1.22-1.43 1.22H17"/><path d="m11 2 .33.82c.34.86-.2 1.82-1.11 1.98v0C9.52 4.9 9 5.52 9 6.23V7"/><path d="M11 13c1.93 1.93 2.83 4.17 2 5-.83.83-3.07-.07-5-2-1.93-1.93-2.83-4.17-2-5 .83-.83 3.07.07 5 2Z"/></svg>`;
          break;
      }
      
      el.appendChild(iconEl);
      
      // Create and add the marker
      const marker = new mapboxgl.Marker(el)
        .setLngLat(event.location)
        .addTo(map.current!);
      
      // Create popup content
      const popupContent = document.createElement('div');
      popupContent.className = 'popup-content';
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
        maxWidth: '320px'
      }).setDOMContent(popupContent);
      
      // Show popup on hover
      el.addEventListener('mouseenter', () => {
        marker.setPopup(popup);
        popup.addTo(map.current!);
      });
      
      // Optional: Close popup on mouseleave
      el.addEventListener('mouseleave', () => {
        setTimeout(() => {
          if (!popup.isOpen()) return;
          popup.remove();
        }, 300);
      });
    });
  }, [mapLoaded, activeCategory, selectedLocation, selectedPrice, selectedDate]);
  
  // Functions to handle filter changes
  const handleCategoryChange = (category: string | null) => {
    setActiveCategory(category === activeCategory ? null : category);
  };
  
  return (
    <div className="relative my-6">
      {/* Filter controls */}
      <div className="bg-white rounded-lg shadow-md p-4 mb-4 flex flex-wrap gap-4">
        <div className="w-full md:w-auto">
          <label htmlFor="location-filter" className="block text-sm font-medium text-gray-700 mb-1">
            Location
          </label>
          <select
            id="location-filter"
            className="w-full border border-gray-300 rounded-md py-2 px-3 bg-white focus:outline-none focus:ring-2 focus:ring-navy-blue"
            value={selectedLocation || ""}
            onChange={(e) => setSelectedLocation(e.target.value || null)}
          >
            <option value="">All Locations</option>
            <option value="Zagreb">Zagreb</option>
            <option value="Split">Split</option>
            <option value="Rijeka">Rijeka</option>
            <option value="Dubrovnik">Dubrovnik</option>
            <option value="Osijek">Osijek</option>
          </select>
        </div>
        
        <div className="w-full md:w-auto">
          <label htmlFor="price-filter" className="block text-sm font-medium text-gray-700 mb-1">
            Price
          </label>
          <select
            id="price-filter"
            className="w-full border border-gray-300 rounded-md py-2 px-3 bg-white focus:outline-none focus:ring-2 focus:ring-navy-blue"
            value={selectedPrice || ""}
            onChange={(e) => setSelectedPrice(e.target.value || null)}
          >
            <option value="">All Prices</option>
            <option value="free">Free</option>
            <option value="under25">Under 25€</option>
            <option value="over25">25€ and above</option>
          </select>
        </div>
        
        <div className="w-full md:w-auto">
          <label htmlFor="date-filter" className="block text-sm font-medium text-gray-700 mb-1">
            Date
          </label>
          <input
            id="date-filter"
            type="date"
            className="w-full border border-gray-300 rounded-md py-2 px-3 bg-white focus:outline-none focus:ring-2 focus:ring-navy-blue"
            value={selectedDate || ""}
            onChange={(e) => setSelectedDate(e.target.value || null)}
          />
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
          className={`map-category-button flex items-center gap-2 ${activeCategory === 'concert' ? 'active' : ''}`}
          onClick={() => handleCategoryChange('concert')}
        >
          <Music size={18} /> Concerts
        </button>
        <button 
          className={`map-category-button flex items-center gap-2 ${activeCategory === 'workout' ? 'active' : ''}`}
          onClick={() => handleCategoryChange('workout')}
        >
          <Dumbbell size={18} /> Workouts
        </button>
        <button 
          className={`map-category-button flex items-center gap-2 ${activeCategory === 'meetup' ? 'active' : ''}`}
          onClick={() => handleCategoryChange('meetup')}
        >
          <Users size={18} /> Meet-ups
        </button>
        <button 
          className={`map-category-button flex items-center gap-2 ${activeCategory === 'conference' ? 'active' : ''}`}
          onClick={() => handleCategoryChange('conference')}
        >
          <CalendarDays size={18} /> Conferences
        </button>
        <button 
          className={`map-category-button flex items-center gap-2 ${activeCategory === 'party' ? 'active' : ''}`}
          onClick={() => handleCategoryChange('party')}
        >
          <PartyPopper size={18} /> Parties
        </button>
      </div>
    </div>
  );
};

export default EventMap;
