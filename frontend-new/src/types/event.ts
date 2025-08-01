export interface EventCategory {
  id: number;
  name: string;
  description?: string;
  created_at: string;
  updated_at: string;
}

export interface Venue {
  id: number;
  name: string;
  address: string;
  city: string;
  country: string;
  latitude?: number;
  longitude?: number;
  capacity?: number;
  description?: string;
  website?: string;
  phone?: string;
  email?: string;
  created_at: string;
  updated_at: string;
}

export interface TicketType {
  id: string;
  name: string;
  price: number;
  currency: string;
  description?: string;
  available_quantity?: number;
  max_per_person?: number;
}

export interface Event {
  id: number;
  title: string;
  time: string;
  date: string;
  price?: string;
  description?: string;
  link?: string;
  image?: string;
  location: string;
  category_id?: number;
  venue_id?: number;
  latitude?: number;
  longitude?: number;
  source: string;
  external_id?: string;
  event_status: 'active' | 'cancelled' | 'postponed' | 'sold_out' | 'draft';
  is_featured: boolean;
  is_recurring: boolean;
  organizer?: string;
  age_restriction?: string;
  ticket_types?: TicketType[];
  tags?: string[];
  organizer_id?: number;
  approval_status: 'pending' | 'approved' | 'rejected';
  platform_commission_rate: number;
  is_user_generated: boolean;
  slug?: string;
  end_date?: string;
  end_time?: string;
  timezone: string;
  view_count: number;
  last_scraped_at?: string;
  scrape_hash?: string;
  created_at: string;
  updated_at: string;
  
  // Relationships
  category?: EventCategory;
  venue?: Venue;
}

export interface EventResponse {
  events: Event[];
  total: number;
  page: number;
  size: number;
  pages: number;
}

export interface EventSearchParams {
  q?: string;
  category_id?: number;
  venue_id?: number;
  city?: string;
  date_from?: string;
  date_to?: string;
  is_featured?: boolean;
  event_status?: string;
  tags?: string[];
  latitude?: number;
  longitude?: number;
  radius_km?: number;
  page?: number;
  size?: number;
  language?: string;
  use_cache?: boolean;
}

export interface MapBounds {
  north: number;
  south: number;
  east: number;
  west: number;
}

export interface EventMarker {
  id: number;
  title: string;
  latitude: number;
  longitude: number;
  category?: EventCategory | undefined;
  event_status: string;
  is_featured: boolean;
  date: string;
  time: string;
  location: string;
  price?: string;
  image?: string;
}

export interface FilterState {
  category?: number;
  dateFrom?: string;
  dateTo?: string;
  priceMin?: number;
  priceMax?: number;
  location?: string;
  featured?: boolean;
  search?: string;
}

export interface MapState {
  center: [number, number];
  zoom: number;
  bounds?: MapBounds;
}

export interface ApiError {
  message: string;
  detail?: string;
  status?: number;
}

export interface PaginationInfo {
  current_page: number;
  total_pages: number;
  total_items: number;
  items_per_page: number;
  has_next: boolean;
  has_previous: boolean;
}

// Clustering-related interfaces
export interface GeoPoint {
  latitude: number;
  longitude: number;
}

export interface PixelPoint {
  x: number;
  y: number;
}

export interface EventCluster {
  id: string;
  events: Event[];
  center: GeoPoint;
  pixelCenter: PixelPoint;
  count: number;
  bounds?: {
    north: number;
    south: number;
    east: number;
    west: number;
  };
  category?: string; // Dominant category
  isCluster: boolean;
}

export interface ClusteringOptions {
  zoom: number;
  mapBounds: MapBounds;
  mapSize: {
    width: number;
    height: number;
  };
  minClusterSize?: number;
  maxClusterDistance?: number;
}

export interface ClusterConfig {
  shouldCluster: boolean;
  threshold: number;
  minClusterSize: number;
  showIndividualEvents: boolean;
  showEventCounts: boolean;
  maxDisplayRadius: number;
}

export interface ClusteringState {
  clusters: EventCluster[];
  config: ClusterConfig;
  isProcessing: boolean;
  totalEvents: number;
  clusterCount: number;
  singleEventCount: number;
}

export interface MapInteractionState {
  selectedCluster?: EventCluster | null;
  hoveredCluster?: EventCluster | null;
  showClusterPopup: boolean;
  popupPosition?: { x: number; y: number };
}