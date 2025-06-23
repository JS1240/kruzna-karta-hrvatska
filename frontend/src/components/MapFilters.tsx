import React, { useState, useCallback } from "react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Alert, AlertDescription } from "@/components/ui/alert";
import { Sheet, SheetContent, SheetHeader, SheetTitle, SheetTrigger } from "@/components/ui/sheet";
import { Badge } from "@/components/ui/badge";
import { Filter } from "lucide-react";
import { UseMapFiltersReturn } from "@/hooks/useMapFilters";
import { useIsMobile } from "@/hooks/use-mobile";
import { countActiveFilters } from "@/lib/filterUtils";
import { CategoryFilter } from "./filters/CategoryFilter";
import { PriceFilter } from "./filters/PriceFilter";
import { DateFilter } from "./filters/DateFilter";
import { LocationFilter } from "./filters/LocationFilter";
import { cn } from "@/lib/utils";

interface MapFiltersProps {
  filters: UseMapFiltersReturn;
  filteredCount: number;
  total: number;
  error: string | null;
}

export const MapFilters: React.FC<MapFiltersProps> = ({
  filters,
  filteredCount,
  total,
  error,
}) => {
  const isMobile = useIsMobile();
  const [isOpen, setIsOpen] = useState(false);
  
  const {
    activeCategory,
    selectedCounty,
    selectedCity,
    selectedDateRange,
    selectedDateRangeObj,
    calendarOpen,
    selectedPrice,
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
  } = filters;

  // Count active filters for badge using utility function
  const activeFiltersCount = countActiveFilters({
    activeCategory,
    selectedCounty,
    selectedCity,
    selectedDateRange,
    selectedDateRangeObj,
    selectedPrice,
    searchTerm
  });

  const handleSearchTermChange = useCallback((e: React.ChangeEvent<HTMLInputElement>) => {
    setSearchTerm(e.target.value);
  }, [setSearchTerm]);

  const FilterContent = () => (
    <div className={cn("space-y-3", isMobile ? "p-0" : "")}>
      <Input
        placeholder="Search events..."
        value={searchTerm}
        onChange={handleSearchTermChange}
      />

      {/* Category Filters - No label as per requirements */}
      <CategoryFilter
        activeCategory={activeCategory}
        onCategoryChange={handleCategoryChange}
        isMobile={isMobile}
      />

      {/* Location Filters - No label as per requirements */}
      <LocationFilter
        selectedCounty={selectedCounty}
        selectedCity={selectedCity}
        countiesWithCities={countiesWithCities}
        availableCities={getAvailableCities()}
        onCountyChange={handleCountyChange}
        onCityChange={handleCityChange}
      />

      {/* Date Range Filter - No label as per requirements */}
      <DateFilter
        selectedDateRange={selectedDateRange}
        selectedDateRangeObj={selectedDateRangeObj}
        calendarOpen={calendarOpen}
        onDateRangeChange={handleDateRangeChange}
        onCalendarOpenChange={setCalendarOpen}
        onDateRangeObjChange={setSelectedDateRangeObj}
        isMobile={isMobile}
      />

      {/* Price Range Filter - No label as per requirements */}
      <PriceFilter
        selectedPrice={selectedPrice}
        onPriceChange={handlePriceRangeChange}
      />

      <Button variant="outline" onClick={clearAllFilters} className="w-full">
        Clear All Filters
      </Button>

      <div className="text-sm text-gray-600 text-center">
        Showing {filteredCount} of {total} events
      </div>

      {error && (
        <Alert variant="destructive">
          <AlertDescription>{error}</AlertDescription>
        </Alert>
      )}
    </div>
  );

  // Universal filter toggle button for all screen sizes
  return (
    <>
      {/* Filter Toggle Button - positioned absolutely within map */}
      <div className="absolute bottom-20 left-4 z-50">
        <Sheet open={isOpen} onOpenChange={setIsOpen}>
          <SheetTrigger asChild>
            <Button className="relative shadow-lg bg-blue-600 hover:bg-blue-700 text-white px-4 py-3">
              <Filter className="h-4 w-4 mr-2" />
              Filters
              {activeFiltersCount > 0 && (
                <Badge variant="destructive" className="absolute -top-2 -right-2 h-5 w-5 p-0 flex items-center justify-center text-xs">
                  {activeFiltersCount}
                </Badge>
              )}
            </Button>
          </SheetTrigger>
          <SheetContent side="left" className={cn("overflow-y-auto", isMobile ? "w-80" : "w-96")}>
            <SheetHeader>
              <SheetTitle>Filter Events</SheetTitle>
            </SheetHeader>
            <div className="mt-4 overflow-y-auto max-h-[calc(100vh-8rem)]">
              <FilterContent />
            </div>
          </SheetContent>
        </Sheet>
      </div>
    </>
  );
};

export default MapFilters;
