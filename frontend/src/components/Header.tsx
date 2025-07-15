import React, { useState, useEffect } from "react";
import { Link, useLocation } from "react-router-dom";
import {
  Moon,
  Sun,
  Bookmark,
  Bookmark as BookmarkFilled,
  Sun as SunFilled,
  Moon as MoonFilled,
  Home,
  Calendar,
  MapPin,
  Heart,
  User,
} from "lucide-react";
import { useTheme } from "./ThemeProvider";
import { Button } from "./ui/button";
import { useLanguage } from "../contexts/LanguageContext";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from "./ui/dropdown-menu";
import Logo from "./Logo";
import Auth from "./Auth";
import NotificationCenter from "./NotificationCenter";
import { MobileNavigation, detectTouchDevice } from "./mobile";

const Header = () => {
  const [mounted, setMounted] = useState(false);
  const { theme, setTheme, resolvedTheme } = useTheme();
  const location = useLocation();
  const { language, setLanguage, t } = useLanguage();

  useEffect(() => {
    setMounted(true);
  }, []);

  // Detect device type for mobile navigation
  const device = detectTouchDevice();

  // Mobile navigation items
  const mobileNavItems = [
    { id: 'home', label: t("nav.home"), href: '/', icon: Home },
    { id: 'about', label: t("nav.about"), href: '/about', icon: Calendar },
    { id: 'venues', label: t("nav.venues"), href: '/venues', icon: MapPin },
    { id: 'favorites', label: 'Favorites', href: '/favorites', icon: Heart },
    { id: 'profile', label: 'Profile', href: '/profile', icon: User },
  ];

  return (
    <header className="sticky top-0 z-50 bg-gradient-to-r from-white via-red-50 to-white dark:from-gray-900 dark:via-gray-800 dark:to-gray-900 border-b border-gray-200 dark:border-gray-700 backdrop-blur-sm transition-colors duration-300">
      <div className="container mx-auto flex justify-between items-center h-24 px-4">
        {/* Left: Mobile Menu + Logo */}
        <div className="flex items-center gap-3 min-w-0 flex-shrink-0">
          {/* Mobile Navigation - Show on mobile/tablet */}
          {(device.isMobile || device.isTablet) && (
            <MobileNavigation 
              items={mobileNavItems}
              className="md:hidden"
            />
          )}
          
          <Link to="/" className="flex items-center gap-2">
            <Logo className="h-8 w-auto" />
          </Link>
        </div>

        {/* Center: Navigation */}
        <nav className="hidden md:flex space-x-8 flex-1 justify-center">
          <Link
            to="/"
            className={`text-lg font-bold transition-all duration-300 ease-in-out hover:text-brand-black hover:scale-110 hover:bg-brand-accent-cream px-4 py-2 rounded-lg transform hover:-translate-y-1 hover:shadow-lg ${
              location.pathname === "/"
                ? "text-brand-black bg-brand-accent-cream scale-105 shadow-md  border-2 border-brand-primary"
                : "text-brand-black dark:text-brand-white hover:bg-brand-accent-cream"
            }`}
          >
            {t("nav.home")}
          </Link>
          <Link
            to="/about"
            className={`text-lg font-bold transition-all duration-300 ease-in-out hover:text-brand-black hover:scale-110 hover:bg-brand-accent-cream px-4 py-2 rounded-lg transform hover:-translate-y-1 hover:shadow-lg ${
              location.pathname === "/about"
                ? "text-brand-black bg-brand-accent-cream scale-105 shadow-md border-2 border-brand-primary"
                : "text-brand-black dark:text-brand-white hover:bg-brand-accent-cream"
            }`}
          >
            {t("nav.about")}
          </Link>
          <Link
            to="/venues"
            className={`text-lg font-bold transition-all duration-300 ease-in-out hover:text-brand-black hover:scale-110 hover:bg-brand-accent-cream px-4 py-2 rounded-lg transform hover:-translate-y-1 hover:shadow-lg ${
              location.pathname === "/venues"
                ? "text-brand-black bg-brand-accent-cream scale-105 shadow-md border-2 border-brand-primary"
                : "text-brand-black dark:text-brand-white hover:bg-brand-accent-cream"
            }`}
          >
            {t("nav.venues")}
          </Link>
          {/* <Link
            to="/popular"
            className={`text-lg font-bold transition-all duration-300 ease-in-out hover:text-brand-black hover:scale-110 hover:bg-brand-accent-cream px-4 py-2 rounded-lg transform hover:-translate-y-1 hover:shadow-lg ${
              location.pathname === "/popular"
                ? "text-brand-black bg-brand-accent-cream scale-105 shadow-md border-2 border-brand-primary"
                : "text-brand-black dark:text-brand-white hover:bg-brand-accent-cream"
            }`}
          >
            {t("nav.popular")}
          </Link> */}
          {/* <Link
            to="/community"
            className={`text-lg font-bold transition-all duration-300 ease-in-out hover:text-brand-black hover:scale-110 hover:bg-brand-accent-cream px-4 py-2 rounded-lg transform hover:-translate-y-1 hover:shadow-lg ${
              location.pathname === "/community"
                ? "text-brand-black bg-brand-accent-cream scale-105 shadow-md border-2 border-brand-primary"
                : "text-brand-black dark:text-brand-white hover:bg-brand-accent-cream"
            }`}
          >
            Community
          </Link> */}
        </nav>

        {/* Right: Controls */}
        <div className="flex items-center space-x-3 flex-shrink-0">
          {/* Notifications */}
          {/* <NotificationCenter /> */}

          {/* Saved/Favorites Button */}
          <Link to="/favorites">
            <Button
              variant="ghost"
              size="icon"
              aria-label="Saved items"
              className="group"
            >
              <Bookmark className="h-[1.2rem] w-[1.2rem] group-hover:hidden transition-all" />
              <BookmarkFilled
                className="h-[1.2rem] w-[1.2rem] hidden group-hover:inline transition-all fill-blue_green-500"
                fill="currentColor"
              />
            </Button>
          </Link>

          {/* Theme Toggle */}
          {mounted && (
            <Button
              variant="ghost"
              size="icon"
              aria-label="Toggle theme"
              onClick={() =>
                setTheme(resolvedTheme === "dark" ? "light" : "dark")
              }
              className="group relative transition-all duration-300 hover:scale-110 hover:bg-gray-100 dark:hover:bg-gray-800"
            >
              {resolvedTheme === "dark" ? (
                <Sun className="h-[1.2rem] w-[1.2rem] transition-all group-hover:hidden text-brand-accent-gold" />
              ) : (
                <Moon className="h-[1.2rem] w-[1.2rem] transition-all group-hover:hidden text-brand-primary" />
              )}
              {resolvedTheme === "dark" ? (
                <SunFilled
                  className="h-[1.2rem] w-[1.2rem] hidden group-hover:inline transition-all text-brand-accent-gold animate-pulse"
                  fill="currentColor"
                />
              ) : (
                <MoonFilled
                  className="h-[1.2rem] w-[1.2rem] hidden group-hover:inline transition-all text-brand-primary animate-pulse"
                  fill="currentColor"
                />
              )}
              <span className="sr-only">Toggle theme</span>
            </Button>
          )}

          {/* Language Toggle Buttons */}
          <div className="flex items-center gap-1">
            <button
              onClick={() => setLanguage("hr")}
              className={`px-3 py-1 rounded font-bold transition-all duration-200 focus:outline-none focus:ring-2 focus:ring-red-400 text-sm tracking-wide
                ${
                  language === "hr"
                    ? "bg-red-500 text-white shadow-lg scale-105"
                    : "bg-red-100 text-red-700 hover:bg-red-200 hover:text-red-900 active:bg-red-200 active:text-red-700"
                }
              `}
              aria-label="Switch to Croatian"
            >
              HRV
            </button>
            <button
              onClick={() => setLanguage("en")}
              className={`px-3 py-1 rounded font-bold transition-all duration-200 focus:outline-none focus:ring-2 focus:ring-red-400 text-sm tracking-wide
                ${
                  language === "en"
                    ? "bg-red-500 text-white shadow-lg scale-105"
                    : "bg-red-100 text-red-700 hover:bg-red-200 hover:text-red-900 active:bg-red-200 active:text-red-700"
                }
              `}
              aria-label="Switch to English"
            >
              ENG
            </button>
          </div>

          {/* Auth Component */}
          <Auth />
        </div>
      </div>
    </header>
  );
};

export default Header;
