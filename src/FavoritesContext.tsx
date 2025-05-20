
import React, { createContext, useState, useContext, useEffect, ReactNode } from 'react';
import { toast } from "@/hooks/use-toast";

// Define the type for an event
interface Event {
  id: number;
  title: string;
  date: string;
  location: string;
  imageUrl: string;
}

// Define the context shape
interface FavoritesContextType {
  favorites: Record<number, Event>;
  addFavorite: (event: Event) => void;
  removeFavorite: (eventId: number) => void;
  isFavorite: (eventId: number) => boolean;
}

const FavoritesContext = createContext<FavoritesContextType | undefined>(undefined);

interface FavoritesProviderProps {
  children: ReactNode;
}

export const FavoritesProvider: React.FC<FavoritesProviderProps> = ({ children }) => {
  const [favorites, setFavorites] = useState<Record<number, Event>>({});

  // Load favorites from localStorage when component mounts
  useEffect(() => {
    const storedFavorites = localStorage.getItem('favorites');
    if (storedFavorites) {
      try {
        setFavorites(JSON.parse(storedFavorites));
      } catch (error) {
        console.error('Error parsing favorites from localStorage:', error);
      }
    }
  }, []);

  // Save favorites to localStorage whenever it changes
  useEffect(() => {
    localStorage.setItem('favorites', JSON.stringify(favorites));
  }, [favorites]);

  // Add an event to favorites
  const addFavorite = (event: Event) => {
    setFavorites(prev => ({
      ...prev,
      [event.id]: event
    }));
    
    toast({
      title: "Added to Favorites",
      description: `${event.title} has been added to your favorites.`,
    });
  };

  // Remove an event from favorites
  const removeFavorite = (eventId: number) => {
    setFavorites(prev => {
      const newFavorites = { ...prev };
      delete newFavorites[eventId];
      return newFavorites;
    });
    
    toast({
      title: "Removed from Favorites",
      description: "Event has been removed from your favorites.",
    });
  };

  // Check if an event is in favorites
  const isFavorite = (eventId: number) => {
    return !!favorites[eventId];
  };

  return (
    <FavoritesContext.Provider value={{ favorites, addFavorite, removeFavorite, isFavorite }}>
      {children}
    </FavoritesContext.Provider>
  );
};

// Custom hook to use the favorites context
export const useFavorites = () => {
  const context = useContext(FavoritesContext);
  if (context === undefined) {
    throw new Error('useFavorites must be used within a FavoritesProvider');
  }
  return context;
};
