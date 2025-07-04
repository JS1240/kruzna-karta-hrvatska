/**
 * TouchForms Components
 * 
 * Touch-optimized form components including date pickers,
 * number inputs, and mobile-friendly form controls.
 */

import React, { useState, useRef, useCallback } from 'react';
import { 
  Calendar,
  ChevronDown,
  ChevronUp,
  Check,
  X,
  Search,
  MapPin,
  Clock,
} from 'lucide-react';
import { TouchButton, TouchCounter } from './TouchControls';
import { useReducedMotion } from '@/hooks/useReducedMotion';
import { detectTouchDevice, getTouchOptimizedClasses } from '@/utils/touchUtils';
import { cn } from '@/lib/utils';

/**
 * Touch-optimized Date Picker
 */
export interface TouchDatePickerProps {
  value?: Date;
  onChange: (date: Date) => void;
  placeholder?: string;
  disabled?: boolean;
  minDate?: Date;
  maxDate?: Date;
  className?: string;
}

export const TouchDatePicker: React.FC<TouchDatePickerProps> = ({
  value,
  onChange,
  placeholder = 'Select date',
  disabled = false,
  minDate,
  maxDate,
  className = '',
}) => {
  const [isOpen, setIsOpen] = useState(false);
  const [selectedDate, setSelectedDate] = useState(value || new Date());
  
  const device = detectTouchDevice();
  const touchClasses = getTouchOptimizedClasses(device);
  const { getClassName } = useReducedMotion();

  const formatDate = (date: Date) => {
    return date.toLocaleDateString('en-US', {
      weekday: 'short',
      year: 'numeric',
      month: 'short',
      day: 'numeric',
    });
  };

  const handleDateSelect = (date: Date) => {
    setSelectedDate(date);
    onChange(date);
    setIsOpen(false);
  };

  const generateCalendarDays = () => {
    const year = selectedDate.getFullYear();
    const month = selectedDate.getMonth();
    const firstDay = new Date(year, month, 1);
    const lastDay = new Date(year, month + 1, 0);
    const daysInMonth = lastDay.getDate();
    const startingDayOfWeek = firstDay.getDay();

    const days = [];
    
    // Add empty cells for days before the first day of the month
    for (let i = 0; i < startingDayOfWeek; i++) {
      days.push(null);
    }
    
    // Add days of the month
    for (let day = 1; day <= daysInMonth; day++) {
      days.push(new Date(year, month, day));
    }
    
    return days;
  };

  const inputClasses = getClassName(
    'w-full flex items-center justify-between px-4 py-3 border border-gray-300 rounded-lg bg-white focus:outline-none focus:ring-2 focus:ring-brand-primary focus:border-transparent transition-all',
    touchClasses.touchTarget,
    ''
  );

  return (
    <div className={cn('relative', className)}>
      {/* Date Input Trigger */}
      <button
        onClick={() => setIsOpen(!isOpen)}
        disabled={disabled}
        className={cn(
          inputClasses,
          touchClasses.interactive,
          disabled && 'opacity-50 cursor-not-allowed'
        )}
        aria-label="Open date picker"
      >
        <div className="flex items-center gap-2">
          <Calendar className="h-5 w-5 text-gray-500" />
          <span className={value ? 'text-gray-900' : 'text-gray-500'}>
            {value ? formatDate(value) : placeholder}
          </span>
        </div>
        <ChevronDown className={cn(
          'h-5 w-5 text-gray-500 transition-transform',
          isOpen && 'rotate-180'
        )} />
      </button>

      {/* Calendar Dropdown */}
      {isOpen && (
        <div className="absolute top-full left-0 right-0 mt-2 bg-white border border-gray-300 rounded-lg shadow-xl z-50 p-4">
          {/* Month/Year Header */}
          <div className="flex items-center justify-between mb-4">
            <TouchButton
              variant="ghost"
              size="small"
              onClick={() => {
                const newDate = new Date(selectedDate);
                newDate.setMonth(newDate.getMonth() - 1);
                setSelectedDate(newDate);
              }}
              aria-label="Previous month"
            >
              <ChevronDown className="h-4 w-4 rotate-90" />
            </TouchButton>
            
            <h3 className="font-semibold text-lg">
              {selectedDate.toLocaleDateString('en-US', { 
                month: 'long',
                year: 'numeric'
              })}
            </h3>
            
            <TouchButton
              variant="ghost"
              size="small"
              onClick={() => {
                const newDate = new Date(selectedDate);
                newDate.setMonth(newDate.getMonth() + 1);
                setSelectedDate(newDate);
              }}
              aria-label="Next month"
            >
              <ChevronDown className="h-4 w-4 -rotate-90" />
            </TouchButton>
          </div>

          {/* Days of Week */}
          <div className="grid grid-cols-7 gap-1 mb-2">
            {['Sun', 'Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat'].map(day => (
              <div key={day} className="text-center text-sm font-medium text-gray-500 py-2">
                {day}
              </div>
            ))}
          </div>

          {/* Calendar Days */}
          <div className="grid grid-cols-7 gap-1">
            {generateCalendarDays().map((date, index) => {
              if (!date) {
                return <div key={index} className="p-2" />;
              }

              const isSelected = value && date.toDateString() === value.toDateString();
              const isToday = date.toDateString() === new Date().toDateString();
              const isDisabled = 
                (minDate && date < minDate) || 
                (maxDate && date > maxDate);

              return (
                <button
                  key={index}
                  onClick={() => !isDisabled && handleDateSelect(date)}
                  disabled={isDisabled}
                  className={cn(
                    'p-2 rounded-lg text-sm font-medium transition-colors',
                    touchClasses.touchTarget,
                    isSelected && 'bg-brand-primary text-white',
                    !isSelected && isToday && 'bg-brand-primary/10 text-brand-primary',
                    !isSelected && !isToday && !isDisabled && 'hover:bg-gray-100',
                    isDisabled && 'text-gray-300 cursor-not-allowed'
                  )}
                >
                  {date.getDate()}
                </button>
              );
            })}
          </div>

          {/* Actions */}
          <div className="flex gap-2 mt-4">
            <TouchButton
              variant="ghost"
              size="small"
              onClick={() => setIsOpen(false)}
              className="flex-1"
            >
              Cancel
            </TouchButton>
            <TouchButton
              variant="primary"
              size="small"
              onClick={() => handleDateSelect(new Date())}
              className="flex-1"
            >
              Today
            </TouchButton>
          </div>
        </div>
      )}
    </div>
  );
};

/**
 * Touch-optimized Time Picker
 */
export interface TouchTimePickerProps {
  value?: { hours: number; minutes: number };
  onChange: (time: { hours: number; minutes: number }) => void;
  format?: '12h' | '24h';
  placeholder?: string;
  disabled?: boolean;
  className?: string;
}

export const TouchTimePicker: React.FC<TouchTimePickerProps> = ({
  value = { hours: 12, minutes: 0 },
  onChange,
  format = '12h',
  placeholder = 'Select time',
  disabled = false,
  className = '',
}) => {
  const [isOpen, setIsOpen] = useState(false);
  const [selectedTime, setSelectedTime] = useState(value);
  const [period, setPeriod] = useState<'AM' | 'PM'>('AM');

  const device = detectTouchDevice();
  const touchClasses = getTouchOptimizedClasses(device);

  const formatTime = (time: { hours: number; minutes: number }) => {
    if (format === '12h') {
      const displayHours = time.hours === 0 ? 12 : time.hours > 12 ? time.hours - 12 : time.hours;
      const period = time.hours >= 12 ? 'PM' : 'AM';
      return `${displayHours}:${time.minutes.toString().padStart(2, '0')} ${period}`;
    } else {
      return `${time.hours.toString().padStart(2, '0')}:${time.minutes.toString().padStart(2, '0')}`;
    }
  };

  const handleTimeChange = (newTime: { hours: number; minutes: number }) => {
    setSelectedTime(newTime);
    onChange(newTime);
  };

  return (
    <div className={cn('relative', className)}>
      {/* Time Input Trigger */}
      <button
        onClick={() => setIsOpen(!isOpen)}
        disabled={disabled}
        className={cn(
          'w-full flex items-center justify-between px-4 py-3 border border-gray-300 rounded-lg bg-white focus:outline-none focus:ring-2 focus:ring-brand-primary transition-all',
          touchClasses.touchTarget,
          touchClasses.interactive,
          disabled && 'opacity-50 cursor-not-allowed'
        )}
      >
        <div className="flex items-center gap-2">
          <Clock className="h-5 w-5 text-gray-500" />
          <span className="text-gray-900">
            {formatTime(selectedTime)}
          </span>
        </div>
        <ChevronDown className={cn(
          'h-5 w-5 text-gray-500 transition-transform',
          isOpen && 'rotate-180'
        )} />
      </button>

      {/* Time Picker Dropdown */}
      {isOpen && (
        <div className="absolute top-full left-0 right-0 mt-2 bg-white border border-gray-300 rounded-lg shadow-xl z-50 p-4">
          <div className="flex items-center justify-center gap-4">
            {/* Hours */}
            <div className="text-center">
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Hours
              </label>
              <TouchCounter
                value={selectedTime.hours}
                min={format === '12h' ? 1 : 0}
                max={format === '12h' ? 12 : 23}
                onChange={(hours) => handleTimeChange({ ...selectedTime, hours })}
                showInput={true}
              />
            </div>

            <div className="text-2xl font-bold text-gray-500 mt-6">:</div>

            {/* Minutes */}
            <div className="text-center">
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Minutes
              </label>
              <TouchCounter
                value={selectedTime.minutes}
                min={0}
                max={59}
                step={5}
                onChange={(minutes) => handleTimeChange({ ...selectedTime, minutes })}
                showInput={true}
              />
            </div>

            {/* AM/PM Toggle for 12h format */}
            {format === '12h' && (
              <div className="text-center">
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Period
                </label>
                <div className="flex flex-col gap-2">
                  <TouchButton
                    variant={period === 'AM' ? 'primary' : 'ghost'}
                    size="small"
                    onClick={() => setPeriod('AM')}
                  >
                    AM
                  </TouchButton>
                  <TouchButton
                    variant={period === 'PM' ? 'primary' : 'ghost'}
                    size="small"
                    onClick={() => setPeriod('PM')}
                  >
                    PM
                  </TouchButton>
                </div>
              </div>
            )}
          </div>

          {/* Actions */}
          <div className="flex gap-2 mt-6">
            <TouchButton
              variant="ghost"
              onClick={() => setIsOpen(false)}
              className="flex-1"
            >
              Cancel
            </TouchButton>
            <TouchButton
              variant="primary"
              onClick={() => setIsOpen(false)}
              className="flex-1"
            >
              Done
            </TouchButton>
          </div>
        </div>
      )}
    </div>
  );
};

/**
 * Touch-optimized Search Input
 */
export interface TouchSearchProps {
  value: string;
  onChange: (value: string) => void;
  onSearch?: (value: string) => void;
  placeholder?: string;
  suggestions?: string[];
  loading?: boolean;
  className?: string;
}

export const TouchSearch: React.FC<TouchSearchProps> = ({
  value,
  onChange,
  onSearch,
  placeholder = 'Search...',
  suggestions = [],
  loading = false,
  className = '',
}) => {
  const [isFocused, setIsFocused] = useState(false);
  const [showSuggestions, setShowSuggestions] = useState(false);
  const inputRef = useRef<HTMLInputElement>(null);

  const device = detectTouchDevice();
  const touchClasses = getTouchOptimizedClasses(device);

  const handleSearch = () => {
    onSearch?.(value);
    setShowSuggestions(false);
    inputRef.current?.blur();
  };

  const handleSuggestionSelect = (suggestion: string) => {
    onChange(suggestion);
    onSearch?.(suggestion);
    setShowSuggestions(false);
    inputRef.current?.blur();
  };

  return (
    <div className={cn('relative', className)}>
      {/* Search Input */}
      <div className="relative">
        <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-5 w-5 text-gray-500" />
        <input
          ref={inputRef}
          type="text"
          value={value}
          onChange={(e) => onChange(e.target.value)}
          onFocus={() => {
            setIsFocused(true);
            setShowSuggestions(suggestions.length > 0);
          }}
          onBlur={() => {
            setIsFocused(false);
            setTimeout(() => setShowSuggestions(false), 200);
          }}
          onKeyDown={(e) => {
            if (e.key === 'Enter') {
              handleSearch();
            }
          }}
          placeholder={placeholder}
          className={cn(
            'w-full pl-10 pr-12 py-3 border border-gray-300 rounded-lg bg-white focus:outline-none focus:ring-2 focus:ring-brand-primary focus:border-transparent transition-all',
            touchClasses.touchTarget
          )}
        />
        
        {/* Clear/Search Button */}
        {value && (
          <button
            onClick={value ? () => onChange('') : handleSearch}
            className={cn(
              'absolute right-2 top-1/2 -translate-y-1/2 p-1 rounded-full hover:bg-gray-100 transition-colors',
              touchClasses.interactive
            )}
          >
            {value ? (
              <X className="h-4 w-4 text-gray-500" />
            ) : (
              <Search className="h-4 w-4 text-gray-500" />
            )}
          </button>
        )}
      </div>

      {/* Suggestions */}
      {showSuggestions && suggestions.length > 0 && (
        <div className="absolute top-full left-0 right-0 mt-1 bg-white border border-gray-300 rounded-lg shadow-xl z-50 max-h-60 overflow-y-auto">
          {suggestions.map((suggestion, index) => (
            <button
              key={index}
              onClick={() => handleSuggestionSelect(suggestion)}
              className={cn(
                'w-full text-left px-4 py-3 hover:bg-gray-50 transition-colors border-b border-gray-100 last:border-b-0',
                touchClasses.touchTarget
              )}
            >
              <div className="flex items-center gap-2">
                <Search className="h-4 w-4 text-gray-400" />
                <span>{suggestion}</span>
              </div>
            </button>
          ))}
        </div>
      )}
    </div>
  );
};

export default {
  TouchDatePicker,
  TouchTimePicker,
  TouchSearch,
};