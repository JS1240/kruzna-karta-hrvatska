
import React, { useState, useEffect } from "react";
import { Link, useLocation } from "react-router-dom";
import { Moon, Sun, Globe, Bookmark } from "lucide-react";
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
        <div className="flex items-center space-x-8">
          {/* Logo */}
          <Link to="/" className="flex items-center">
            <Logo className="h-8 w-auto" />
          </Link>

          {/* Navigation */}
          <nav className="hidden md:flex space-x-6">
            <Link
              to="/"
              className={`text-sm font-medium transition-colors hover:text-primary ${
                location.pathname === "/" ? "text-primary" : "text-gray-700 dark:text-gray-300"
              }`}
            >
              Home
            </Link>
            <Link
              to="/about"
              className={`text-sm font-medium transition-colors hover:text-primary ${
                location.pathname === "/about" ? "text-primary" : "text-gray-700 dark:text-gray-300"
              }`}
            >
              About
            </Link>
            <Link
              to="/venues"
              className={`text-sm font-medium transition-colors hover:text-primary ${
                location.pathname === "/venues" ? "text-primary" : "text-gray-700 dark:text-gray-300"
              }`}
            >
              Venues
            </Link>
            <Link
              to="/popular"
              className={`text-sm font-medium transition-colors hover:text-primary ${
                location.pathname === "/popular" ? "text-primary" : "text-gray-700 dark:text-gray-300"
              }`}
            >
              Popular
            </Link>
          </nav>
        </div>

        {/* Right side controls */}
        <div className="flex items-center space-x-3">
          {/* Saved/Favorites Button */}
          <Link to="/favorites">
            <Button variant="ghost" size="icon" aria-label="Saved items">
              <Bookmark className="h-[1.2rem] w-[1.2rem]" />
            </Button>
          </Link>

          {/* Theme Toggle */}
          {mounted && (
            <DropdownMenu>
              <DropdownMenuTrigger asChild>
                <Button variant="ghost" size="icon">
                  <Sun className="h-[1.2rem] w-[1.2rem] rotate-0 scale-100 transition-all dark:-rotate-90 dark:scale-0" />
                  <Moon className="absolute h-[1.2rem] w-[1.2rem] rotate-90 scale-0 transition-all dark:rotate-0 dark:scale-100" />
                  <span className="sr-only">Toggle theme</span>
                </Button>
              </DropdownMenuTrigger>
              <DropdownMenuContent align="end">
                <DropdownMenuItem onClick={() => setTheme("light")}>
                  <Sun className="mr-2 h-4 w-4" />
                  <span>Light</span>
                </DropdownMenuItem>
                <DropdownMenuItem onClick={() => setTheme("dark")}>
                  <Moon className="mr-2 h-4 w-4" />
                  <span>Dark</span>
                </DropdownMenuItem>
                <DropdownMenuItem onClick={() => setTheme("system")}>
                  <span>System</span>
                </DropdownMenuItem>
              </DropdownMenuContent>
            </DropdownMenu>
          )}

          {/* Language Toggle */}
          <DropdownMenu>
            <DropdownMenuTrigger asChild>
              <Button variant="ghost" size="icon" className="relative">
                <Globe className="h-[1.2rem] w-[1.2rem]" />
                <span className="sr-only">Change language</span>
              </Button>
            </DropdownMenuTrigger>
            <DropdownMenuContent align="end">
              <DropdownMenuItem onClick={() => setCurrentLanguage("en")} className="flex items-center gap-2">
                <img
                  src="/usa-flag.svg"
                  alt="English"
                  className="w-4 h-3 object-cover"
                />
                <span>English</span>
                {currentLanguage === "en" && <span className="ml-auto">✓</span>}
              </DropdownMenuItem>
              <DropdownMenuItem onClick={() => setCurrentLanguage("hr")} className="flex items-center gap-2">
                <img
                  src="/croatia-flag.svg"
                  alt="Croatian"
                  className="w-4 h-3 object-cover"
                />
                <span>Croatian</span>
                {currentLanguage === "hr" && <span className="ml-auto">✓</span>}
              </DropdownMenuItem>
            </DropdownMenuContent>
          </DropdownMenu>

          {/* Auth Component */}
          <Auth />
        </div>
      </div>
    </header>
  );
};

export default Header;
