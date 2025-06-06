const API_BASE_URL =
  import.meta.env.VITE_API_BASE_URL || "http://localhost:8000/api";

export interface Event {
  id: number;
  name: string;
  time: string;
  date: string;
  location: string;
  description?: string;
  price?: string;
  image?: string;
  link?: string;
  created_at: string;
  updated_at: string;
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

export { ApiError };
