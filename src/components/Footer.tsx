
import React from 'react';
import { Facebook, Instagram, Twitter, Linkedin, Mail, MapPin, Phone, Calendar, Users } from 'lucide-react';
import { Button } from '@/components/ui/button';

const Footer = () => {
  const currentYear = new Date().getFullYear();
  
  return (
    <footer className="bg-gradient-to-r from-navy-blue to-medium-blue">
      <div className="container mx-auto px-4 py-12">
        {/* Newsletter Section */}
        <div className="flex flex-col md:flex-row justify-between items-center bg-white/10 backdrop-blur-sm p-6 rounded-lg mb-10">
          <div className="mb-4 md:mb-0">
            <h3 className="text-white text-xl font-bold font-sreda">Subscribe to Our Newsletter</h3>
            <p className="text-white/80 font-josefin">Stay updated with latest events and offers</p>
          </div>
          <div className="flex flex-col sm:flex-row gap-3 w-full md:w-auto">
            <input 
              type="email" 
              placeholder="Your email" 
              className="px-4 py-2 rounded-md bg-white/20 text-white placeholder:text-white/60 border border-white/30 focus:outline-none focus:ring-2 focus:ring-white/50"
            />
            <Button variant="secondary" className="whitespace-nowrap font-josefin">
              Subscribe Now
            </Button>
          </div>
        </div>
        
        {/* Main Footer Columns */}
        <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-4 gap-8 mb-8">
          {/* Column 1: About */}
          <div>
            <h3 className="text-white font-bold text-lg mb-4 font-sreda">EventMap Croatia</h3>
            <p className="text-white/70 mb-4 font-josefin">
              Your ultimate guide to discovering events, concerts, and gatherings across beautiful Croatia.
            </p>
            <div className="flex gap-3">
              <a href="#" className="text-white/80 hover:text-white transition-colors p-2 bg-white/10 rounded-full">
                <Facebook size={18} />
              </a>
              <a href="#" className="text-white/80 hover:text-white transition-colors p-2 bg-white/10 rounded-full">
                <Instagram size={18} />
              </a>
              <a href="#" className="text-white/80 hover:text-white transition-colors p-2 bg-white/10 rounded-full">
                <Twitter size={18} />
              </a>
              <a href="#" className="text-white/80 hover:text-white transition-colors p-2 bg-white/10 rounded-full">
                <Linkedin size={18} />
              </a>
            </div>
          </div>
          
          {/* Column 2: Quick Links */}
          <div>
            <h3 className="text-white font-bold text-lg mb-4 font-sreda">Quick Links</h3>
            <ul className="space-y-2 text-white/70 font-josefin">
              <li>
                <a href="#" className="hover:text-white transition-colors flex items-center gap-2">
                  <Calendar size={16} />
                  <span>Events Calendar</span>
                </a>
              </li>
              <li>
                <a href="#" className="hover:text-white transition-colors flex items-center gap-2">
                  <MapPin size={16} />
                  <span>Popular Venues</span>
                </a>
              </li>
              <li>
                <a href="#" className="hover:text-white transition-colors flex items-center gap-2">
                  <Users size={16} />
                  <span>For Organizers</span>
                </a>
              </li>
              <li>
                <a href="#" className="hover:text-white transition-colors flex items-center gap-2">
                  <Mail size={16} />
                  <span>Contact Us</span>
                </a>
              </li>
            </ul>
          </div>
          
          {/* Column 3: Resources */}
          <div>
            <h3 className="text-white font-bold text-lg mb-4 font-sreda">Resources</h3>
            <ul className="space-y-2 text-white/70 font-josefin">
              <li><a href="#" className="hover:text-white transition-colors">Travel Guide</a></li>
              <li><a href="#" className="hover:text-white transition-colors">City Guides</a></li>
              <li><a href="#" className="hover:text-white transition-colors">Transportation</a></li>
              <li><a href="#" className="hover:text-white transition-colors">Accommodations</a></li>
              <li><a href="#" className="hover:text-white transition-colors">Local Cuisine</a></li>
            </ul>
          </div>
          
          {/* Column 4: Legal */}
          <div>
            <h3 className="text-white font-bold text-lg mb-4 font-sreda">Legal</h3>
            <ul className="space-y-2 text-white/70 font-josefin">
              <li><a href="#" className="hover:text-white transition-colors">Terms of Service</a></li>
              <li><a href="#" className="hover:text-white transition-colors">Privacy Policy</a></li>
              <li><a href="#" className="hover:text-white transition-colors">Cookie Policy</a></li>
              <li><a href="#" className="hover:text-white transition-colors">Accessibility</a></li>
              <li><a href="#" className="hover:text-white transition-colors">GDPR Compliance</a></li>
            </ul>
          </div>
        </div>
        
        {/* Contact Information */}
        <div className="border-t border-white/20 pt-6 pb-4">
          <div className="flex flex-col md:flex-row justify-between">
            <div className="flex flex-col sm:flex-row gap-6 mb-4 md:mb-0">
              <div className="flex items-center gap-2 text-white/80">
                <Mail size={16} />
                <a href="mailto:info@eventmap.hr" className="hover:text-white transition-colors">info@eventmap.hr</a>
              </div>
              <div className="flex items-center gap-2 text-white/80">
                <Phone size={16} />
                <a href="tel:+38512345678" className="hover:text-white transition-colors">+385 1 234 5678</a>
              </div>
              <div className="flex items-center gap-2 text-white/80">
                <MapPin size={16} />
                <span>Zagreb, Croatia</span>
              </div>
            </div>
            
            <div className="text-white/60 text-sm font-josefin">
              © {currentYear} EventMap Croatia. All Rights Reserved.
            </div>
          </div>
        </div>
      </div>
    </footer>
  );
};

export default Footer;
