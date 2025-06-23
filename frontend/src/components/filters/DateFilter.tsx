import React, { memo } from "react";
import { Popover, PopoverContent, PopoverTrigger } from "@/components/ui/popover";
import { Button } from "@/components/ui/button";
import { Calendar } from "@/components/ui/calendar";
import { ToggleGroup, ToggleGroupItem } from "@/components/ui/toggle-group";
import { cn } from "@/lib/utils";
import type { DateRange } from "react-day-picker";

interface DateFilterProps {
  selectedDateRange: string | null;
  selectedDateRangeObj: DateRange | undefined;
  calendarOpen: boolean;
  onDateRangeChange: (value: string) => void;
  onCalendarOpenChange: (open: boolean) => void;
  onDateRangeObjChange: (range: DateRange | undefined) => void;
  isMobile: boolean;
}

export const DateFilter = memo<DateFilterProps>(({ 
  selectedDateRange,
  selectedDateRangeObj,
  calendarOpen,
  onDateRangeChange,
  onCalendarOpenChange,
  onDateRangeObjChange,
  isMobile
}) => {
  const handleDateRangeChange = (value: string) => {
    try {
      onDateRangeChange(value);
    } catch (error) {
      console.error('Date range change error:', error, { value });
    }
  };

  const handleDateRangeObjChange = (range: DateRange | undefined) => {
    try {
      onDateRangeObjChange(range);
    } catch (error) {
      console.error('Date range object change error:', error, { range });
    }
  };

  return (
    <div className="space-y-2">
      <ToggleGroup
        type="single"
        value={selectedDateRange || ""}
        onValueChange={handleDateRangeChange}
        className={isMobile ? "grid grid-cols-2 gap-1" : ""}
      >
        <ToggleGroupItem value="today" className={isMobile ? "text-xs" : ""}>
          Today
        </ToggleGroupItem>
        <ToggleGroupItem value="tomorrow" className={isMobile ? "text-xs" : ""}>
          Tomorrow
        </ToggleGroupItem>
        <ToggleGroupItem value="this-weekend" className={isMobile ? "text-xs" : ""}>
          Weekend
        </ToggleGroupItem>
        <ToggleGroupItem value="this-month" className={isMobile ? "text-xs" : ""}>
          This Month
        </ToggleGroupItem>
      </ToggleGroup>

      <Popover open={calendarOpen} onOpenChange={onCalendarOpenChange}>
        <PopoverTrigger asChild>
          <Button variant="outline" className="w-full">
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
            onSelect={handleDateRangeObjChange}
            numberOfMonths={isMobile ? 1 : 2}
          />
        </PopoverContent>
      </Popover>
    </div>
  );
});

DateFilter.displayName = "DateFilter";