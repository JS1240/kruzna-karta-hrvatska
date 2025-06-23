import React, { memo } from "react";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";

interface LocationFilterProps {
  selectedCounty: string | null;
  selectedCity: string | null;
  countiesWithCities: Record<string, string[]>;
  availableCities: string[];
  onCountyChange: (county: string) => void;
  onCityChange: (city: string) => void;
}

export const LocationFilter = memo<LocationFilterProps>(({ 
  selectedCounty,
  selectedCity,
  countiesWithCities,
  availableCities,
  onCountyChange,
  onCityChange
}) => {
  const handleCountyChange = (county: string) => {
    try {
      onCountyChange(county);
    } catch (error) {
      console.error('County change error:', error, { county });
    }
  };

  const handleCityChange = (city: string) => {
    try {
      onCityChange(city);
    } catch (error) {
      console.error('City change error:', error, { city });
    }
  };

  return (
    <div className="space-y-2">
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
            {availableCities.map((city) => (
              <SelectItem key={city} value={city}>
                {city}
              </SelectItem>
            ))}
          </SelectContent>
        </Select>
      )}
    </div>
  );
});

LocationFilter.displayName = "LocationFilter";