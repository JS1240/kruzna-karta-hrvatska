import React, { useState, useEffect } from "react";
import { Link, useLocation } from "react-router-dom";
import {
  Moon,
  Sun,
  Bookmark,
  Bookmark as BookmarkFilled,
  Sun as SunFilled,
  Moon as MoonFilled,
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

const Header = () => {
  const [mounted, setMounted] = useState(false);
  const { theme, setTheme, resolvedTheme } = useTheme();
  const location = useLocation();
  const { language, setLanguage, t } = useLanguage();

  useEffect(() => {
    setMounted(true);
  }, []);

  return (
    <header className="sticky top-0 z-50 bg-gradient-to-r from-white via-red-50 to-white dark:from-gray-900 dark:via-gray-800 dark:to-gray-900 border-b border-gray-200 dark:border-gray-700 backdrop-blur-sm transition-colors duration-300">
      <div className="container mx-auto flex justify-between items-center h-24 px-4">
        {/* Left: Logo and Title */}
        <div className="flex items-center min-w-0 flex-shrink-0">
          <Link to="/" className="flex items-center gap-2">
            <Logo className="h-8 w-auto" />
          </Link>
        </div>

        {/* Center: Navigation */}
        <nav className="hidden md:flex space-x-8 flex-1 justify-center">
          <Link
            to="/"
            className={`text-lg font-bold transition-all duration-300 ease-in-out hover:text-red-500 hover:scale-110 hover:bg-red-50 px-4 py-2 rounded-lg transform hover:-translate-y-1 hover:shadow-lg ${
              location.pathname === "/"
                ? "text-red-500 bg-red-50 scale-105 shadow-md animate-pulse"
                : "text-gray-700 dark:text-gray-300 hover:bg-red-50"
            }`}
          >
            {t("nav.home")}
          </Link>
          <Link
            to="/about"
            className={`text-lg font-bold transition-all duration-300 ease-in-out hover:text-red-500 hover:scale-110 hover:bg-red-50 px-4 py-2 rounded-lg transform hover:-translate-y-1 hover:shadow-lg ${
              location.pathname === "/about"
                ? "text-red-500 bg-red-50 scale-105 shadow-md animate-pulse"
                : "text-gray-700 dark:text-gray-300 hover:bg-red-50"
            }`}
          >
            {t("nav.about")}
          </Link>
          <Link
            to="/venues"
            className={`text-lg font-bold transition-all duration-300 ease-in-out hover:text-red-500 hover:scale-110 hover:bg-red-50 px-4 py-2 rounded-lg transform hover:-translate-y-1 hover:shadow-lg ${
              location.pathname === "/venues"
                ? "text-red-500 bg-red-50 scale-105 shadow-md animate-pulse"
                : "text-gray-700 dark:text-gray-300 hover:bg-red-50"
            }`}
          >
            {t("nav.venues")}
          </Link>
          <Link
            to="/popular"
            className={`text-lg font-bold transition-all duration-300 ease-in-out hover:text-red-500 hover:scale-110 hover:bg-red-50 px-4 py-2 rounded-lg transform hover:-translate-y-1 hover:shadow-lg ${
              location.pathname === "/popular"
                ? "text-red-500 bg-red-50 scale-105 shadow-md animate-pulse"
                : "text-gray-700 dark:text-gray-300 hover:bg-red-50"
            }`}
          >
            {t("nav.popular")}
          </Link>
          <Link
            to="/community"
            className={`text-lg font-bold transition-all duration-300 ease-in-out hover:text-red-500 hover:scale-110 hover:bg-red-50 px-4 py-2 rounded-lg transform hover:-translate-y-1 hover:shadow-lg ${
              location.pathname === "/community"
                ? "text-red-500 bg-red-50 scale-105 shadow-md animate-pulse"
                : "text-gray-700 dark:text-gray-300 hover:bg-red-50"
            }`}
          >
            Community
          </Link>
        </nav>

        {/* Right: Controls */}
        <div className="flex items-center space-x-3 flex-shrink-0">
          {/* Notifications */}
          <NotificationCenter />

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
                <Sun className="h-[1.2rem] w-[1.2rem] transition-all group-hover:hidden text-yellow-400" />
              ) : (
                <Moon className="h-[1.2rem] w-[1.2rem] transition-all group-hover:hidden text-slate-600" />
              )}
              {resolvedTheme === "dark" ? (
                <SunFilled
                  className="h-[1.2rem] w-[1.2rem] hidden group-hover:inline transition-all text-yellow-500 animate-pulse"
                  fill="currentColor"
                />
              ) : (
                <MoonFilled
                  className="h-[1.2rem] w-[1.2rem] hidden group-hover:inline transition-all text-blue-500 animate-pulse"
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
