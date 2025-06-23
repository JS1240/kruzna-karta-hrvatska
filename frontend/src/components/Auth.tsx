import React, { useState, useEffect } from "react";
import { Dialog, DialogContent, DialogTrigger } from "./ui/dialog";
import { DropdownMenu, DropdownMenuContent, DropdownMenuItem, DropdownMenuTrigger, DropdownMenuSeparator } from "./ui/dropdown-menu";
import { Button } from "./ui/button";
import { Avatar, AvatarFallback, AvatarImage } from "./ui/avatar";
import { UserCircle, Calendar, BarChart3, LogOut, Settings, User, Ticket } from "lucide-react";
import { Link } from "react-router-dom";
import LoginForm from "./LoginForm";
import { getCurrentUser, logout, User as UserType } from "../lib/auth";

const Auth = () => {
  const [isOpen, setIsOpen] = useState(false);
  const [mode, setMode] = useState<"login" | "signup" | "reset">("login");
  const [isLoggedIn, setIsLoggedIn] = useState(false);
  const [user, setUser] = useState<UserType | null>(null);

  useEffect(() => {
    // Check if user is logged in and get user data
    const loggedInStatus = localStorage.getItem("isLoggedIn") === "true";
    const currentUser = getCurrentUser();
    setIsLoggedIn(loggedInStatus);
    setUser(currentUser);

    // Listen for auth state changes
    const handleAuthChange = (e: CustomEvent) => {
      setIsLoggedIn(e.detail.isLoggedIn);
      setUser(e.detail.user);
    };

    window.addEventListener('authStateChanged', handleAuthChange as EventListener);
    
    return () => {
      window.removeEventListener('authStateChanged', handleAuthChange as EventListener);
    };
  }, []);

  const handleModeChange = (newMode: "login" | "signup" | "reset") => {
    setMode(newMode);
  };

  const handleToggleMode = () => {
    setMode(mode === "login" ? "signup" : "login");
  };

  const handleClose = () => {
    setIsOpen(false);
  };

  const handleLogout = async () => {
    try {
      await logout();
      setIsLoggedIn(false);
      setUser(null);
    } catch (error) {
      console.error('Logout failed:', error);
    }
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
              className="gap-2 transition-all duration-200 hover:bg-sky_blue-100 hover:scale-105 hover:shadow-md focus:ring-2 focus:ring-blue_green-400 h-auto p-2"
            >
              <Avatar className="h-8 w-8">
                <AvatarImage src={user?.avatar} />
                <AvatarFallback className="bg-navy-blue text-white text-sm">
                  {user?.name?.charAt(0)?.toUpperCase() || user?.email?.charAt(0)?.toUpperCase()}
                </AvatarFallback>
              </Avatar>
              <span className="hidden sm:inline">{user?.name || 'My Account'}</span>
            </Button>
          </DropdownMenuTrigger>
          <DropdownMenuContent align="end" className="w-56">
            {user && (
              <>
                <div className="px-3 py-2 border-b">
                  <p className="text-sm font-medium">{user.name}</p>
                  <p className="text-xs text-gray-500">{user.email}</p>
                </div>
                <DropdownMenuSeparator />
              </>
            )}
            <DropdownMenuItem asChild>
              <Link to="/profile" className="flex items-center gap-2">
                <User className="h-4 w-4" />
                Profile Settings
              </Link>
            </DropdownMenuItem>
            <DropdownMenuItem asChild>
              <Link to="/bookings" className="flex items-center gap-2">
                <Ticket className="h-4 w-4" />
                My Bookings
              </Link>
            </DropdownMenuItem>
            <DropdownMenuItem asChild>
              <Link to="/favorites" className="flex items-center gap-2">
                <Settings className="h-4 w-4" />
                My Favorites
              </Link>
            </DropdownMenuItem>
            <DropdownMenuSeparator />
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
              onModeChange={handleModeChange}
            />
          </DialogContent>
        </Dialog>
      )}
    </>
  );
};

export default Auth;
