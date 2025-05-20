
import React, { useState } from 'react';
import { Link } from 'react-router-dom';
import { Flag } from 'lucide-react';
import Auth from './Auth';

const Header = () => {
  const [language, setLanguage] = useState<'en' | 'hr'>('en');

  return (
    <header className="bg-navy-blue text-white py-4">
      <div className="container mx-auto flex items-center justify-between">
        <Link to="/" className="flex items-center space-x-2">
          <span className="text-2xl font-sreda font-bold">EventMap</span>
          <span className="text-medium-blue font-josefin">Croatia</span>
        </Link>
        
        <nav className="hidden md:flex items-center space-x-8">
          <Link to="/" className="font-josefin hover:text-medium-blue transition-colors">Map</Link>
          <Link to="/popular" className="font-josefin hover:text-medium-blue transition-colors">Popular</Link>
          <Link to="/upcoming" className="font-josefin hover:text-medium-blue transition-colors">Upcoming</Link>
          <Link to="/venues" className="font-josefin hover:text-medium-blue transition-colors">Venues</Link>
          <Link to="/about" className="font-josefin hover:text-medium-blue transition-colors">About</Link>
        </nav>
        
        <div className="flex items-center space-x-4">
          <div className="flex items-center space-x-2">
            <button 
              onClick={() => setLanguage('en')} 
              className={`language-toggle ${language === 'en' ? 'active' : ''}`}
              aria-label="English"
            >
              <img src="/usa-flag.svg" alt="English" className="w-full h-full object-cover" />
            </button>
            <button 
              onClick={() => setLanguage('hr')} 
              className={`language-toggle ${language === 'hr' ? 'active' : ''}`}
              aria-label="Hrvatski"
            >
              <img src="/croatia-flag.svg" alt="Hrvatski" className="w-full h-full object-cover" />
            </button>
          </div>
          
          <Auth />
        </div>
      </div>
    </header>
  );
};

export default Header;
