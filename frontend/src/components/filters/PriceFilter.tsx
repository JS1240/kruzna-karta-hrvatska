import React, { memo } from "react";
import { Slider } from "@/components/ui/slider";

interface PriceFilterProps {
  selectedPrice: [number, number] | null;
  onPriceChange: (value: [number, number]) => void;
}

export const PriceFilter = memo<PriceFilterProps>(({ 
  selectedPrice, 
  onPriceChange 
}) => {
  const handlePriceChange = (value: [number, number]) => {
    try {
      onPriceChange(value);
    } catch (error) {
      console.error('Price change error:', error, { value });
    }
  };

  return (
    <div>
      <div className="px-2 py-4">
        <Slider
          defaultValue={[0, 200]}
          max={500}
          step={10}
          value={selectedPrice || [0, 500]}
          onValueChange={handlePriceChange}
        />
        <div className="flex justify-between text-xs text-gray-500 mt-1">
          <span>{selectedPrice?.[0] || 0}€</span>
          <span>{selectedPrice?.[1] || 500}€</span>
        </div>
      </div>
    </div>
  );
});

PriceFilter.displayName = "PriceFilter";