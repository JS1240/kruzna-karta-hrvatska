
import React, { useState } from 'react';
import Header from '@/components/Header';
import EventMap from '@/components/EventMap';
import { SearchIcon, CalendarIcon, MapPinIcon, HeartIcon, InfoIcon } from 'lucide-react';

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
              <img 
                src="/hero-image.jpg" 
                alt="Events in Croatia" 
                className="w-full h-auto rounded-lg shadow-xl object-cover"
                style={{ maxHeight: '400px' }}
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
        
        <section className="mb-12">
          <div className="bg-white rounded-lg shadow-lg p-6 border border-light-blue">
            <h2 className="text-2xl font-bold mb-4 font-sreda text-navy-blue flex items-center gap-2">
              <InfoIcon size={24} className="text-medium-blue" />
              About This Map
            </h2>
            <p className="text-gray-700 mb-4">
              Our interactive event map aggregates events from popular Croatian platforms including entrio.hr, eventim.hr and meetup.com. 
              We update the map daily to ensure you always have access to the latest events happening across Croatia.
            </p>
            <p className="text-gray-700">
              Use the filters above the map to find specific events by location, price range, or date. Click on the category buttons below the map to focus on a particular type of event. 
              Hover over any event marker to see details and access links to buy tickets or learn more.
            </p>
          </div>
        </section>
        
        <section className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          <div className="bg-white rounded-lg shadow-lg overflow-hidden border border-light-blue hover:shadow-xl transition-shadow">
            <div className="h-48 bg-navy-blue flex items-center justify-center text-white">
              <CalendarIcon size={64} />
            </div>
            <div className="p-6">
              <h3 className="text-xl font-bold mb-2 font-josefin text-navy-blue">Featured Events</h3>
              <p className="text-gray-700">Discover our selection of must-attend events happening across Croatia.</p>
              <button className="mt-4 px-4 py-2 bg-medium-blue text-white rounded-md hover:bg-navy-blue transition-colors">
                Explore
              </button>
            </div>
          </div>
          
          <div className="bg-white rounded-lg shadow-lg overflow-hidden border border-light-blue hover:shadow-xl transition-shadow">
            <div className="h-48 bg-medium-blue flex items-center justify-center text-white">
              <InfoIcon size={64} />
            </div>
            <div className="p-6">
              <h3 className="text-xl font-bold mb-2 font-josefin text-navy-blue">About Croatia</h3>
              <p className="text-gray-700">Learn more about the beautiful country of Croatia and its vibrant culture.</p>
              <button className="mt-4 px-4 py-2 bg-navy-blue text-white rounded-md hover:bg-medium-blue transition-colors">
                Learn More
              </button>
            </div>
          </div>
          
          <div className="bg-white rounded-lg shadow-lg overflow-hidden border border-light-blue hover:shadow-xl transition-shadow">
            <div className="h-48 bg-light-blue flex items-center justify-center text-navy-blue">
              <HeartIcon size={64} />
            </div>
            <div className="p-6">
              <h3 className="text-xl font-bold mb-2 font-josefin text-navy-blue">Popular Venues</h3>
              <p className="text-gray-700">Explore the most popular event venues and locations throughout Croatia.</p>
              <button className="mt-4 px-4 py-2 bg-medium-blue text-white rounded-md hover:bg-navy-blue transition-colors">
                View Venues
              </button>
            </div>
          </div>
        </section>
      </main>
      
      <footer className="bg-navy-blue text-white py-8 mt-16">
        <div className="container mx-auto px-4">
          <div className="flex flex-col md:flex-row justify-between items-center">
            <div className="mb-6 md:mb-0">
              <h2 className="text-2xl font-bold mb-2 font-sreda">EventMap Croatia</h2>
              <p className="text-sm text-medium-blue">© {new Date().getFullYear()} All Rights Reserved</p>
            </div>
            
            <div className="flex gap-8">
              <div>
                <h3 className="font-bold mb-2 font-josefin">Information</h3>
                <ul className="space-y-1 text-sm">
                  <li><a href="#" className="hover:text-medium-blue transition-colors">About Us</a></li>
                  <li><a href="#" className="hover:text-medium-blue transition-colors">Contact</a></li>
                  <li><a href="#" className="hover:text-medium-blue transition-colors">Privacy Policy</a></li>
                </ul>
              </div>
              
              <div>
                <h3 className="font-bold mb-2 font-josefin">Follow Us</h3>
                <ul className="space-y-1 text-sm">
                  <li><a href="#" className="hover:text-medium-blue transition-colors">Facebook</a></li>
                  <li><a href="#" className="hover:text-medium-blue transition-colors">Instagram</a></li>
                  <li><a href="#" className="hover:text-medium-blue transition-colors">Twitter</a></li>
                </ul>
              </div>
            </div>
          </div>
        </div>
      </footer>
    </div>
  );
};

export default Index;
