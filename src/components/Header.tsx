import React, { useState, useEffect } from "react";
import { Link, useLocation } from "react-router-dom";
import { Moon, Sun } from "lucide-react";
import { useTheme } from "next-themes";
import { Button } from "@/components/ui/button";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";
import Logo from "./Logo";

const Header = () => {
  const [mounted, setMounted] = useState(false);
  const { setTheme } = useTheme();
  const location = useLocation();

  useEffect(() => {
    setMounted(true);
  }, []);

  return (
    <header className="sticky top-0 z-50 bg-white border-b border-gray-200">
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
                location.pathname === "/" ? "text-primary" : "text-gray-700"
              }`}
            >
              Home
            </Link>
            <Link
              to="/about"
              className={`text-sm font-medium transition-colors hover:text-primary ${
                location.pathname === "/about" ? "text-primary" : "text-gray-700"
              }`}
            >
              About
            </Link>
            <Link
              to="/venues"
              className={`text-sm font-medium transition-colors hover:text-primary ${
                location.pathname === "/venues" ? "text-primary" : "text-gray-700"
              }`}
            >
              Venues
            </Link>
            <Link
              to="/popular"
              className={`text-sm font-medium transition-colors hover:text-primary ${
                location.pathname === "/popular" ? "text-primary" : "text-gray-700"
              }`}
            >
              Popular
            </Link>
          </nav>
        </div>

        {/* Right side controls */}
        <div className="flex items-center space-x-4">
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
                  Light
                </DropdownMenuItem>
                <DropdownMenuItem onClick={() => setTheme("dark")}>
                  Dark
                </DropdownMenuItem>
                <DropdownMenuItem onClick={() => setTheme("system")}>
                  System
                </DropdownMenuItem>
              </DropdownMenuContent>
            </DropdownMenu>
          )}

          {/* Language Toggle - Example, replace with actual implementation */}
          <button className="language-toggle">
            <img
              src="https://flagcdn.com/24x18/hr.png"
              alt="Croatian"
              className="w-full h-full object-cover"
            />
          </button>
        </div>
      </div>

      {/* Mobile Menu (Example - implement as needed) */}
      {/* You can add a mobile menu here that appears on smaller screens */}
    </header>
  );
};

export default Header;
