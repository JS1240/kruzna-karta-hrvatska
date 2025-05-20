import React, { useState, useEffect } from 'react';
import { Link, useLocation } from 'react-router-dom';
import { Heart } from 'lucide-react';
import Auth from './Auth';
import Logo from './Logo';
import { useFavorites } from '../FavoritesContext';

const Header = () => {
  const location = useLocation();
  const [isMenuOpen, setIsMenuOpen] = useState(false);
  const { favorites } = useFavorites();
  const [isLoggedIn, setIsLoggedIn] = useState(false); // Example state for login status

  // Mock function to simulate checking if user is logged in
  const checkLoginStatus = () => {
    // Replace this with your actual authentication check
    const token = localStorage.getItem('authToken');
    setIsLoggedIn(!!token);
  };

  useEffect(() => {
    checkLoginStatus();
  }, []);

  const toggleMenu = () => {
    setIsMenuOpen(!isMenuOpen);
  };

  const closeMenu = () => {
    setIsMenuOpen(false);
  };

  const hasFavorites = favorites && Object.keys(favorites).length > 0;
  const favoriteCount = favorites ? Object.keys(favorites).length : 0;

  return (
    <header className="bg-white shadow-md">
      <div className="container mx-auto px-4 py-4">
        <div className="flex justify-between items-center">
          {/* Logo and Title */}
          <Link to="/" className="flex items-center gap-2">
            <Logo className="h-8 w-8" />
            <h1 className="text-xl font-bold text-navy-blue">Visit Croatia</h1>
          </Link>

          {/* Navigation */}
          <nav className="hidden md:flex items-center space-x-6">
            <Link
              to="/"
              className={`text-gray-600 hover:text-navy-blue transition-colors ${
                location.pathname === '/' ? 'text-navy-blue font-medium' : ''
              }`}
            >
              Home
            </Link>
            <Link
              to="/upcoming"
              className={`text-gray-600 hover:text-navy-blue transition-colors ${
                location.pathname === '/upcoming' ? 'text-navy-blue font-medium' : ''
              }`}
            >
              Upcoming
            </Link>
            <Link
              to="/venues"
              className={`text-gray-600 hover:text-navy-blue transition-colors ${
                location.pathname === '/venues' ? 'text-navy-blue font-medium' : ''
              }`}
            >
              Venues
            </Link>
            <Link
              to="/about"
              className={`text-gray-600 hover:text-navy-blue transition-colors ${
                location.pathname === '/about' ? 'text-navy-blue font-medium' : ''
              }`}
            >
              About
            </Link>
            {isLoggedIn && (
              <Link
                to="/favorites"
                className={`text-gray-600 hover:text-navy-blue transition-colors relative ${
                  location.pathname === '/favorites' ? 'text-navy-blue font-medium' : ''
                }`}
              >
                <Heart className={`h-5 w-5 ${hasFavorites ? 'fill-red-500 stroke-red-500' : ''}`} />
                {hasFavorites && (
                  <span className="absolute -top-1 -right-1 bg-red-500 text-white text-xs rounded-full h-4 w-4 flex items-center justify-center">
                    {favoriteCount}
                  </span>
                )}
              </Link>
            )}
          </nav>

          {/* Authentication */}
          <Auth />

          {/* Mobile Menu Button */}
          <button
            onClick={toggleMenu}
            className="md:hidden text-navy-blue focus:outline-none"
          >
            <svg
              className="h-6 w-6"
              fill="none"
              stroke="currentColor"
              viewBox="0 0 24 24"
              xmlns="http://www.w3.org/2000/svg"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth="2"
                d="M4 6h16M4 12h16M4 18h16"
              />
            </svg>
          </button>
        </div>

        {/* Mobile Menu */}
        <div className={`md:hidden ${isMenuOpen ? 'block' : 'none'}`}>
          <div className="bg-light-blue p-4 rounded-md mt-2">
            <Link
              to="/"
              className="block text-gray-600 hover:text-navy-blue py-2 transition-colors"
              onClick={closeMenu}
            >
              Home
            </Link>
            <Link
              to="/upcoming"
              className="block text-gray-600 hover:text-navy-blue py-2 transition-colors"
              onClick={closeMenu}
            >
              Upcoming
            </Link>
            <Link
              to="/venues"
              className="block text-gray-600 hover:text-navy-blue py-2 transition-colors"
              onClick={closeMenu}
            >
              Venues
            </Link>
            <Link
              to="/about"
              className="block text-gray-600 hover:text-navy-blue py-2 transition-colors"
              onClick={closeMenu}
            >
              About
            </Link>
            {isLoggedIn && (
              <Link
                to="/favorites"
                className="block text-gray-600 hover:text-navy-blue py-2 transition-colors"
                onClick={closeMenu}
              >
                Favorites
              </Link>
            )}
          </div>
        </div>
      </div>
    </header>
  );
};

export default Header;
