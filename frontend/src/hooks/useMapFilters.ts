import { useState, useMemo } from "react";
import type { DateRange } from "react-day-picker";

export const useMapFilters = (countiesWithCities: Record<string, string[]>) => {
  const [activeCategory, setActiveCategory] = useState<string | null>(null);
  const [selectedCounty, setSelectedCounty] = useState<string | null>(null);
  const [selectedCity, setSelectedCity] = useState<string | null>(null);
  const [selectedPrice, setSelectedPrice] = useState<[number, number] | null>(null);
  const [selectedDateRange, setSelectedDateRange] = useState<string | null>(null);
  const [selectedDateRangeObj, setSelectedDateRangeObj] = useState<DateRange | undefined>(undefined);
  const [calendarOpen, setCalendarOpen] = useState(false);
  const [searchTerm, setSearchTerm] = useState("");

  const getDateRangeFromSelection = (selection: string | null): [Date, Date] | null => {
    if (!selection) return null;

    const today = new Date();
    today.setHours(0, 0, 0, 0);

    const tomorrow = new Date(today);
    tomorrow.setDate(tomorrow.getDate() + 1);

    const thisWeekend = new Date(today);
    const dayOfWeek = today.getDay();
    const daysUntilWeekend = dayOfWeek === 0 || dayOfWeek === 6 ? 0 : 6 - dayOfWeek;
    thisWeekend.setDate(today.getDate() + daysUntilWeekend);

    const nextWeekend = new Date(thisWeekend);
    nextWeekend.setDate(nextWeekend.getDate() + 7);

    const endOfMonth = new Date(today.getFullYear(), today.getMonth() + 1, 0);

    switch (selection) {
      case "today":
        return [today, today];
      case "tomorrow":
        return [tomorrow, tomorrow];
      case "this-weekend": {
        const weekendEnd = new Date(thisWeekend);
        weekendEnd.setDate(thisWeekend.getDate() + 1);
        return [thisWeekend, weekendEnd];
      }
      case "next-weekend": {
        const nextWeekendEnd = new Date(nextWeekend);
        nextWeekendEnd.setDate(nextWeekend.getDate() + 1);
        return [nextWeekend, nextWeekendEnd];
      }
      case "this-month":
        return [today, endOfMonth];
      default:
        return null;
    }
  };

  const apiFilters = useMemo(() => {
    const filters: any = {};

    if (searchTerm) {
      filters.search = searchTerm;
    }

    if (selectedCity) {
      filters.location = selectedCity;
    } else if (selectedCounty) {
      filters.location = selectedCounty;
    }

    const dateRange = getDateRangeFromSelection(selectedDateRange);
    if (dateRange) {
      filters.date_from = dateRange[0].toISOString().split("T")[0];
      filters.date_to = dateRange[1].toISOString().split("T")[0];
    } else if (selectedDateRangeObj?.from) {
      filters.date_from = selectedDateRangeObj.from.toISOString().split("T")[0];
      if (selectedDateRangeObj.to) {
        filters.date_to = selectedDateRangeObj.to.toISOString().split("T")[0];
      }
    }

    return filters;
  }, [searchTerm, selectedCity, selectedCounty, selectedDateRange, selectedDateRangeObj]);

  const clearAllFilters = () => {
    setActiveCategory(null);
    setSelectedCounty(null);
    setSelectedCity(null);
    setSelectedPrice(null);
    setSelectedDateRange(null);
    setSelectedDateRangeObj(undefined);
    setSearchTerm("");
  };

  const handleCategoryChange = (category: string | null) => {
    setActiveCategory(category === activeCategory ? null : category);
  };

  const handleDateRangeChange = (value: string) => {
    setSelectedDateRange(value === selectedDateRange ? null : value);
    setSelectedDateRangeObj(undefined);
  };

  const handleCountyChange = (county: string) => {
    setSelectedCounty(county === selectedCounty ? "" : county);
    setSelectedCity(null);
  };

  const handleCityChange = (city: string) => {
    setSelectedCity(city === selectedCity ? "" : city);
  };

  const handlePriceRangeChange = (values: number[]) => {
    setSelectedPrice([values[0], values[1]]);
  };

  const getAvailableCities = () => {
    if (!selectedCounty) return [];
    return countiesWithCities[selectedCounty] || [];
  };

  return {
    activeCategory,
    selectedCounty,
    selectedCity,
    selectedPrice,
    selectedDateRange,
    selectedDateRangeObj,
    calendarOpen,
    searchTerm,
    setCalendarOpen,
    setSearchTerm,
    setSelectedDateRangeObj,
    handleCategoryChange,
    handleDateRangeChange,
    handleCountyChange,
    handleCityChange,
    handlePriceRangeChange,
    clearAllFilters,
    getAvailableCities,
    apiFilters,
  };
};

