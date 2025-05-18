
import React from 'react';
import Header from '@/components/Header';
import { MapPinIcon, CalendarIcon, Users, Globe, ArrowRight } from 'lucide-react';

const About = () => {
  return (
    <div className="min-h-screen flex flex-col bg-cream">
      <Header />
      
      <main className="flex-grow container mx-auto px-4 py-8">
        <section className="mb-12">
          <h1 className="text-4xl md:text-5xl font-bold text-navy-blue mb-6 font-sreda">
            About EventMap Croatia
          </h1>
          
          <div className="bg-white rounded-lg shadow-lg p-8 border border-light-blue">
            <div className="flex flex-col md:flex-row gap-8 items-center mb-8">
              <div className="md:w-1/2">
                <p className="text-lg mb-4">
                  EventMap Croatia is a comprehensive platform that aggregates events from various sources including entrio.hr, eventim.hr, and meetup.com to provide a unified view of what's happening across Croatia.
                </p>
                <p className="text-lg mb-4">
                  Our mission is to make it easy for locals and tourists alike to discover exciting events, from concerts and parties to professional conferences and fitness meetups.
                </p>
                <p className="text-lg">
                  With our interactive map, you can visually explore events by location and category, making it simple to find activities that match your interests wherever you are in Croatia.
                </p>
              </div>
              <div className="md:w-1/2">
                <img 
                  src="/about-image.jpg" 
                  alt="Croatia events" 
                  className="w-full h-auto rounded-lg shadow-md object-cover"
                  style={{ maxHeight: '400px' }}
                />
              </div>
            </div>
            
            <hr className="border-light-blue my-8" />
            
            <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
              <div>
                <h2 className="text-2xl font-bold mb-4 font-sreda text-navy-blue">Our Features</h2>
                
                <ul className="space-y-4">
                  <li className="flex items-start gap-3">
                    <div className="mt-1 bg-navy-blue rounded-full p-1 text-white">
                      <MapPinIcon size={18} />
                    </div>
                    <div>
                      <h3 className="font-bold font-josefin">Interactive Map</h3>
                      <p className="text-gray-700">Explore events across Croatia on our user-friendly map interface.</p>
                    </div>
                  </li>
                  
                  <li className="flex items-start gap-3">
                    <div className="mt-1 bg-navy-blue rounded-full p-1 text-white">
                      <CalendarIcon size={18} />
                    </div>
                    <div>
                      <h3 className="font-bold font-josefin">Daily Updates</h3>
                      <p className="text-gray-700">Our platform refreshes daily to ensure you have access to the latest events.</p>
                    </div>
                  </li>
                  
                  <li className="flex items-start gap-3">
                    <div className="mt-1 bg-navy-blue rounded-full p-1 text-white">
                      <Users size={18} />
                    </div>
                    <div>
                      <h3 className="font-bold font-josefin">Category Filters</h3>
                      <p className="text-gray-700">Easily filter events by category: concerts, workouts, meet-ups, conferences, and parties.</p>
                    </div>
                  </li>
                  
                  <li className="flex items-start gap-3">
                    <div className="mt-1 bg-navy-blue rounded-full p-1 text-white">
                      <Globe size={18} />
                    </div>
                    <div>
                      <h3 className="font-bold font-josefin">Multilingual Support</h3>
                      <p className="text-gray-700">Access our platform in both English and Croatian languages.</p>
                    </div>
                  </li>
                </ul>
              </div>
              
              <div>
                <h2 className="text-2xl font-bold mb-4 font-sreda text-navy-blue">How It Works</h2>
                
                <div className="space-y-6">
                  <div className="flex gap-4 items-center">
                    <div className="w-10 h-10 rounded-full bg-medium-blue text-white flex items-center justify-center font-bold flex-shrink-0">
                      1
                    </div>
                    <div className="flex-grow">
                      <h3 className="font-bold font-josefin">Data Collection</h3>
                      <p className="text-gray-700">We aggregate events from multiple trusted sources across Croatia.</p>
                    </div>
                  </div>
                  
                  <div className="flex items-center justify-center">
                    <ArrowRight className="text-medium-blue" />
                  </div>
                  
                  <div className="flex gap-4 items-center">
                    <div className="w-10 h-10 rounded-full bg-medium-blue text-white flex items-center justify-center font-bold flex-shrink-0">
                      2
                    </div>
                    <div className="flex-grow">
                      <h3 className="font-bold font-josefin">Processing & Categorization</h3>
                      <p className="text-gray-700">Events are processed, categorized, and geolocated for optimal mapping.</p>
                    </div>
                  </div>
                  
                  <div className="flex items-center justify-center">
                    <ArrowRight className="text-medium-blue" />
                  </div>
                  
                  <div className="flex gap-4 items-center">
                    <div className="w-10 h-10 rounded-full bg-medium-blue text-white flex items-center justify-center font-bold flex-shrink-0">
                      3
                    </div>
                    <div className="flex-grow">
                      <h3 className="font-bold font-josefin">Interactive Display</h3>
                      <p className="text-gray-700">Events are displayed on our interactive map with detailed information.</p>
                    </div>
                  </div>
                  
                  <div className="flex items-center justify-center">
                    <ArrowRight className="text-medium-blue" />
                  </div>
                  
                  <div className="flex gap-4 items-center">
                    <div className="w-10 h-10 rounded-full bg-medium-blue text-white flex items-center justify-center font-bold flex-shrink-0">
                      4
                    </div>
                    <div className="flex-grow">
                      <h3 className="font-bold font-josefin">Direct Access</h3>
                      <p className="text-gray-700">Users can click through to purchase tickets or get more information about events.</p>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </section>
        
        <section className="mb-12">
          <h2 className="text-3xl font-bold mb-6 font-sreda text-navy-blue">
            Our Team
          </h2>
          
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            <div className="bg-white rounded-lg shadow-lg overflow-hidden border border-light-blue">
              <img 
                src="/team-member-1.jpg" 
                alt="Team Member" 
                className="w-full h-64 object-cover"
              />
              <div className="p-6">
                <h3 className="text-xl font-bold mb-1 font-josefin text-navy-blue">Ana Horvat</h3>
                <p className="text-medium-blue mb-3">Founder & CEO</p>
                <p className="text-gray-700">Ana brings 10+ years of experience in event management and digital mapping.</p>
              </div>
            </div>
            
            <div className="bg-white rounded-lg shadow-lg overflow-hidden border border-light-blue">
              <img 
                src="/team-member-2.jpg" 
                alt="Team Member" 
                className="w-full h-64 object-cover"
              />
              <div className="p-6">
                <h3 className="text-xl font-bold mb-1 font-josefin text-navy-blue">Marko Kovač</h3>
                <p className="text-medium-blue mb-3">Lead Developer</p>
                <p className="text-gray-700">Marko is responsible for our interactive map and data integration systems.</p>
              </div>
            </div>
            
            <div className="bg-white rounded-lg shadow-lg overflow-hidden border border-light-blue">
              <img 
                src="/team-member-3.jpg" 
                alt="Team Member" 
                className="w-full h-64 object-cover"
              />
              <div className="p-6">
                <h3 className="text-xl font-bold mb-1 font-josefin text-navy-blue">Ivana Novak</h3>
                <p className="text-medium-blue mb-3">Content Manager</p>
                <p className="text-gray-700">Ivana curates our event database and ensures data accuracy across the platform.</p>
              </div>
            </div>
          </div>
        </section>
        
        <section>
          <h2 className="text-3xl font-bold mb-6 font-sreda text-navy-blue">
            Contact Us
          </h2>
          
          <div className="bg-white rounded-lg shadow-lg p-8 border border-light-blue">
            <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
              <div>
                <h3 className="text-xl font-bold mb-4 font-josefin text-navy-blue">Get in Touch</h3>
                <p className="mb-6">Have questions, suggestions, or want to partner with us? We'd love to hear from you!</p>
                
                <div className="space-y-4">
                  <div className="flex items-center gap-3">
                    <div className="bg-light-blue p-2 rounded-full text-navy-blue">
                      <MapPinIcon size={18} />
                    </div>
                    <span>Ilica 242, 10000 Zagreb, Croatia</span>
                  </div>
                  
                  <div className="flex items-center gap-3">
                    <div className="bg-light-blue p-2 rounded-full text-navy-blue">
                      <svg xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                        <path d="M22 16.92v3a2 2 0 0 1-2.18 2 19.79 19.79 0 0 1-8.63-3.07 19.5 19.5 0 0 1-6-6 19.79 19.79 0 0 1-3.07-8.67A2 2 0 0 1 4.11 2h3a2 2 0 0 1 2 1.72 12.84 12.84 0 0 0 .7 2.81 2 2 0 0 1-.45 2.11L8.09 9.91a16 16 0 0 0 6 6l1.27-1.27a2 2 0 0 1 2.11-.45 12.84 12.84 0 0 0 2.81.7A2 2 0 0 1 22 16.92z"></path>
                      </svg>
                    </div>
                    <span>+385 1 234 5678</span>
                  </div>
                  
                  <div className="flex items-center gap-3">
                    <div className="bg-light-blue p-2 rounded-full text-navy-blue">
                      <svg xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                        <rect width="20" height="16" x="2" y="4" rx="2"></rect>
                        <path d="m22 7-8.97 5.7a1.94 1.94 0 0 1-2.06 0L2 7"></path>
                      </svg>
                    </div>
                    <span>info@eventmapcroatia.com</span>
                  </div>
                </div>
              </div>
              
              <div>
                <h3 className="text-xl font-bold mb-4 font-josefin text-navy-blue">Send a Message</h3>
                
                <form className="space-y-4">
                  <div>
                    <label htmlFor="name" className="block text-sm font-medium text-gray-700 mb-1">Name</label>
                    <input 
                      type="text" 
                      id="name" 
                      className="w-full border border-light-blue rounded-md py-2 px-3 focus:outline-none focus:ring-2 focus:ring-navy-blue"
                    />
                  </div>
                  
                  <div>
                    <label htmlFor="email" className="block text-sm font-medium text-gray-700 mb-1">Email</label>
                    <input 
                      type="email" 
                      id="email" 
                      className="w-full border border-light-blue rounded-md py-2 px-3 focus:outline-none focus:ring-2 focus:ring-navy-blue"
                    />
                  </div>
                  
                  <div>
                    <label htmlFor="message" className="block text-sm font-medium text-gray-700 mb-1">Message</label>
                    <textarea 
                      id="message" 
                      rows={4}
                      className="w-full border border-light-blue rounded-md py-2 px-3 focus:outline-none focus:ring-2 focus:ring-navy-blue"
                    ></textarea>
                  </div>
                  
                  <button 
                    type="submit"
                    className="px-6 py-3 bg-navy-blue text-white rounded-md hover:bg-medium-blue transition-colors font-josefin"
                  >
                    Send Message
                  </button>
                </form>
              </div>
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

export default About;
