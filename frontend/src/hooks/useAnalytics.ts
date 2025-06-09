import { useState } from "react";
import { logger } from "../lib/logger";

export interface RevenueTrend {
  period: string;
  total_revenue: number;
  commission: number;
  organizer_revenue: number;
  booking_count: number;
}

export interface EventPerformance {
  event_id: number;
  title: string;
  date: string;
  location: string;
  total_bookings: number;
  total_revenue: number;
  commission: number;
  organizer_revenue: number;
  tickets_sold: number;
  view_count: number;
  conversion_rate: number;
}

export interface TicketTypeAnalytics {
  name: string;
  price: number;
  total_bookings: number;
  tickets_sold: number;
  total_revenue: number;
  organizer_revenue: number;
  total_quantity: number;
  available_quantity: number;
  sold_percentage: number;
}

export interface ConversionMetrics {
  overall_conversion_rate: number;
  total_views: number;
  total_bookings: number;
  conversion_by_status: Array<{
    status: string;
    views: number;
    bookings: number;
    conversion_rate: number;
  }>;
}

export interface GeographicRevenue {
  location: string;
  event_count: number;
  total_bookings: number;
  total_revenue: number;
  organizer_revenue: number;
  avg_revenue_per_event: number;
}

export const useAnalytics = (revenuePeriod: string) => {
  const [revenueTrends, setRevenueTrends] = useState<RevenueTrend[]>([]);
  const [eventPerformance, setEventPerformance] = useState<EventPerformance[]>([]);
  const [ticketAnalytics, setTicketAnalytics] = useState<TicketTypeAnalytics[]>([]);
  const [conversionMetrics, setConversionMetrics] = useState<ConversionMetrics | null>(null);
  const [geographicRevenue, setGeographicRevenue] = useState<GeographicRevenue[]>([]);
  const [analyticsLoading, setAnalyticsLoading] = useState(false);

  const fetchAnalyticsData = async () => {
    setAnalyticsLoading(true);
    try {
      const token = localStorage.getItem('token');
      if (!token) return;
      const apiBase = import.meta.env.VITE_API_BASE_URL || "http://localhost:8000/api";

      const [trendsResponse, performanceResponse, ticketsResponse, conversionResponse, geoResponse] = await Promise.all([
        fetch(`${apiBase}/user-events/analytics/revenue-trends?period=${revenuePeriod}`, { headers: { Authorization: `Bearer ${token}` } }),
        fetch(`${apiBase}/user-events/analytics/event-performance`, { headers: { Authorization: `Bearer ${token}` } }),
        fetch(`${apiBase}/user-events/analytics/ticket-types`, { headers: { Authorization: `Bearer ${token}` } }),
        fetch(`${apiBase}/user-events/analytics/booking-conversion`, { headers: { Authorization: `Bearer ${token}` } }),
        fetch(`${apiBase}/user-events/analytics/geographic-revenue`, { headers: { Authorization: `Bearer ${token}` } }),
      ]);

      if (trendsResponse.ok) {
        const data = await trendsResponse.json();
        setRevenueTrends(data.trends || []);
      }
      if (performanceResponse.ok) {
        const data = await performanceResponse.json();
        setEventPerformance(data.events || []);
      }
      if (ticketsResponse.ok) {
        const data = await ticketsResponse.json();
        setTicketAnalytics(data.ticket_types || []);
      }
      if (conversionResponse.ok) {
        const data = await conversionResponse.json();
        setConversionMetrics(data);
      }
      if (geoResponse.ok) {
        const data = await geoResponse.json();
        setGeographicRevenue(data.locations || []);
      }
    } catch (err) {
      logger.error('Error fetching analytics data:', err);
    } finally {
      setAnalyticsLoading(false);
    }
  };

  return {
    revenueTrends,
    eventPerformance,
    ticketAnalytics,
    conversionMetrics,
    geographicRevenue,
    analyticsLoading,
    fetchAnalyticsData,
  };
};
