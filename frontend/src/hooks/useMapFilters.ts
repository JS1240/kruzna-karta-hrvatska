import { useState, useMemo } from "react";
import type { DateRange } from "react-day-picker";
import { MapFilters } from "@/lib/api";

const countiesWithCities = {
  "Split-Dalmatia": ["Split", "Makarska", "Trogir", "Omiš", "Hvar"],
  Zagreb: ["Zagreb", "Velika Gorica", "Samobor", "Zaprešić"],
  "Dubrovnik-Neretva": ["Dubrovnik", "Metković", "Ploče", "Korčula"],
  "Primorje-Gorski Kotar": ["Rijeka", "Opatija", "Crikvenica", "Krk"],
  Zadar: ["Zadar", "Biograd", "Pag", "Nin"],
  Istria: ["Pula", "Rovinj", "Poreč", "Umag"],
  "Lika-Senj": ["Gospić", "Senj", "Otočac", "Novalja"],
};

export const useMapFilters = () => {
  const [activeCategory, setActiveCategory] = useState<string | null>(null);
  const [selectedCounty, setSelectedCounty] = useState<string | null>(null);
  const [selectedCity, setSelectedCity] = useState<string | null>(null);
  const [selectedPrice, setSelectedPrice] = useState<[number, number] | null>(null);
  const [selectedDateRange, setSelectedDateRange] = useState<string | null>(null);
  const [selectedDateRangeObj, setSelectedDateRangeObj] = useState<DateRange | undefined>(undefined);
  const [calendarOpen, setCalendarOpen] = useState(false);
  const [searchTerm, setSearchTerm] = useState("");

  const getAvailableCities = () => {
    return selectedCounty ? countiesWithCities[selectedCounty as keyof typeof countiesWithCities] || [] : [];
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

  const handlePriceRangeChange = (value: [number, number]) => {
    setSelectedPrice(value);
  };

  const clearAllFilters = () => {
    setActiveCategory(null);
    setSelectedCounty(null);
    setSelectedCity(null);
    setSelectedPrice(null);
    setSelectedDateRange(null);
    setSelectedDateRangeObj(undefined);
    setSearchTerm("");
  };

  const getDateRangeFromSelection = (
    selection: string | null,
  ): [Date, Date] | null => {
    if (!selection) return null;

    const today = new Date();
    today.setHours(0, 0, 0, 0);

    const tomorrow = new Date(today);
    tomorrow.setDate(tomorrow.getDate() + 1);

    const thisWeekend = new Date(today);
    const dayOfWeek = today.getDay();
    const daysUntilWeekend =
      dayOfWeek === 0 || dayOfWeek === 6 ? 0 : 6 - dayOfWeek;
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
    const filters: MapFilters = {};

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

  return {
    activeCategory,
    selectedCounty,
    selectedCity,
    selectedPrice,
    selectedDateRange,
    selectedDateRangeObj,
    calendarOpen,
    searchTerm,
    setSearchTerm,
    handleCategoryChange,
    handleDateRangeChange,
    handleCountyChange,
    handleCityChange,
    handlePriceRangeChange,
    clearAllFilters,
    setCalendarOpen,
    setSelectedDateRangeObj,
    countiesWithCities,
    getAvailableCities,
    apiFilters,
  };
};

export type UseMapFiltersReturn = ReturnType<typeof useMapFilters>;
