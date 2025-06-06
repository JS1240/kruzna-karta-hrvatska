import { useState, useEffect } from "react";
import { eventsApi, Event, EventFilters } from "@/lib/api";

export interface UseEventsOptions {
  filters?: EventFilters;
  autoFetch?: boolean;
}

export interface UseEventsReturn {
  events: Event[];
  loading: boolean;
  error: string | null;
  total: number;
  refetch: () => Promise<void>;
  fetchMore: () => Promise<void>;
  hasMore: boolean;
}

export const useEvents = (options: UseEventsOptions = {}): UseEventsReturn => {
  const { filters = {}, autoFetch = true } = options;

  const [events, setEvents] = useState<Event[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [total, setTotal] = useState(0);
  const [page, setPage] = useState(1);
  const [hasMore, setHasMore] = useState(true);

  const fetchEvents = async (reset = false) => {
    if (loading && !reset) return;

    setLoading(true);
    setError(null);

    try {
      const currentPage = reset ? 1 : page;
      const limit = 20;
      const skip = (currentPage - 1) * limit;

      const response = await eventsApi.getEvents({
        ...filters,
        skip,
        limit,
      });

      if (reset) {
        setEvents(response.events);
        setPage(2);
      } else {
        setEvents((prev) => [...prev, ...response.events]);
        setPage((prev) => prev + 1);
      }

      setTotal(response.total);
      setHasMore(
        response.events.length === limit &&
          events.length + response.events.length < response.total,
      );
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to fetch events");
      console.error("Error fetching events:", err);
    } finally {
      setLoading(false);
    }
  };

  const refetch = async () => {
    setPage(1);
    await fetchEvents(true);
  };

  const fetchMore = async () => {
    if (!hasMore || loading) return;
    await fetchEvents(false);
  };

  useEffect(() => {
    if (autoFetch) {
      refetch();
    }
  }, [JSON.stringify(filters)]); // Re-fetch when filters change

  return {
    events,
    loading,
    error,
    total,
    refetch,
    fetchMore,
    hasMore,
  };
};
