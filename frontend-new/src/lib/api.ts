import { QueryClient } from '@tanstack/react-query';
import {
  Event,
  EventResponse,
  EventSearchParams,
  EventCategory,
  Venue,
  ApiError,
} from '@/types/event';

const API_BASE_URL = '/api';

export const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      retry: 3,
      retryDelay: attemptIndex => Math.min(1000 * 2 ** attemptIndex, 30000),
      staleTime: 5 * 60 * 1000, // 5 minutes
      refetchOnWindowFocus: false,
    },
  },
});

class ApiClient {
  private baseUrl: string;

  constructor(baseUrl: string) {
    this.baseUrl = baseUrl;
  }

  private async request<T>(
    endpoint: string,
    options: RequestInit = {}
  ): Promise<T> {
    const url = `${this.baseUrl}${endpoint}`;
    
    const config: RequestInit = {
      headers: {
        'Content-Type': 'application/json',
        ...options.headers,
      },
      ...options,
    };

    try {
      const response = await fetch(url, config);

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}));
        const error: ApiError = {
          message: errorData.message || response.statusText,
          detail: errorData.detail,
          status: response.status,
        };
        throw error;
      }

      return await response.json();
    } catch (error) {
      if (error instanceof Error) {
        throw {
          message: error.message,
          status: 0,
        } as ApiError;
      }
      throw error;
    }
  }

  async getEvents(params: EventSearchParams = {}): Promise<EventResponse> {
    const searchParams = new URLSearchParams();
    
    Object.entries(params).forEach(([key, value]) => {
      if (value !== undefined && value !== null) {
        if (Array.isArray(value)) {
          value.forEach(item => searchParams.append(key, item.toString()));
        } else {
          searchParams.append(key, value.toString());
        }
      }
    });

    const endpoint = `/events/?${searchParams.toString()}`;
    return this.request<EventResponse>(endpoint);
  }

  async getEvent(id: number): Promise<Event> {
    return this.request<Event>(`/events/${id}/`);
  }

  async getFeaturedEvents(page = 1, size = 10): Promise<EventResponse> {
    const searchParams = new URLSearchParams({
      page: page.toString(),
      size: size.toString(),
    });
    
    return this.request<EventResponse>(`/events/featured/?${searchParams.toString()}`);
  }

  async searchEvents(params: EventSearchParams): Promise<EventResponse> {
    const searchParams = new URLSearchParams();
    
    Object.entries(params).forEach(([key, value]) => {
      if (value !== undefined && value !== null) {
        if (Array.isArray(value)) {
          value.forEach(item => searchParams.append(key, item.toString()));
        } else {
          searchParams.append(key, value.toString());
        }
      }
    });

    const endpoint = `/events/search/?${searchParams.toString()}`;
    return this.request<EventResponse>(endpoint);
  }

  async getNearbyEvents(
    latitude: number,
    longitude: number,
    radius = 10,
    page = 1,
    size = 20
  ): Promise<EventResponse> {
    const searchParams = new URLSearchParams({
      latitude: latitude.toString(),
      longitude: longitude.toString(),
      radius_km: radius.toString(),
      page: page.toString(),
      size: size.toString(),
    });

    return this.request<EventResponse>(`/events/nearby/?${searchParams.toString()}`);
  }

  async getCategories(): Promise<EventCategory[]> {
    const response = await this.request<{categories: EventCategory[], total: number}>('/categories/');
    return response.categories;
  }

  async getVenues(): Promise<Venue[]> {
    const response = await this.request<{venues: Venue[], total: number}>('/venues/');
    return response.venues;
  }

  async getEventsByCategory(categoryId: number, page = 1, size = 20): Promise<EventResponse> {
    const searchParams = new URLSearchParams({
      category_id: categoryId.toString(),
      page: page.toString(),
      size: size.toString(),
    });

    return this.request<EventResponse>(`/events?${searchParams.toString()}`);
  }

  async getEventsByVenue(venueId: number, page = 1, size = 20): Promise<EventResponse> {
    const searchParams = new URLSearchParams({
      venue_id: venueId.toString(),
      page: page.toString(),
      size: size.toString(),
    });

    return this.request<EventResponse>(`/events?${searchParams.toString()}`);
  }

  async getEventsByDateRange(
    dateFrom: string,
    dateTo: string,
    page = 1,
    size = 20
  ): Promise<EventResponse> {
    const searchParams = new URLSearchParams({
      date_from: dateFrom,
      date_to: dateTo,
      page: page.toString(),
      size: size.toString(),
    });

    return this.request<EventResponse>(`/events?${searchParams.toString()}`);
  }

  async geocodeEvents(limit = 50): Promise<{
    message: string;
    geocoded_count: number;
    total_checked: number;
    geocoding_results: Array<{
      location: string;
      latitude: number;
      longitude: number;
      confidence: number;
      accuracy: string;
    }>;
  }> {
    const searchParams = new URLSearchParams({
      limit: limit.toString(),
    });

    return this.request(`/events/geocode/?${searchParams.toString()}`, {
      method: 'POST',
    });
  }

  async getGeocodingStatus(): Promise<{
    total_events: number;
    events_with_coordinates: number;
    events_need_geocoding: number;
    events_without_location: number;
    geocoding_percentage: number;
  }> {
    return this.request('/events/geocoding-status/');
  }
}

export const apiClient = new ApiClient(API_BASE_URL);

// Query keys for React Query
export const queryKeys = {
  events: {
    all: ['events'] as const,
    lists: () => [...queryKeys.events.all, 'list'] as const,
    list: (params: EventSearchParams) => [...queryKeys.events.lists(), params] as const,
    details: () => [...queryKeys.events.all, 'detail'] as const,
    detail: (id: number) => [...queryKeys.events.details(), id] as const,
    featured: () => [...queryKeys.events.all, 'featured'] as const,
    nearby: (lat: number, lng: number, radius: number) => 
      [...queryKeys.events.all, 'nearby', lat, lng, radius] as const,
    search: (params: EventSearchParams) => 
      [...queryKeys.events.all, 'search', params] as const,
  },
  categories: {
    all: ['categories'] as const,
    list: () => [...queryKeys.categories.all, 'list'] as const,
  },
  venues: {
    all: ['venues'] as const,
    list: () => [...queryKeys.venues.all, 'list'] as const,
  },
} as const;

// Helper function to create error messages
export const createErrorMessage = (error: unknown): string => {
  if (typeof error === 'object' && error !== null && 'message' in error) {
    return (error as ApiError).message;
  }
  return 'An unexpected error occurred';
};

// Helper function to check if error is an API error
export const isApiError = (error: unknown): error is ApiError => {
  return (
    typeof error === 'object' &&
    error !== null &&
    'message' in error &&
    typeof (error as ApiError).message === 'string'
  );
};