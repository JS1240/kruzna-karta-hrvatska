import React from "react";
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
import { Popover, PopoverContent, PopoverTrigger } from "@/components/ui/popover";
import { Calendar } from "@/components/ui/calendar";
import type { DateRange } from "react-day-picker";

interface CategoryConfigItem {
  icon: React.ComponentType<{ className?: string; style?: React.CSSProperties }>;
  color: string;
  label: string;
}

interface MapFiltersProps {
  categoryConfig: Record<string, CategoryConfigItem>;
  counties: string[];
  searchTerm: string;
  setSearchTerm: (term: string) => void;
  activeCategory: string | null;
  selectedCounty: string | null;
  selectedCity: string | null;
  selectedPrice: [number, number] | null;
  selectedDateRange: string | null;
  selectedDateRangeObj?: DateRange;
  calendarOpen: boolean;
  setCalendarOpen: (open: boolean) => void;
  handleCategoryChange: (c: string | null) => void;
  handleCountyChange: (c: string) => void;
  handleCityChange: (c: string) => void;
  handleDateRangeChange: (v: string) => void;
  setSelectedDateRangeObj: (d: DateRange | undefined) => void;
  handlePriceRangeChange: (v: number[]) => void;
  clearAllFilters: () => void;
  getAvailableCities: () => string[];
  filteredCount: number;
  totalCount: number;
}

const MapFilters: React.FC<MapFiltersProps> = ({
  categoryConfig,
  counties,
  searchTerm,
  setSearchTerm,
  activeCategory,
  selectedCounty,
  selectedCity,
  selectedPrice,
  selectedDateRange,
  selectedDateRangeObj,
  calendarOpen,
  setCalendarOpen,
  handleCategoryChange,
  handleCountyChange,
  handleCityChange,
  handleDateRangeChange,
  setSelectedDateRangeObj,
  handlePriceRangeChange,
  clearAllFilters,
  getAvailableCities,
  filteredCount,
  totalCount,
}) => {
  return (
    <div className="absolute top-4 left-4 bg-white rounded-lg shadow-lg p-4 z-40 space-y-4 w-64 overflow-y-auto max-h-[90vh]">
      <Input
        placeholder="Search events..."
        value={searchTerm}
        onChange={(e) => setSearchTerm(e.target.value)}
      />

      <div className="space-y-2">
        <Label>Category</Label>
        <ToggleGroup
          type="single"
          value={activeCategory || ""}
          onValueChange={handleCategoryChange}
        >
          {Object.entries(categoryConfig).map(([key, config]) => {
            const Icon = config.icon;
            return (
              <ToggleGroupItem key={key} value={key} aria-label={config.label}>
                <Icon className="h-4 w-4" style={{ color: config.color }} />
              </ToggleGroupItem>
            );
          })}
        </ToggleGroup>
      </div>

      <div className="space-y-2">
        <Label>Location</Label>
        <Select value={selectedCounty || ""} onValueChange={handleCountyChange}>
          <SelectTrigger>
            <SelectValue placeholder="Select County" />
          </SelectTrigger>
          <SelectContent>
            {counties.map((county) => (
              <SelectItem key={county} value={county}>
                {county}
              </SelectItem>
            ))}
          </SelectContent>
        </Select>
      </div>

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
        Showing {filteredCount} of {totalCount} events
      </div>
    </div>
  );
};

export default MapFilters;
