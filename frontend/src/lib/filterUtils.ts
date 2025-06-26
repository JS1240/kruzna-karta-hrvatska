// Filter utility functions to avoid hoisting issues

/**
 * Infer event category from name and description
 * Moved outside of component to prevent hoisting issues
 */
export const inferEventCategory = (name: string, description: string): string => {
  const text = `${name} ${description}`.toLowerCase();

  // Festival category (check first as it's more specific)
  if (
    text.includes("festival") ||
    text.includes("festivalu") ||
    text.includes("fest ") ||
    text.includes("ultra") ||
    text.includes("summer festival") ||
    text.includes("music festival")
  ) {
    return "festival";
  }

  // Concert/Music category
  if (
    text.includes("concert") ||
    text.includes("koncert") ||
    text.includes("glazba") ||
    text.includes("muzik") ||
    text.includes("music") ||
    text.includes("opera") ||
    text.includes("symphony") ||
    text.includes("orkestar") ||
    text.includes("amira medunjanin") ||
    text.includes("electronic") ||
    text.includes("jazz") ||
    text.includes("rock") ||
    text.includes("pop")
  ) {
    return "music";
  }
  
  // Theater/Culture category
  if (
    text.includes("theater") ||
    text.includes("theatre") ||
    text.includes("kazalište") ||
    text.includes("predstava") ||
    text.includes("drama") ||
    text.includes("opera") ||
    text.includes("performance") ||
    text.includes("cultural") ||
    text.includes("kultura") ||
    text.includes("art") ||
    text.includes("umjetnost") ||
    text.includes("exhibition") ||
    text.includes("izložba")
  ) {
    return "culture";
  }
  
  // Sports/Workout category
  if (
    text.includes("sport") ||
    text.includes("fitness") ||
    text.includes("workout") ||
    text.includes("trening") ||
    text.includes("football") ||
    text.includes("basketball") ||
    text.includes("tennis") ||
    text.includes("marathon") ||
    text.includes("cycling") ||
    text.includes("bicikl")
  ) {
    return "sports";
  }
  
  // Conference/Business category
  if (
    text.includes("conference") ||
    text.includes("konferencija") ||
    text.includes("business") ||
    text.includes("seminar") ||
    text.includes("workshop") ||
    text.includes("summit") ||
    text.includes("meeting") ||
    text.includes("networking")
  ) {
    return "conference";
  }
  
  // Party/Entertainment category
  if (
    text.includes("party") ||
    text.includes("zabava") ||
    text.includes("club") ||
    text.includes("nightlife") ||
    text.includes("dance") ||
    text.includes("ples") ||
    text.includes("disco") ||
    text.includes("night") ||
    text.includes("evening")
  ) {
    return "party";
  }
  
  // Meetup/Social category
  if (
    text.includes("meetup") ||
    text.includes("meet") ||
    text.includes("social") ||
    text.includes("community") ||
    text.includes("gathering") ||
    text.includes("okupljanje")
  ) {
    return "meetup";
  }

  return "other";
};

/**
 * Extract numeric price value from string
 * Moved outside of component to prevent hoisting issues
 */
export const extractPriceValue = (price: string): number | null => {
  if (!price) return null;
  
  if (
    price.toLowerCase().includes("free") ||
    price.toLowerCase().includes("besplatno")
  ) {
    return 0;
  }

  const match = price.match(/(\d+)/);
  return match ? parseInt(match[1]) : null;
};

/**
 * Count active filters for badge display
 */
export const countActiveFilters = (filters: {
  activeCategory?: string | null;
  selectedCounty?: string | null;
  selectedCity?: string | null;
  selectedDateRange?: string | null;
  selectedDateRangeObj?: { from?: Date } | undefined;
  selectedPrice?: [number, number] | null;
  searchTerm?: string;
}): number => {
  return [
    filters.activeCategory,
    filters.selectedCounty,
    filters.selectedCity,
    filters.selectedDateRange,
    filters.selectedDateRangeObj?.from,
    filters.selectedPrice && 
      (filters.selectedPrice[0] > 0 || filters.selectedPrice[1] < 500),
    filters.searchTerm && filters.searchTerm.length > 0
  ].filter(Boolean).length;
};