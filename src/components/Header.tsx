
import React, { useState } from 'react';
import { Link } from 'react-router-dom';
import { Flag, Heart } from 'lucide-react';
import Auth from './Auth';
import { 
  Tooltip,
  TooltipContent,
  TooltipProvider,
  TooltipTrigger,
} from "@/components/ui/tooltip";
import { Button } from "@/components/ui/button";
import { toast } from "@/hooks/use-toast";

const Header = () => {
  const [language, setLanguage] = useState<'en' | 'hr'>('en');
  const [isLoggedIn, setIsLoggedIn] = useState(false); // Simulate login state

  // For demo purposes - this would normally be handled by proper auth
  React.useEffect(() => {
    // Check if user is logged in from localStorage
    const loggedInStatus = localStorage.getItem('isLoggedIn') === 'true';
    setIsLoggedIn(loggedInStatus);
    
    // Listen for login/logout events
    const handleAuthChange = (e: CustomEvent) => {
      setIsLoggedIn(e.detail.isLoggedIn);
    };
    
    window.addEventListener('authStateChanged' as any, handleAuthChange);
    
    return () => {
      window.removeEventListener('authStateChanged' as any, handleAuthChange);
    };
  }, []);

  const handleFavoritesClick = () => {
    if (!isLoggedIn) {
      toast({
        title: "Login Required",
        description: "Please log in to view your favorite events",
        variant: "destructive",
      });
      return;
    }
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
          
          <TooltipProvider>
            <Tooltip>
              <TooltipTrigger asChild>
                <Link to="/favorites">
                  <Button 
                    onClick={handleFavoritesClick} 
                    variant="ghost" 
                    className="text-white hover:text-medium-blue"
                  >
                    <Heart className="h-5 w-5" />
                  </Button>
                </Link>
              </TooltipTrigger>
              <TooltipContent>
                <p>Your Favorites</p>
              </TooltipContent>
            </Tooltip>
          </TooltipProvider>
          
          <Auth />
        </div>
      </div>
    </header>
  );
};

export default Header;
