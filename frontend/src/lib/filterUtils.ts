// Filter utility functions to avoid hoisting issues

/**
 * Infer event category from name and description
 * Moved outside of component to prevent hoisting issues
 */
export const inferEventCategory = (name: string, description: string): string => {
  const text = `${name} ${description}`.toLowerCase();

  if (
    text.includes("concert") ||
    text.includes("glazba") ||
    text.includes("muzik")
  ) {
    return "concert";
  }
  
  if (
    text.includes("sport") ||
    text.includes("fitness") ||
    text.includes("workout") ||
    text.includes("trening")
  ) {
    return "workout";
  }
  
  if (
    text.includes("meetup") ||
    text.includes("networking") ||
    text.includes("meet")
  ) {
    return "meetup";
  }
  
  if (
    text.includes("conference") ||
    text.includes("konferencija") ||
    text.includes("business")
  ) {
    return "conference";
  }
  
  if (
    text.includes("party") ||
    text.includes("zabava") ||
    text.includes("festival")
  ) {
    return "party";
  }
  
  if (
    text.includes("theater") ||
    text.includes("kazalište") ||
    text.includes("predstava")
  ) {
    return "theater";
  }
  
  if (text.includes("festival")) {
    return "festival";
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