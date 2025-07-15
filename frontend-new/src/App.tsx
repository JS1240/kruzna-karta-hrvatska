import React, { useState } from 'react';
import { QueryClientProvider } from '@tanstack/react-query';
import { Menu, X, MapIcon, Calendar } from 'lucide-react';
import { EventMap } from '@/components/map/EventMap';
import { FilterPanel } from '@/components/map/FilterPanel';
import { FeaturedEvents } from '@/components/events/FeaturedEvents';
import { LatestEvents } from '@/components/events/LatestEvents';
import { useEvents } from '@/hooks/useEvents';
import { useMapFilters } from '@/hooks/useMapFilters';
import { Event } from '@/types/event';
import { queryClient } from '@/lib/api';
import { sampleEvents } from '@/components/map/SampleEvents';

const Header: React.FC = () => {
  const [isMenuOpen, setIsMenuOpen] = useState(false);

  return (
    <header className="bg-white shadow-sm border-b border-gray-200">
      <div className="container mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex items-center justify-between h-16">
          <div className="flex items-center gap-2">
            <MapIcon className="w-8 h-8 text-primary-500" />
            <h1 className="text-2xl font-bold text-gray-900">
              Kružna Karta Hrvatska
            </h1>
          </div>
          
          <nav className="hidden md:flex items-center gap-6">
            <a href="#map" className="text-gray-600 hover:text-primary-600 transition-colors">
              Map
            </a>
            <a href="#featured" className="text-gray-600 hover:text-primary-600 transition-colors">
              Featured
            </a>
            <a href="#latest" className="text-gray-600 hover:text-primary-600 transition-colors">
              Latest
            </a>
          </nav>
          
          <button
            onClick={() => setIsMenuOpen(!isMenuOpen)}
            className="md:hidden p-2 rounded-md text-gray-400 hover:text-gray-500 hover:bg-gray-100"
          >
            {isMenuOpen ? <X className="w-6 h-6" /> : <Menu className="w-6 h-6" />}
          </button>
        </div>
        
        {/* Mobile menu */}
        {isMenuOpen && (
          <div className="md:hidden py-4 border-t border-gray-200">
            <nav className="flex flex-col gap-4">
              <a href="#map" className="text-gray-600 hover:text-primary-600 transition-colors">
                Map
              </a>
              <a href="#featured" className="text-gray-600 hover:text-primary-600 transition-colors">
                Featured
              </a>
              <a href="#latest" className="text-gray-600 hover:text-primary-600 transition-colors">
                Latest
              </a>
            </nav>
          </div>
        )}
      </div>
    </header>
  );
};

const HeroSection: React.FC = () => {
  return (
    <section className="bg-gradient-to-br from-primary-50 to-accent-50 py-16">
      <div className="container mx-auto px-4 sm:px-6 lg:px-8">
        <div className="text-center max-w-3xl mx-auto">
          <h2 className="text-4xl md:text-5xl font-bold text-gray-900 mb-6">
            Discover Amazing Events in Croatia
          </h2>
          <p className="text-xl text-gray-600 mb-8">
            From concerts and festivals to cultural events and nightlife - 
            find everything happening in your city and beyond.
          </p>
          <div className="flex flex-col sm:flex-row gap-4 justify-center">
            <a
              href="#map"
              className="btn btn-primary px-8 py-4 text-lg font-medium"
            >
              <MapIcon className="w-5 h-5 mr-2" />
              Explore Map
            </a>
            <a
              href="#featured"
              className="btn btn-outline px-8 py-4 text-lg font-medium"
            >
              <Calendar className="w-5 h-5 mr-2" />
              Featured Events
            </a>
          </div>
        </div>
      </div>
    </section>
  );
};

const HomePage: React.FC = () => {
  const [, setSelectedEvent] = useState<Event | null>(null);
  const [isFilterOpen, setIsFilterOpen] = useState(false);
  const { filters, updateFilter, clearAllFilters, searchParams } = useMapFilters();
  
  const { data: eventsResponse, isLoading: eventsLoading } = useEvents(searchParams);
  const apiEvents = eventsResponse?.events || [];
  
  // Use sample events if no API events are available for testing
  const events = apiEvents.length > 0 ? apiEvents : sampleEvents;

  const handleEventClick = (event: Event) => {
    setSelectedEvent(event);
    // Here you would typically open a modal or navigate to event details
    console.log('Event clicked:', event);
  };

  return (
    <div className="min-h-screen bg-gray-50">
      <Header />
      <HeroSection />
      
      {/* Map Section */}
      <section id="map" className="py-8">
        <div className="max-w-full mx-auto px-4 sm:px-6 lg:px-8">
          <div className="mb-8">
            <h2 className="text-3xl font-bold text-gray-900 mb-4">
              Events Map
            </h2>
            <p className="text-gray-600 mb-6">
              Explore events happening across Croatia on our interactive map
            </p>
          </div>
          
          {/* Filters Above Map */}
          <div className="mb-6">
            <FilterPanel
              filters={filters}
              onFilterChange={updateFilter}
              onClearFilters={clearAllFilters}
              isOpen={isFilterOpen}
              onToggle={() => setIsFilterOpen(!isFilterOpen)}
            />
          </div>
        </div>

        {/* Map with horizontal margins */}
        <div className="w-full px-4 sm:px-6 lg:px-8">
          <EventMap
            events={events}
            loading={false}
            onEventClick={handleEventClick}
            height="850px"
            className="w-full"
          />
        </div>
      </section>
      
      {/* Featured Events Section */}
      <section id="featured" className="bg-white">
        <FeaturedEvents onEventClick={handleEventClick} />
      </section>
      
      {/* Latest Events Section */}
      <section id="latest">
        <LatestEvents 
          onEventClick={handleEventClick}
          maxEvents={8}
          showPagination={true}
        />
      </section>
      
      {/* Footer */}
      <footer className="bg-secondary-900 text-white py-12">
        <div className="container mx-auto px-4 sm:px-6 lg:px-8">
          <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
            <div>
              <div className="flex items-center gap-2 mb-4">
                <MapIcon className="w-8 h-8 text-primary-400" />
                <h3 className="text-xl font-bold">Kružna Karta Hrvatska</h3>
              </div>
              <p className="text-gray-300">
                Your ultimate guide to events happening across Croatia. 
                Discover, explore, and never miss out on what's happening in your area.
              </p>
            </div>
            
            <div>
              <h4 className="text-lg font-semibold mb-4">Quick Links</h4>
              <ul className="space-y-2">
                <li><a href="#map" className="text-gray-300 hover:text-white transition-colors">Event Map</a></li>
                <li><a href="#featured" className="text-gray-300 hover:text-white transition-colors">Featured Events</a></li>
                <li><a href="#latest" className="text-gray-300 hover:text-white transition-colors">Latest Events</a></li>
              </ul>
            </div>
            
            <div>
              <h4 className="text-lg font-semibold mb-4">Cities</h4>
              <ul className="space-y-2 text-gray-300">
                <li>Zagreb</li>
                <li>Split</li>
                <li>Rijeka</li>
                <li>Dubrovnik</li>
                <li>Zadar</li>
              </ul>
            </div>
          </div>
          
          <div className="border-t border-gray-700 mt-8 pt-8 text-center text-gray-400">
            <p>&copy; 2024 Kružna Karta Hrvatska. All rights reserved.</p>
          </div>
        </div>
      </footer>
    </div>
  );
};

function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <HomePage />
    </QueryClientProvider>
  );
}

export default App;
