import React, { useState, useEffect } from "react";
import { Dialog, DialogContent, DialogTrigger } from "./ui/dialog";
import { DropdownMenu, DropdownMenuContent, DropdownMenuItem, DropdownMenuTrigger, DropdownMenuSeparator } from "./ui/dropdown-menu";
import { Button } from "./ui/button";
import { UserCircle, Calendar, BarChart3, LogOut, Settings } from "lucide-react";
import { Link } from "react-router-dom";
import LoginForm from "./LoginForm";

const Auth = () => {
  const [isOpen, setIsOpen] = useState(false);
  const [mode, setMode] = useState<"login" | "signup">("login");
  const [isLoggedIn, setIsLoggedIn] = useState(false);

  useEffect(() => {
    // Check if user is logged in from localStorage
    const loggedInStatus = localStorage.getItem("isLoggedIn") === "true";
    setIsLoggedIn(loggedInStatus);
  }, []);

  const handleToggleMode = () => {
    setMode(mode === "login" ? "signup" : "login");
  };

  const handleClose = () => {
    setIsOpen(false);
  };

  const handleLogout = () => {
    localStorage.removeItem("token");
    localStorage.setItem("isLoggedIn", "false");
    setIsLoggedIn(false);

    // Dispatch custom event for auth state change
    const event = new CustomEvent("authStateChanged", {
      detail: { isLoggedIn: false },
    });
    window.dispatchEvent(event);
  };

  const handleLoginSuccess = () => {
    localStorage.setItem("isLoggedIn", "true");
    setIsLoggedIn(true);
    setIsOpen(false);

    // Dispatch custom event for auth state change
    const event = new CustomEvent("authStateChanged", {
      detail: { isLoggedIn: true },
    });
    window.dispatchEvent(event);
  };

  return (
    <>
      {isLoggedIn ? (
        <DropdownMenu>
          <DropdownMenuTrigger asChild>
            <Button
              variant="ghost"
              className="gap-2 transition-all duration-200 hover:bg-sky_blue-100 hover:scale-105 hover:shadow-md focus:ring-2 focus:ring-blue_green-400"
            >
              <UserCircle className="h-5 w-5 transition-all group-hover:text-blue_green-600" />
              <span className="hidden sm:inline">My Account</span>
            </Button>
          </DropdownMenuTrigger>
          <DropdownMenuContent align="end" className="w-48">
            <DropdownMenuItem asChild>
              <Link to="/organizer/dashboard" className="flex items-center gap-2">
                <BarChart3 className="h-4 w-4" />
                Organizer Dashboard
              </Link>
            </DropdownMenuItem>
            <DropdownMenuItem asChild>
              <Link to="/create-event" className="flex items-center gap-2">
                <Calendar className="h-4 w-4" />
                Create Event
              </Link>
            </DropdownMenuItem>
            <DropdownMenuSeparator />
            <DropdownMenuItem asChild>
              <Link to="/favorites" className="flex items-center gap-2">
                <Settings className="h-4 w-4" />
                My Favorites
              </Link>
            </DropdownMenuItem>
            <DropdownMenuSeparator />
            <DropdownMenuItem onClick={handleLogout} className="flex items-center gap-2 text-red-600">
              <LogOut className="h-4 w-4" />
              Logout
            </DropdownMenuItem>
          </DropdownMenuContent>
        </DropdownMenu>
      ) : (
        <Dialog open={isOpen} onOpenChange={setIsOpen}>
          <DialogTrigger asChild>
            <Button
              variant="ghost"
              className="gap-2 transition-all duration-200 hover:bg-sky_blue-100 hover:scale-105 hover:shadow-md focus:ring-2 focus:ring-blue_green-400"
            >
              <UserCircle className="h-5 w-5 transition-all group-hover:text-blue_green-600" />
              <span>{mode === "login" ? "Login" : "Sign up"}</span>
            </Button>
          </DialogTrigger>
          <DialogContent className="sm:max-w-[425px]">
            <LoginForm
              mode={mode}
              onToggleMode={handleToggleMode}
              onClose={handleClose}
              onLoginSuccess={handleLoginSuccess}
            />
          </DialogContent>
        </Dialog>
      )}
    </>
  );
};

export default Auth;
