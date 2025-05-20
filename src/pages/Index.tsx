import React, { useState } from 'react';
import Header from '@/components/Header';
import EventMap from '@/components/EventMap';
import FeaturedEvents from '@/components/FeaturedEvents';
import LatestNews from '@/components/LatestNews';
import AboutCroatia from '@/components/AboutCroatia';
import Footer from '@/components/Footer';
import { SearchIcon, CalendarIcon, MapPinIcon, HeartIcon } from 'lucide-react';
import EventCarousel from '@/components/EventCarousel';

const Index = () => {
  const [searchTerm, setSearchTerm] = useState('');
  
  return (
    <div className="min-h-screen flex flex-col bg-cream">
      <Header />
      
      <main className="flex-grow container mx-auto px-4 py-8">
        <section className="mb-12">
          <div className="flex flex-col md:flex-row items-center justify-between gap-6">
            <div className="md:w-1/2">
              <h1 className="text-4xl md:text-5xl lg:text-6xl font-bold text-navy-blue mb-4 font-sreda">
                Discover <span className="text-medium-blue">Events</span> in Croatia
              </h1>
              <p className="text-lg text-gray-700 mb-6 font-josefin">
                Explore concerts, workouts, meet-ups, conferences, and parties all across Croatia with our interactive map.
              </p>
              
              <div className="relative">
                <input 
                  type="text" 
                  placeholder="Search events, venues or cities..." 
                  className="w-full py-3 px-4 pr-12 bg-white border border-light-blue rounded-lg shadow-sm focus:outline-none focus:ring-2 focus:ring-navy-blue"
                  value={searchTerm}
                  onChange={(e) => setSearchTerm(e.target.value)}
                />
                <div className="absolute right-3 top-1/2 transform -translate-y-1/2">
                  <SearchIcon className="text-medium-blue" size={20} />
                </div>
              </div>
              
              <div className="mt-6 flex flex-wrap gap-4">
                <div className="flex items-center gap-2 text-sm text-gray-700">
                  <CalendarIcon className="text-navy-blue" size={16} />
                  <span>Updated Daily</span>
                </div>
                <div className="flex items-center gap-2 text-sm text-gray-700">
                  <MapPinIcon className="text-navy-blue" size={16} />
                  <span>All Croatian Cities</span>
                </div>
                <div className="flex items-center gap-2 text-sm text-gray-700">
                  <HeartIcon className="text-navy-blue" size={16} />
                  <span>Curated Selection</span>
                </div>
              </div>
            </div>
            
            <div className="md:w-1/2">
              <EventCarousel
                events={[
                  {
                    id: '1',
                    title: 'Zagreb Summer Festival',
                    image: '/event-images/concert.jpg',
                    date: 'June 10, 2025',
                    location: 'Zagreb',
                  },
                  {
                    id: '2',
                    title: 'Dubrovnik Night Run',
                    image: '/event-images/workout.jpg',
                    date: 'June 12, 2025',
                    location: 'Dubrovnik',
                  },
                  {
                    id: '3',
                    title: 'Split Tech Meetup',
                    image: '/event-images/meetup.jpg',
                    date: 'June 15, 2025',
                    location: 'Split',
                  },
                  {
                    id: '4',
                    title: 'Pula Party Weekend',
                    image: '/event-images/party.jpg',
                    date: 'June 20, 2025',
                    location: 'Pula',
                  },
                  {
                    id: '5',
                    title: 'Rijeka Business Conference',
                    image: '/event-images/conference.jpg',
                    date: 'June 25, 2025',
                    location: 'Rijeka',
                  },
                ]}
                speed={40}
              />
            </div>
          </div>
        </section>
        
        <section className="mb-8">
          <h2 className="text-3xl font-bold mb-6 font-sreda text-navy-blue">
            Find Events on the Map
          </h2>
          
          <EventMap />
        </section>
        
        <FeaturedEvents />
        
        <LatestNews />
        
        <AboutCroatia />
      </main>
      
      <Footer />
    </div>
  );
};

export default Index;
