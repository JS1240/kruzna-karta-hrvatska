const API_BASE_URL =
  import.meta.env.VITE_API_BASE_URL || "http://localhost:8000/api";

export interface Event {
  id: number;
  name?: string;  // Legacy field
  title?: string; // New field from backend
  time: string;
  date: string;
  location: string;
  description?: string;
  price?: string;
  image?: string;
  link?: string;
  created_at: string;
  updated_at: string;
  latitude?: string;
  longitude?: string;
}

export interface EventsResponse {
  events: Event[];
  total: number;
  page: number;
  size: number;
  pages: number;
}

export interface EventCreateData {
  name: string;
  time: string;
  date: string;
  location: string;
  description?: string;
  price?: string;
  image?: string;
  link?: string;
}

export interface EventUpdateData {
  name?: string;
  time?: string;
  date?: string;
  location?: string;
  description?: string;
  price?: string;
  image?: string;
  link?: string;
}

export interface EventFilters {
  skip?: number;
  limit?: number;
  search?: string;
  location?: string;
  date_from?: string;
  date_to?: string;
}

export interface MapFilters {
  search?: string;
  location?: string;
  date_from?: string;
  date_to?: string;
}

class ApiError extends Error {
  constructor(
    public status: number,
    message: string,
  ) {
    super(message);
    this.name = "ApiError";
  }
}

async function apiRequest<T>(
  endpoint: string,
  options: RequestInit = {},
): Promise<T> {
  const url = `${API_BASE_URL}${endpoint}`;

  const config: RequestInit = {
    headers: {
      "Content-Type": "application/json",
      ...options.headers,
    },
    ...options,
  };

  try {
    const response = await fetch(url, config);

    if (!response.ok) {
      const errorData = await response
        .json()
        .catch(() => ({ detail: "An error occurred" }));
      throw new ApiError(
        response.status,
        errorData.detail || `HTTP ${response.status}`,
      );
    }

    return await response.json();
  } catch (error) {
    if (error instanceof ApiError) {
      throw error;
    }
    throw new ApiError(0, "Network error or server unavailable");
  }
}

export const eventsApi = {
  // Get all events with optional filters
  getEvents: (filters: EventFilters = {}): Promise<EventsResponse> => {
    const params = new URLSearchParams();

    Object.entries(filters).forEach(([key, value]) => {
      if (value !== undefined && value !== null) {
        params.append(key, value.toString());
      }
    });

    const queryString = params.toString();
    return apiRequest(`/events${queryString ? `?${queryString}` : ""}`);
  },

  // Get a specific event by ID
  getEvent: (id: number): Promise<Event> => {
    return apiRequest(`/events/${id}`);
  },

  // Create a new event
  createEvent: (data: EventCreateData): Promise<Event> => {
    return apiRequest("/events", {
      method: "POST",
      body: JSON.stringify(data),
    });
  },

  // Update an existing event
  updateEvent: (id: number, data: EventUpdateData): Promise<Event> => {
    return apiRequest(`/events/${id}`, {
      method: "PUT",
      body: JSON.stringify(data),
    });
  },

  // Delete an event
  deleteEvent: (id: number): Promise<{ message: string }> => {
    return apiRequest(`/events/${id}`, {
      method: "DELETE",
    });
  },
};

// Additional API interfaces
export interface Venue {
  id: number;
  name: string;
  city: string;
  county: string;
  address: string;
  category: 'hotel' | 'concert-hall' | 'conference-center' | 'club' | 'restaurant' | 'outdoor';
  capacity: number;
  priceRange: 1 | 2 | 3 | 4 | 5;
  amenities: string[];
  imageUrl: string;
  rating: number;
  description: string;
  latitude?: string;
  longitude?: string;
  contactEmail?: string;
  contactPhone?: string;
  website?: string;
}

export interface VenuesResponse {
  venues: Venue[];
  total: number;
  page: number;
  size: number;
  pages: number;
}

export interface VenueFilters {
  skip?: number;
  limit?: number;
  search?: string;
  county?: string;
  category?: string;
  minCapacity?: number;
  maxCapacity?: number;
  priceRange?: number[];
}

export interface FavoriteEvent {
  id: number;
  userId: string;
  eventId: number;
  event: Event;
  dateAdded: string;
  notifyEnabled: boolean;
  userNotes?: string;
}

export interface NewsArticle {
  id: number;
  title: string;
  date: string;
  description: string;
  imageUrl: string;
  link?: string;
  category?: string;
  eventId?: number;
  event?: Event;
}

export interface CommunityPost {
  id: string;
  type: 'event_review' | 'event_photo' | 'event_recommendation' | 'general_discussion';
  userId: string;
  userName: string;
  userAvatar?: string;
  content: string;
  images?: string[];
  eventId?: number;
  event?: Event;
  likes: number;
  comments: number;
  shares: number;
  isLiked: boolean;
  isBookmarked: boolean;
  createdAt: string;
  tags?: string[];
}

// Enhanced API services
export const favoritesApi = {
  // Get user's favorite events
  getUserFavorites: (userId: string): Promise<FavoriteEvent[]> => {
    return apiRequest(`/users/${userId}/favorites`);
  },

  // Add event to favorites
  addToFavorites: (userId: string, eventId: number, notifyEnabled: boolean = false): Promise<FavoriteEvent> => {
    return apiRequest(`/users/${userId}/favorites`, {
      method: "POST",
      body: JSON.stringify({ eventId, notifyEnabled }),
    });
  },

  // Remove event from favorites
  removeFromFavorites: (userId: string, eventId: number): Promise<{ message: string }> => {
    return apiRequest(`/users/${userId}/favorites/${eventId}`, {
      method: "DELETE",
    });
  },

  // Update favorite settings
  updateFavorite: (userId: string, eventId: number, data: { notifyEnabled?: boolean; userNotes?: string }): Promise<FavoriteEvent> => {
    return apiRequest(`/users/${userId}/favorites/${eventId}`, {
      method: "PATCH",
      body: JSON.stringify(data),
    });
  },
};

export const venuesApi = {
  // Get venues with filters
  getVenues: (filters: VenueFilters = {}): Promise<VenuesResponse> => {
    const params = new URLSearchParams();

    Object.entries(filters).forEach(([key, value]) => {
      if (value !== undefined && value !== null) {
        if (Array.isArray(value)) {
          value.forEach(v => params.append(key, v.toString()));
        } else {
          params.append(key, value.toString());
        }
      }
    });

    const queryString = params.toString();
    return apiRequest(`/venues${queryString ? `?${queryString}` : ""}`);
  },

  // Get specific venue
  getVenue: (id: number): Promise<Venue> => {
    return apiRequest(`/venues/${id}`);
  },

  // Search venues
  searchVenues: (query: string, filters: VenueFilters = {}): Promise<VenuesResponse> => {
    return venuesApi.getVenues({ ...filters, search: query });
  },

  // Contact venue
  contactVenue: (venueId: number, contactData: {
    name: string;
    email: string;
    phone?: string;
    eventDate?: string;
    message: string;
  }): Promise<{ message: string }> => {
    return apiRequest(`/venues/${venueId}/contact`, {
      method: "POST",
      body: JSON.stringify(contactData),
    });
  },
};

export const newsApi = {
  // Get latest news (can be event-based or from CMS)
  getLatestNews: (limit: number = 5): Promise<NewsArticle[]> => {
    return apiRequest(`/news?limit=${limit}`);
  },

  // Get news by category
  getNewsByCategory: (category: string, limit: number = 5): Promise<NewsArticle[]> => {
    return apiRequest(`/news?category=${category}&limit=${limit}`);
  },

  // Get event-related news
  getEventNews: (eventId: number): Promise<NewsArticle[]> => {
    return apiRequest(`/events/${eventId}/news`);
  },

  // Alternative: Generate news from recent events
  generateEventNews: (limit: number = 5): Promise<NewsArticle[]> => {
    return eventsApi.getEvents({ limit, skip: 0 }).then(response => {
      return response.events.map(event => ({
        id: event.id,
        title: `New Event: ${event.title || event.name}`,
        date: event.created_at,
        description: event.description || `Join us for ${event.title || event.name} in ${event.location}`,
        imageUrl: event.image || '/event-images/concert.jpg',
        category: 'event_announcement',
        eventId: event.id,
        event: event,
      }));
    });
  },
};

export const communityApi = {
  // Get community posts
  getCommunityPosts: (filters: {
    type?: string;
    eventId?: number;
    userId?: string;
    limit?: number;
    skip?: number;
  } = {}): Promise<CommunityPost[]> => {
    const params = new URLSearchParams();
    
    Object.entries(filters).forEach(([key, value]) => {
      if (value !== undefined && value !== null) {
        params.append(key, value.toString());
      }
    });

    const queryString = params.toString();
    return apiRequest(`/community/posts${queryString ? `?${queryString}` : ""}`);
  },

  // Create new post
  createPost: (postData: {
    type: string;
    content: string;
    eventId?: number;
    images?: string[];
    tags?: string[];
  }): Promise<CommunityPost> => {
    return apiRequest(`/community/posts`, {
      method: "POST",
      body: JSON.stringify(postData),
    });
  },

  // Get posts for specific event
  getEventPosts: (eventId: number): Promise<CommunityPost[]> => {
    return communityApi.getCommunityPosts({ eventId });
  },

  // Like/unlike post
  togglePostLike: (postId: string): Promise<{ liked: boolean; likes: number }> => {
    return apiRequest(`/community/posts/${postId}/like`, {
      method: "POST",
    });
  },

  // Bookmark/unbookmark post
  togglePostBookmark: (postId: string): Promise<{ bookmarked: boolean }> => {
    return apiRequest(`/community/posts/${postId}/bookmark`, {
      method: "POST",
    });
  },

  // Add comment to post
  addComment: (postId: string, content: string): Promise<any> => {
    return apiRequest(`/community/posts/${postId}/comments`, {
      method: "POST",
      body: JSON.stringify({ content }),
    });
  },

  // Generate mock posts from real events (fallback)
  generateMockPosts: (limit: number = 10): Promise<CommunityPost[]> => {
    return eventsApi.getEvents({ limit, skip: 0 }).then(response => {
      return response.events.slice(0, 3).map((event, index) => ({
        id: `generated-${event.id}-${index}`,
        type: index === 0 ? 'event_review' : index === 1 ? 'event_recommendation' : 'general_discussion',
        userId: 'system',
        userName: 'Event Organizer',
        content: index === 0 
          ? `Amazing experience at ${event.title || event.name}! Highly recommended for everyone.`
          : index === 1
          ? `Don't miss ${event.title || event.name} - tickets are selling fast!`
          : `What are your thoughts about events in ${event.location}?`,
        eventId: event.id,
        event: event,
        likes: Math.floor(Math.random() * 30) + 5,
        comments: Math.floor(Math.random() * 15) + 2,
        shares: Math.floor(Math.random() * 10) + 1,
        isLiked: false,
        isBookmarked: false,
        createdAt: new Date(Date.now() - Math.random() * 86400000 * 7).toISOString(), // Random within last week
        tags: [event.location?.toLowerCase(), 'events', 'croatia'],
      }));
    });
  },
};

export { ApiError };
