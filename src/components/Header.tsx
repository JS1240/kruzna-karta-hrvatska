
import React, { useState } from 'react';
import { Link } from 'react-router-dom';
import { Flag, LogIn, UserPlus } from 'lucide-react';
import { Button } from '@/components/ui/button';
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from '@/components/ui/dialog';
import LoginForm from '@/components/LoginForm';

const Header = () => {
  const [language, setLanguage] = useState<'en' | 'hr'>('en');
  const [authDialogOpen, setAuthDialogOpen] = useState(false);
  const [authMode, setAuthMode] = useState<'login' | 'signup'>('login');

  const openLoginDialog = () => {
    setAuthMode('login');
    setAuthDialogOpen(true);
  };

  const openSignupDialog = () => {
    setAuthMode('signup');
    setAuthDialogOpen(true);
  };

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

          <div className="flex items-center space-x-2">
            <Button 
              variant="outline" 
              size="sm" 
              className="bg-transparent border-medium-blue hover:bg-medium-blue hover:text-white text-white"
              onClick={openLoginDialog}
            >
              <LogIn className="mr-1 h-4 w-4" />
              Log In
            </Button>
            <Button 
              size="sm" 
              className="bg-medium-blue hover:bg-light-blue text-white" 
              onClick={openSignupDialog}
            >
              <UserPlus className="mr-1 h-4 w-4" />
              Sign Up
            </Button>
          </div>
        </div>
      </div>

      <Dialog open={authDialogOpen} onOpenChange={setAuthDialogOpen}>
        <DialogContent className="sm:max-w-md">
          <DialogHeader>
            <DialogTitle className="text-xl font-sreda">
              {authMode === 'login' ? 'Log In to Your Account' : 'Create Your Account'}
            </DialogTitle>
            <DialogDescription className="font-josefin text-gray-500">
              {authMode === 'login' 
                ? 'Welcome back! Please enter your details.' 
                : 'Join EventMap Croatia to discover amazing events.'}
            </DialogDescription>
          </DialogHeader>
          <LoginForm mode={authMode} onToggleMode={() => setAuthMode(authMode === 'login' ? 'signup' : 'login')} />
        </DialogContent>
      </Dialog>
    </header>
  );
};

export default Header;
