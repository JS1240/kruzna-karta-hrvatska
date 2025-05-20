import React, { useState, useEffect } from 'react';
import {
  Dialog,
  DialogContent,
  DialogTrigger,
} from '@/components/ui/dialog';
import { Button } from '@/components/ui/button';
import { UserCircle } from 'lucide-react';
import LoginForm from './LoginForm';

const Auth = () => {
  const [isOpen, setIsOpen] = useState(false);
  const [mode, setMode] = useState<'login' | 'signup'>('login');
  const [isLoggedIn, setIsLoggedIn] = useState(false);

  useEffect(() => {
    // Check if user is logged in from localStorage
    const loggedInStatus = localStorage.getItem('isLoggedIn') === 'true';
    setIsLoggedIn(loggedInStatus);
  }, []);

  const handleToggleMode = () => {
    setMode(mode === 'login' ? 'signup' : 'login');
  };

  const handleClose = () => {
    setIsOpen(false);
  };

  const handleLogout = () => {
    localStorage.setItem('isLoggedIn', 'false');
    setIsLoggedIn(false);
    
    // Dispatch custom event for auth state change
    const event = new CustomEvent('authStateChanged', {
      detail: { isLoggedIn: false }
    });
    window.dispatchEvent(event);
  };

  const handleLoginSuccess = () => {
    localStorage.setItem('isLoggedIn', 'true');
    setIsLoggedIn(true);
    setIsOpen(false);
    
    // Dispatch custom event for auth state change
    const event = new CustomEvent('authStateChanged', {
      detail: { isLoggedIn: true }
    });
    window.dispatchEvent(event);
  };

  return (
    <Dialog open={isOpen} onOpenChange={setIsOpen}>
      <DialogTrigger asChild>
        {isLoggedIn ? (
          <Button 
            variant="ghost" 
            className="gap-2 transition-all duration-200 hover:bg-sky_blue-100 hover:scale-105 hover:shadow-md focus:ring-2 focus:ring-blue_green-400"
            onClick={handleLogout}
          >
            <UserCircle className="h-5 w-5 transition-all group-hover:text-blue_green-600" />
            <span>Logout</span>
          </Button>
        ) : (
          <Button 
            variant="ghost" 
            className="gap-2 transition-all duration-200 hover:bg-sky_blue-100 hover:scale-105 hover:shadow-md focus:ring-2 focus:ring-blue_green-400"
          >
            <UserCircle className="h-5 w-5 transition-all group-hover:text-blue_green-600" />
            <span>{mode === 'login' ? 'Login' : 'Sign up'}</span>
          </Button>
        )}
      </DialogTrigger>
      {!isLoggedIn && (
        <DialogContent className="sm:max-w-[425px]">
          <LoginForm 
            mode={mode} 
            onToggleMode={handleToggleMode} 
            onClose={handleClose}
            onLoginSuccess={handleLoginSuccess}
          />
        </DialogContent>
      )}
    </Dialog>
  );
};

export default Auth;
