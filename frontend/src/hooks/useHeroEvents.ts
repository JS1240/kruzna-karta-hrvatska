import { useState, useEffect, useCallback } from 'react';
import { Event, eventsApi } from '@/lib/api';

interface HeroEvent {
  id: string;
  title: string;
  image: string;
  date: string;
  location: string;
}

interface UseHeroEventsReturn {
  events: HeroEvent[];
  loading: boolean;
  error: string | null;
  refetch: () => Promise<void>;
}

const CACHE_KEY = 'hero-events-cache';
const CACHE_DURATION = 5 * 60 * 1000; // 5 minutes

interface CachedData {
  events: HeroEvent[];
  timestamp: number;
  randomSeed: number;
}

// Fisher-Yates shuffle algorithm
const shuffleArray = <T>(array: T[], seed?: number): T[] => {
  const shuffled = [...array];
  
  // Use seed for consistent randomization within a session
  let random = seed ? 
    () => {
      seed = (seed * 9301 + 49297) % 233280;
      return seed / 233280;
    } : Math.random;
  
  for (let i = shuffled.length - 1; i > 0; i--) {
    const j = Math.floor(random() * (i + 1));
    [shuffled[i], shuffled[j]] = [shuffled[j], shuffled[i]];
  }
  
  return shuffled;
};

// Convert API Event to HeroEvent format
const convertToHeroEvent = (event: Event): HeroEvent | null => {
  // Only include events with valid images
  if (!event.image || event.image.trim() === '') {
    return null;
  }
  
  // Format date for display
  let formattedDate: string;
  try {
    const eventDate = new Date(event.date);
    formattedDate = eventDate.toLocaleDateString('en-US', {
      month: 'long',
      day: 'numeric',
      year: 'numeric'
    });
  } catch {
    formattedDate = event.date;
  }
  
  return {
    id: event.id.toString(),
    title: event.title || event.name || 'Untitled Event',
    image: event.image,
    date: formattedDate,
    location: event.location || 'Croatia'
  };
};

// Generate minimal fallback events only when absolutely necessary
const generateFallbackEvents = (count: number): HeroEvent[] => {
  const fallbackEvents: HeroEvent[] = [
    {
      id: 'fallback-1',
      title: 'Discover Events in Croatia',
      image: '/event-images/placeholder.jpg',
      date: 'Explore Now',
      location: 'Croatia',
    },
    {
      id: 'fallback-2',
      title: 'Join Our Community',
      image: '/event-images/placeholder.jpg',
      date: 'Get Started',
      location: 'Croatia',
    }
  ];
  
  return fallbackEvents.slice(0, Math.min(count, 2)); // Max 2 fallback events
};

export const useHeroEvents = (targetCount: number = 5): UseHeroEventsReturn => {
  const [events, setEvents] = useState<HeroEvent[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Check cache for existing data
  const getCachedData = useCallback((): HeroEvent[] | null => {
    try {
      const cached = localStorage.getItem(CACHE_KEY);
      if (!cached) return null;
      
      const data: CachedData = JSON.parse(cached);
      const now = Date.now();
      
      // Check if cache is still valid
      if (now - data.timestamp < CACHE_DURATION) {
        return data.events;
      }
      
      // Clear expired cache
      localStorage.removeItem(CACHE_KEY);
      return null;
    } catch {
      localStorage.removeItem(CACHE_KEY);
      return null;
    }
  }, []);

  // Save data to cache
  const setCachedData = useCallback((eventsData: HeroEvent[]) => {
    try {
      const cacheData: CachedData = {
        events: eventsData,
        timestamp: Date.now(),
        randomSeed: Math.floor(Math.random() * 1000000)
      };
      localStorage.setItem(CACHE_KEY, JSON.stringify(cacheData));
    } catch {
      // Ignore cache errors
    }
  }, []);

  const fetchEvents = useCallback(async () => {
    try {
      setLoading(true);
      setError(null);

      // Check cache first
      const cached = getCachedData();
      if (cached) {
        setEvents(cached);
        setLoading(false);
        return;
      }

      // Fetch more events than needed for better randomization
      const fetchCount = Math.max(targetCount * 3, 20);
      
      // Try multiple API strategies to get the best events
      let apiEvents: Event[] = [];
      
      try {
        // Strategy 1: Get featured events with images first
        const featuredResponse = await eventsApi.getEvents({ 
          skip: 0, 
          limit: fetchCount,
          featured: true  // If API supports featured flag
        });
        
        apiEvents = featuredResponse.events.filter(event => 
          event.image && event.image.trim() !== ''
        );
        
        // Strategy 2: If not enough featured events, get recent/upcoming events
        if (apiEvents.length < targetCount) {
          const recentResponse = await eventsApi.getEvents({ 
            skip: 0, 
            limit: fetchCount,
            sort: 'date_asc'  // Get upcoming events first
          });
          
          const additionalEvents = recentResponse.events.filter(event => 
            event.image && 
            event.image.trim() !== '' &&
            !apiEvents.some(existing => existing.id === event.id)
          );
          
          apiEvents.push(...additionalEvents);
        }
        
        // Strategy 3: If still not enough, get any events with images
        if (apiEvents.length < Math.min(targetCount, 3)) {
          const allResponse = await eventsApi.getEvents({ 
            skip: 0, 
            limit: fetchCount * 2
          });
          
          const moreEvents = allResponse.events.filter(event => 
            event.image && 
            event.image.trim() !== '' &&
            !apiEvents.some(existing => existing.id === event.id)
          );
          
          apiEvents.push(...moreEvents);
        }
        
      } catch (fetchError) {
        console.error('Failed to fetch events for hero carousel:', fetchError);
        apiEvents = [];
      }

      // Convert to hero event format
      const heroEvents = apiEvents
        .map(convertToHeroEvent)
        .filter((event): event is HeroEvent => event !== null);

      let finalEvents: HeroEvent[] = [];

      if (heroEvents.length >= targetCount) {
        // We have enough real events - use them all
        const shuffled = shuffleArray(heroEvents);
        finalEvents = shuffled.slice(0, targetCount);
      } else if (heroEvents.length >= 2) {
        // We have some real events - use them primarily
        const shuffled = shuffleArray(heroEvents);
        finalEvents = shuffled;
        
        // Only add minimal fallbacks if we're significantly short
        if (heroEvents.length < Math.ceil(targetCount * 0.6)) {
          const fallbacksNeeded = Math.min(2, targetCount - heroEvents.length);
          const fallbacks = generateFallbackEvents(fallbacksNeeded);
          finalEvents = [...finalEvents, ...fallbacks].slice(0, targetCount);
        }
      } else {
        // Very few real events - show what we have + minimal fallbacks
        const fallbacks = generateFallbackEvents(Math.min(2, targetCount));
        finalEvents = [...heroEvents, ...fallbacks].slice(0, targetCount);
      }

      setEvents(finalEvents);
      setCachedData(finalEvents);
      
    } catch (err) {
      console.error('Failed to fetch hero events:', err);
      setError('Failed to load events');
      
      // Use minimal fallback events on error
      const fallbackEvents = generateFallbackEvents(Math.min(2, targetCount));
      setEvents(fallbackEvents);
    } finally {
      setLoading(false);
    }
  }, [targetCount, getCachedData, setCachedData]);

  const refetch = useCallback(async () => {
    // Clear cache and refetch
    localStorage.removeItem(CACHE_KEY);
    await fetchEvents();
  }, [fetchEvents]);

  useEffect(() => {
    fetchEvents();
  }, [fetchEvents]);

  return {
    events,
    loading,
    error,
    refetch
  };
};