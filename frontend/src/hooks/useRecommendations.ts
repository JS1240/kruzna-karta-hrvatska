import { useState, useEffect, useCallback } from 'react';
import { getCurrentUser } from '@/lib/auth';
import { eventsApi } from '@/lib/api';

export interface Event {
  id: string;
  title: string;
  description: string;
  category: string;
  date: string;
  time: string;
  venue: string;
  city: string;
  county: string;
  price?: string;
  image: string;
  latitude: number;
  longitude: number;
  rating?: number;
  attendeeCount?: number;
}

export interface RecommendationReason {
  type: 'category' | 'location' | 'similar_events' | 'trending' | 'time_preference' | 'price_range';
  description: string;
  confidence: number;
}

export interface RecommendedEvent extends Event {
  reason: RecommendationReason;
  score: number;
}

interface UserPreferences {
  favoriteCategories: string[];
  preferredLocations: string[];
  priceRange: { min: number; max: number };
  timePreferences: string[]; // 'morning', 'afternoon', 'evening', 'night'
  attendedEvents: string[];
  favoriteEvents: string[];
}

interface UseRecommendationsReturn {
  recommendations: RecommendedEvent[];
  trendingEvents: Event[];
  nearbyEvents: Event[];
  loading: boolean;
  refreshRecommendations: () => void;
  trackEventView: (eventId: string) => void;
  trackEventInteraction: (eventId: string, type: 'favorite' | 'share' | 'click') => void;
}

// Transform API event to recommendation Event format
const transformApiEventToRecommendation = (apiEvent: any): Event => {
  return {
    id: apiEvent.id?.toString() || '',
    title: apiEvent.title || apiEvent.name || 'Untitled Event',
    description: apiEvent.description || 'No description available.',
    category: apiEvent.category || 'other',
    date: apiEvent.date || new Date().toISOString().split('T')[0],
    time: apiEvent.time || '00:00',
    venue: apiEvent.venue || apiEvent.location || 'TBA',
    city: apiEvent.city || apiEvent.location || 'Croatia',
    county: apiEvent.county || apiEvent.region || '',
    price: apiEvent.price || 'TBA',
    image: apiEvent.image || '/event-images/placeholder.jpg',
    latitude: apiEvent.latitude || 0,
    longitude: apiEvent.longitude || 0,
    rating: apiEvent.rating || 0,
    attendeeCount: apiEvent.attendee_count || apiEvent.sold_tickets || 0,
  };
};

export const useRecommendations = (): UseRecommendationsReturn => {
  const [recommendations, setRecommendations] = useState<RecommendedEvent[]>([]);
  const [trendingEvents, setTrendingEvents] = useState<Event[]>([]);
  const [nearbyEvents, setNearbyEvents] = useState<Event[]>([]);
  const [loading, setLoading] = useState(true);
  const [allEvents, setAllEvents] = useState<Event[]>([]);
  const [userPreferences, setUserPreferences] = useState<UserPreferences>({
    favoriteCategories: [],
    preferredLocations: [],
    priceRange: { min: 0, max: 1000 },
    timePreferences: [],
    attendedEvents: [],
    favoriteEvents: [],
  });

  const user = getCurrentUser();

  // Fetch events from API
  useEffect(() => {
    const fetchAllEvents = async () => {
      try {
        setLoading(true);
        
        // Fetch a good sample of events for recommendations
        const response = await eventsApi.getEvents({ 
          skip: 0, 
          limit: 50, // Get more events for better recommendations
        });
        
        // Transform API events to recommendation format
        const transformedEvents = response.events.map(transformApiEventToRecommendation);
        
        setAllEvents(transformedEvents);
        
      } catch (error) {
        console.error('Failed to fetch events for recommendations:', error);
        // Keep empty array for graceful degradation
        setAllEvents([]);
      }
    };

    fetchAllEvents();
  }, []);

  // Load user preferences and behavior data
  useEffect(() => {
    if (!user) return;

    const loadUserData = () => {
      // Load from localStorage or user profile
      const savedPreferences = localStorage.getItem(`user_preferences_${user.id}`);
      const savedInteractions = localStorage.getItem(`user_interactions_${user.id}`);
      const favoriteEvents = JSON.parse(localStorage.getItem('favoriteEvents') || '[]');

      if (savedPreferences) {
        try {
          setUserPreferences(prev => ({ ...prev, ...JSON.parse(savedPreferences) }));
        } catch (error) {
          console.error('Failed to parse user preferences:', error);
        }
      } else if (user.preferences?.favoriteCategories) {
        // Use preferences from user profile
        setUserPreferences(prev => ({
          ...prev,
          favoriteCategories: user.preferences.favoriteCategories,
        }));
      }

      // Extract favorite event data
      if (favoriteEvents.length > 0) {
        setUserPreferences(prev => ({
          ...prev,
          favoriteEvents: favoriteEvents.map((e: any) => e.id.toString()),
          favoriteCategories: [
            ...new Set([
              ...prev.favoriteCategories,
              ...favoriteEvents.map((e: any) => e.category)
            ])
          ],
          preferredLocations: [
            ...new Set([
              ...prev.preferredLocations,
              ...favoriteEvents.map((e: any) => e.city)
            ])
          ],
        }));
      }
    };

    loadUserData();
  }, [user]);

  // Calculate event score based on user preferences
  const calculateEventScore = useCallback((event: Event): { score: number; reason: RecommendationReason } => {
    let score = 50; // Base score
    let primaryReason: RecommendationReason = {
      type: 'trending',
      description: 'Popular event',
      confidence: 0.5,
    };

    // Category preference boost
    if (userPreferences.favoriteCategories.includes(event.category)) {
      score += 30;
      primaryReason = {
        type: 'category',
        description: `Matches your interest in ${event.category} events`,
        confidence: 0.8,
      };
    }

    // Location preference boost
    if (userPreferences.preferredLocations.includes(event.city)) {
      score += 25;
      if (primaryReason.confidence < 0.7) {
        primaryReason = {
          type: 'location',
          description: `Located in ${event.city}, one of your preferred cities`,
          confidence: 0.7,
        };
      }
    }

    // Price range check
    if (event.price) {
      const price = parseFloat(event.price.replace(/[^\d.]/g, '')) || 0;
      if (price >= userPreferences.priceRange.min && price <= userPreferences.priceRange.max) {
        score += 15;
      } else if (price > userPreferences.priceRange.max) {
        score -= 20;
      }
    } else {
      score += 10; // Free events get a small boost
    }

    // Time preference
    const hour = parseInt(event.time.split(':')[0]);
    let timeCategory = '';
    if (hour < 12) timeCategory = 'morning';
    else if (hour < 17) timeCategory = 'afternoon';
    else if (hour < 21) timeCategory = 'evening';
    else timeCategory = 'night';

    if (userPreferences.timePreferences.includes(timeCategory)) {
      score += 10;
    }

    // Rating boost
    if (event.rating) {
      score += (event.rating - 3) * 10; // Boost based on rating above 3
    }

    // Similar events boost (events in same category as favorited events)
    const similarEvents = userPreferences.favoriteEvents.filter(favId => {
      const favEvent = allEvents.find(e => e.id === favId);
      return favEvent && favEvent.category === event.category;
    });

    if (similarEvents.length > 0 && primaryReason.confidence < 0.9) {
      score += 20;
      primaryReason = {
        type: 'similar_events',
        description: `Similar to events you've liked before`,
        confidence: 0.9,
      };
    }

    // Trending boost based on attendee count
    if (event.attendeeCount && event.attendeeCount > 1000) {
      score += 15;
      if (primaryReason.type === 'trending') {
        primaryReason.description = `Trending event with ${event.attendeeCount.toLocaleString()} attendees`;
        primaryReason.confidence = 0.6;
      }
    }

    // Ensure score is within bounds
    score = Math.max(0, Math.min(100, score));

    return { score, reason: primaryReason };
  }, [userPreferences, allEvents]);

  // Generate recommendations
  const generateRecommendations = useCallback(() => {
    if (allEvents.length === 0) {
      setLoading(false);
      return;
    }

    setLoading(true);

    // Calculate scores for all events
    const scoredEvents = allEvents.map(event => {
      const { score, reason } = calculateEventScore(event);
      return {
        ...event,
        score,
        reason,
      };
    });

    // Sort by score and take top recommendations
    const topRecommendations = scoredEvents
      .sort((a, b) => b.score - a.score)
      .slice(0, 6);

    setRecommendations(topRecommendations);

    // Generate trending events (high attendee count or rating)
    const trending = allEvents
      .filter(event => (event.attendeeCount && event.attendeeCount > 100) || (event.rating && event.rating > 4.0))
      .sort((a, b) => (b.attendeeCount || 0) - (a.attendeeCount || 0))
      .slice(0, 4);

    setTrendingEvents(trending);

    // Generate nearby events (based on user's favorite locations)
    const nearby = allEvents
      .filter(event => 
        userPreferences.preferredLocations.length === 0 || 
        userPreferences.preferredLocations.includes(event.city)
      )
      .slice(0, 4);

    setNearbyEvents(nearby);

    setLoading(false);
  }, [calculateEventScore, userPreferences, allEvents]);

  // Initial load and when preferences change
  useEffect(() => {
    const timer = setTimeout(() => {
      generateRecommendations();
    }, 500); // Small delay to simulate API call

    return () => clearTimeout(timer);
  }, [generateRecommendations]);

  // Track user interactions
  const trackEventView = useCallback((eventId: string) => {
    if (!user) return;

    const interactions = JSON.parse(localStorage.getItem(`user_interactions_${user.id}`) || '{}');
    interactions.views = interactions.views || {};
    interactions.views[eventId] = (interactions.views[eventId] || 0) + 1;
    
    localStorage.setItem(`user_interactions_${user.id}`, JSON.stringify(interactions));

    // Update preferences based on viewed event
    const viewedEvent = allEvents.find(e => e.id === eventId);
    if (viewedEvent) {
      setUserPreferences(prev => {
        const updatedPreferences = {
          ...prev,
          favoriteCategories: prev.favoriteCategories.includes(viewedEvent.category) 
            ? prev.favoriteCategories 
            : [...prev.favoriteCategories, viewedEvent.category],
          preferredLocations: prev.preferredLocations.includes(viewedEvent.city)
            ? prev.preferredLocations
            : [...prev.preferredLocations, viewedEvent.city],
        };
        
        localStorage.setItem(`user_preferences_${user.id}`, JSON.stringify(updatedPreferences));
        return updatedPreferences;
      });
    }
  }, [user]);

  const trackEventInteraction = useCallback((eventId: string, type: 'favorite' | 'share' | 'click') => {
    if (!user) return;

    const interactions = JSON.parse(localStorage.getItem(`user_interactions_${user.id}`) || '{}');
    interactions[type] = interactions[type] || {};
    interactions[type][eventId] = (interactions[type][eventId] || 0) + 1;
    
    localStorage.setItem(`user_interactions_${user.id}`, JSON.stringify(interactions));

    // Stronger signal for favorites
    if (type === 'favorite') {
      const favoritedEvent = allEvents.find(e => e.id === eventId);
      if (favoritedEvent) {
        setUserPreferences(prev => {
          const updatedPreferences = {
            ...prev,
            favoriteEvents: [...prev.favoriteEvents, eventId],
            favoriteCategories: prev.favoriteCategories.includes(favoritedEvent.category) 
              ? prev.favoriteCategories 
              : [...prev.favoriteCategories, favoritedEvent.category],
          };
          
          localStorage.setItem(`user_preferences_${user.id}`, JSON.stringify(updatedPreferences));
          return updatedPreferences;
        });
      }
    }
  }, [user, allEvents]);

  const refreshRecommendations = useCallback(() => {
    generateRecommendations();
  }, [generateRecommendations]);

  return {
    recommendations,
    trendingEvents,
    nearbyEvents,
    loading,
    refreshRecommendations,
    trackEventView,
    trackEventInteraction,
  };
};