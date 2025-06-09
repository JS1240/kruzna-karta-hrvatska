import React from "react";
import { Music, Dumbbell, Users, CalendarDays, PartyPopper } from "lucide-react";
import { Popover, PopoverContent, PopoverTrigger } from "@/components/ui/popover";
import { Button } from "@/components/ui/button";
import { ToggleGroup, ToggleGroupItem } from "@/components/ui/toggle-group";
import { Slider } from "@/components/ui/slider";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { Calendar } from "@/components/ui/calendar";
import { Alert, AlertDescription } from "@/components/ui/alert";
import { UseMapFiltersReturn } from "@/hooks/useMapFilters";

const categoryConfig = {
  concert: { icon: Music, color: "#e11d48", label: "Concerts" },
  music: { icon: Music, color: "#e11d48", label: "Music" },
  workout: { icon: Dumbbell, color: "#059669", label: "Sports & Fitness" },
  sports: { icon: Dumbbell, color: "#059669", label: "Sports" },
  meetup: { icon: Users, color: "#7c3aed", label: "Meetups" },
  conference: { icon: CalendarDays, color: "#dc2626", label: "Conferences" },
  party: { icon: PartyPopper, color: "#ea580c", label: "Parties" },
  festival: { icon: Music, color: "#db2777", label: "Festivals" },
  theater: { icon: CalendarDays, color: "#0891b2", label: "Theater" },
  culture: { icon: CalendarDays, color: "#0891b2", label: "Culture" },
  other: { icon: CalendarDays, color: "#6b7280", label: "Other" },
};

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

  return (
    <div className="absolute top-4 left-4 bg-white rounded-lg shadow-lg p-4 z-40 w-64 space-y-4">
      <Input
        placeholder="Search events..."
        value={searchTerm}
        onChange={(e) => setSearchTerm(e.target.value)}
      />

      {/* Category Filters */}
      <div className="space-y-2">
        <Label>Category</Label>
        <ToggleGroup
          type="single"
          value={activeCategory || ""}
          onValueChange={handleCategoryChange}
        >
          {Object.entries(categoryConfig).map(([key, config]) => {
            const IconComponent = config.icon;
            return (
              <ToggleGroupItem key={key} value={key} aria-label={config.label}>
                <IconComponent
                  className="h-4 w-4"
                  style={{ color: config.color }}
                />
              </ToggleGroupItem>
            );
          })}
        </ToggleGroup>
      </div>

      {/* Location Filters */}
      <div className="space-y-2">
        <Label>Location</Label>
        <Select value={selectedCounty || ""} onValueChange={handleCountyChange}>
          <SelectTrigger>
            <SelectValue placeholder="Select County" />
          </SelectTrigger>
          <SelectContent>
            {Object.keys(countiesWithCities).map((county) => (
              <SelectItem key={county} value={county}>
                {county}
              </SelectItem>
            ))}
          </SelectContent>
        </Select>

        {selectedCounty && (
          <Select value={selectedCity || ""} onValueChange={handleCityChange}>
            <SelectTrigger>
              <SelectValue placeholder="Select City" />
            </SelectTrigger>
            <SelectContent>
              {getAvailableCities().map((city) => (
                <SelectItem key={city} value={city}>
                  {city}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
        )}
      </div>

      {/* Date Range Filter */}
      <div>
        <Label>Date Range</Label>
        <ToggleGroup
          type="single"
          value={selectedDateRange || ""}
          onValueChange={handleDateRangeChange}
        >
          <ToggleGroupItem value="today">Today</ToggleGroupItem>
          <ToggleGroupItem value="tomorrow">Tomorrow</ToggleGroupItem>
          <ToggleGroupItem value="this-weekend">Weekend</ToggleGroupItem>
          <ToggleGroupItem value="this-month">This Month</ToggleGroupItem>
        </ToggleGroup>

        <Popover open={calendarOpen} onOpenChange={setCalendarOpen}>
          <PopoverTrigger asChild>
            <Button variant="outline" className="w-full mt-2">
              {selectedDateRangeObj?.from
                ? selectedDateRangeObj.to
                  ? `${selectedDateRangeObj.from.toLocaleDateString()} - ${selectedDateRangeObj.to.toLocaleDateString()}`
                  : selectedDateRangeObj.from.toLocaleDateString()
                : "Pick custom dates"}
            </Button>
          </PopoverTrigger>
          <PopoverContent className="w-auto p-0" align="start">
            <Calendar
              initialFocus
              mode="range"
              defaultMonth={selectedDateRangeObj?.from}
              selected={selectedDateRangeObj}
              onSelect={setSelectedDateRangeObj}
              numberOfMonths={2}
            />
          </PopoverContent>
        </Popover>
      </div>

      {/* Price Range Filter */}
      <div>
        <Label>Price Range (EUR)</Label>
        <div className="px-2 py-4">
          <Slider
            defaultValue={[0, 200]}
            max={500}
            step={10}
            value={selectedPrice || [0, 500]}
            onValueChange={handlePriceRangeChange}
          />
          <div className="flex justify-between text-xs text-gray-500 mt-1">
            <span>{selectedPrice?.[0] || 0}€</span>
            <span>{selectedPrice?.[1] || 500}€</span>
          </div>
        </div>
      </div>

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
};

export default MapFilters;
