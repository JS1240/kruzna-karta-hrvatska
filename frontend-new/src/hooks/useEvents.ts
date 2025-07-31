import { useQuery, UseQueryOptions } from '@tanstack/react-query';
import {
  Event,
  EventResponse,
  EventSearchParams,
  EventCategory,
  Venue,
  ApiError,
} from '@/types/event';
import { apiClient, queryKeys } from '@/lib/api';

export const useEvents = (
  params: EventSearchParams = {},
  options?: UseQueryOptions<EventResponse, ApiError>
) => {
  return useQuery({
    queryKey: queryKeys.events.list(params),
    queryFn: () => apiClient.getEvents(params),
    ...options,
  });
};

export const useEvent = (
  id: number,
  options?: UseQueryOptions<Event, ApiError>
) => {
  return useQuery({
    queryKey: queryKeys.events.detail(id),
    queryFn: () => apiClient.getEvent(id),
    enabled: !!id,
    ...options,
  });
};

export const useFeaturedEvents = (
  page = 1,
  size = 10,
  options?: UseQueryOptions<EventResponse, ApiError>
) => {
  return useQuery({
    queryKey: queryKeys.events.featured(),
    queryFn: () => apiClient.getFeaturedEvents(page, size),
    ...options,
  });
};

export const useSearchEvents = (
  params: EventSearchParams,
  options?: UseQueryOptions<EventResponse, ApiError>
) => {
  return useQuery({
    queryKey: queryKeys.events.search(params),
    queryFn: () => apiClient.searchEvents(params),
    enabled: !!(params.q || params.category_id || params.venue_id || params.city),
    ...options,
  });
};

export const useNearbyEvents = (
  latitude: number,
  longitude: number,
  radius = 10,
  page = 1,
  size = 20,
  options?: UseQueryOptions<EventResponse, ApiError>
) => {
  return useQuery({
    queryKey: queryKeys.events.nearby(latitude, longitude, radius),
    queryFn: () => apiClient.getNearbyEvents(latitude, longitude, radius, page, size),
    enabled: !!(latitude && longitude),
    ...options,
  });
};

export const useCategories = (
  options?: UseQueryOptions<EventCategory[], ApiError>
) => {
  return useQuery({
    queryKey: queryKeys.categories.list(),
    queryFn: () => apiClient.getCategories(),
    staleTime: 30 * 60 * 1000, // 30 minutes
    ...options,
  });
};

export const useVenues = (
  options?: UseQueryOptions<Venue[], ApiError>
) => {
  return useQuery({
    queryKey: queryKeys.venues.list(),
    queryFn: () => apiClient.getVenues(),
    staleTime: 30 * 60 * 1000, // 30 minutes
    ...options,
  });
};

export const useEventsByCategory = (
  categoryId: number,
  page = 1,
  size = 20,
  options?: UseQueryOptions<EventResponse, ApiError>
) => {
  return useQuery({
    queryKey: queryKeys.events.list({ category_id: categoryId, page, size }),
    queryFn: () => apiClient.getEventsByCategory(categoryId, page, size),
    enabled: !!categoryId,
    ...options,
  });
};

export const useEventsByVenue = (
  venueId: number,
  page = 1,
  size = 20,
  options?: UseQueryOptions<EventResponse, ApiError>
) => {
  return useQuery({
    queryKey: queryKeys.events.list({ venue_id: venueId, page, size }),
    queryFn: () => apiClient.getEventsByVenue(venueId, page, size),
    enabled: !!venueId,
    ...options,
  });
};

export const useEventsByDateRange = (
  dateFrom: string,
  dateTo: string,
  page = 1,
  size = 20,
  options?: UseQueryOptions<EventResponse, ApiError>
) => {
  return useQuery({
    queryKey: queryKeys.events.list({ date_from: dateFrom, date_to: dateTo, page, size }),
    queryFn: () => apiClient.getEventsByDateRange(dateFrom, dateTo, page, size),
    enabled: !!(dateFrom && dateTo),
    ...options,
  });
};