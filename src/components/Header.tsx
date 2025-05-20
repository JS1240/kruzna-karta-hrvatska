import React, { useState, useEffect } from "react";
import { Link, useLocation } from "react-router-dom";
import { Moon, Sun, Bookmark, Bookmark as BookmarkFilled, Sun as SunFilled, Moon as MoonFilled } from "lucide-react";
import { useTheme } from "next-themes";
import { Button } from "@/components/ui/button";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";
import Logo from "./Logo";
import Auth from "./Auth";

const Header = () => {
  const [mounted, setMounted] = useState(false);
  const { theme, setTheme } = useTheme();
  const location = useLocation();
  const [currentLanguage, setCurrentLanguage] = useState<"en" | "hr">("en");

  useEffect(() => {
    setMounted(true);
  }, []);

  const toggleLanguage = () => {
    setCurrentLanguage(currentLanguage === "en" ? "hr" : "en");
  };

  return (
    <header className="sticky top-0 z-50 bg-white dark:bg-gray-900 border-b border-gray-200 dark:border-gray-800">
      <div className="container mx-auto flex justify-between items-center h-16 px-4">
        {/* Left: Logo and Title */}
        <div className="flex items-center min-w-0 flex-shrink-0">
          <Link to="/" className="flex items-center gap-2">
            <Logo className="h-8 w-auto" />
          </Link>
        </div>

        {/* Center: Navigation */}
        <nav className="hidden md:flex space-x-6 flex-1 justify-center">
          <Link
            to="/"
            className={`text-sm font-bold transition-colors duration-200 hover:text-primary hover:scale-110 hover:bg-sky_blue-100 px-2 py-1 rounded-md ${
              location.pathname === "/" ? "text-primary" : "text-gray-700 dark:text-gray-300"
            }`}
          >
            Home
          </Link>
          <Link
            to="/about"
            className={`text-sm font-bold transition-colors duration-200 hover:text-primary hover:scale-110 hover:bg-sky_blue-100 px-2 py-1 rounded-md ${
              location.pathname === "/about" ? "text-primary" : "text-gray-700 dark:text-gray-300"
            }`}
          >
            About
          </Link>
          <Link
            to="/venues"
            className={`text-sm font-bold transition-colors duration-200 hover:text-primary hover:scale-110 hover:bg-sky_blue-100 px-2 py-1 rounded-md ${
              location.pathname === "/venues" ? "text-primary" : "text-gray-700 dark:text-gray-300"
            }`}
          >
            Venues
          </Link>
          <Link
            to="/popular"
            className={`text-sm font-bold transition-colors duration-200 hover:text-primary hover:scale-110 hover:bg-sky_blue-100 px-2 py-1 rounded-md ${
              location.pathname === "/popular" ? "text-primary" : "text-gray-700 dark:text-gray-300"
            }`}
          >
            Popular
          </Link>
        </nav>

        {/* Right: Controls */}
        <div className="flex items-center space-x-3 flex-shrink-0">
          {/* Saved/Favorites Button */}
          <Link to="/favorites">
            <Button
              variant="ghost"
              size="icon"
              aria-label="Saved items"
              className="group"
            >
              <Bookmark className="h-[1.2rem] w-[1.2rem] group-hover:hidden transition-all" />
              <BookmarkFilled className="h-[1.2rem] w-[1.2rem] hidden group-hover:inline transition-all fill-blue_green-500" fill="currentColor" />
            </Button>
          </Link>

          {/* Theme Toggle */}
          {mounted && (
            <Button
              variant="ghost"
              size="icon"
              aria-label="Toggle theme"
              onClick={() => setTheme(theme === "dark" ? "light" : "dark")}
              className="group relative"
            >
              {theme === "dark" ? (
                <Moon className="h-[1.2rem] w-[1.2rem] transition-all group-hover:hidden" />
              ) : (
                <Sun className="h-[1.2rem] w-[1.2rem] transition-all group-hover:hidden" />
              )}
              {theme === "dark" ? (
                <MoonFilled className="h-[1.2rem] w-[1.2rem] hidden group-hover:inline transition-all text-blue-400" fill="currentColor" />
              ) : (
                <SunFilled className="h-[1.2rem] w-[1.2rem] hidden group-hover:inline transition-all text-yellow-400" fill="currentColor" />
              )}
              <span className="sr-only">Toggle theme</span>
            </Button>
          )}

          {/* Language Toggle Buttons */}
          <div className="flex items-center gap-1">
            <button
              onClick={() => setCurrentLanguage("en")}
              className={`px-3 py-1 rounded font-bold transition-all duration-200 focus:outline-none focus:ring-2 focus:ring-blue_green-400 text-sm tracking-wide
                ${currentLanguage === "en"
                  ? "bg-sky_blue-400 text-white shadow-lg scale-105"
                  : "bg-sky_blue-100 text-blue_green-700 hover:bg-blue_green-100 hover:text-blue_green-900 active:bg-sky_blue-200"}
              `}
              aria-label="Switch to English"
            >
              ENG
            </button>
            <button
              onClick={() => setCurrentLanguage("hr")}
              className={`px-3 py-1 rounded font-bold transition-all duration-200 focus:outline-none focus:ring-2 focus:ring-blue_green-400 text-sm tracking-wide
                ${currentLanguage === "hr"
                  ? "bg-sky_blue-400 text-white shadow-lg scale-105"
                  : "bg-sky_blue-100 text-blue_green-700 hover:bg-blue_green-100 hover:text-blue_green-900 active:bg-sky_blue-200"}
              `}
              aria-label="Switch to Croatian"
            >
              HRV
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
