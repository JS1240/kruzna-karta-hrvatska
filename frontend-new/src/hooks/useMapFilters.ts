import { useState, useCallback, useMemo } from 'react';
import { FilterState, EventSearchParams } from '@/types/event';

export const useMapFilters = (initialFilters: FilterState = {}) => {
  const [filters, setFilters] = useState<FilterState>(initialFilters);

  const updateFilter = useCallback((key: keyof FilterState, value: unknown) => {
    setFilters(prev => ({
      ...prev,
      [key]: value,
    }));
  }, []);

  const clearFilter = useCallback((key: keyof FilterState) => {
    setFilters(prev => {
      const newFilters = { ...prev };
      delete newFilters[key];
      return newFilters;
    });
  }, []);

  const clearAllFilters = useCallback(() => {
    setFilters({});
  }, []);

  const setMultipleFilters = useCallback((newFilters: Partial<FilterState>) => {
    setFilters(prev => ({
      ...prev,
      ...newFilters,
    }));
  }, []);

  // Convert filters to API search params
  const searchParams = useMemo((): EventSearchParams => {
    const params: EventSearchParams = {};

    if (filters.category) {
      params.category_id = filters.category;
    }

    if (filters.dateFrom) {
      params.date_from = filters.dateFrom;
    }

    if (filters.dateTo) {
      params.date_to = filters.dateTo;
    }

    if (filters.location) {
      params.city = filters.location;
    }

    if (filters.featured !== undefined) {
      params.is_featured = filters.featured;
    }

    if (filters.search) {
      params.q = filters.search;
    }

    return params;
  }, [filters]);

  // Check if any filters are active
  const hasActiveFilters = useMemo(() => {
    return Object.keys(filters).length > 0;
  }, [filters]);

  // Get count of active filters
  const activeFilterCount = useMemo(() => {
    return Object.keys(filters).length;
  }, [filters]);

  return {
    filters,
    updateFilter,
    clearFilter,
    clearAllFilters,
    setMultipleFilters,
    searchParams,
    hasActiveFilters,
    activeFilterCount,
  };
};