/**
 * EventClusterPopup component for displaying multiple events in a cluster
 * Shows event list with details and actions
 */

import React, { useMemo } from 'react';
import { format, parseISO, isValid } from 'date-fns';
import { Calendar, Clock, MapPin, Euro, ExternalLink, X } from 'lucide-react';
import { Event } from '@/types/event';
import { EventCluster } from '@/utils/mapClustering';
import clsx from 'clsx';

interface EventClusterPopupProps {
  cluster: EventCluster;
  onClose?: () => void;
  onEventClick?: (event: Event) => void;
  onZoomToCluster?: (cluster: EventCluster) => void;
  maxHeight?: string;
  className?: string;
}

/**
 * Format date for display
 */
const formatEventDate = (dateString: string): string => {
  try {
    const date = parseISO(dateString);
    if (isValid(date)) {
      return format(date, 'MMM d, yyyy');
    }
  } catch {
    // Fallback for invalid dates
  }
  return dateString || 'Date TBD';
};

/**
 * Format time for display
 */
const formatEventTime = (timeString: string): string => {
  if (!timeString) return 'Time TBD';
  
  // Handle various time formats
  try {
    // Try parsing as ISO time
    const time = parseISO(`2000-01-01T${timeString}`);
    if (isValid(time)) {
      return format(time, 'HH:mm');
    }
  } catch {
    // Fallback to original string
  }
  
  return timeString;
};

/**
 * Format price for display
 */
const formatEventPrice = (price?: string): string => {
  if (!price) return 'Contact organizer';
  if (price.toLowerCase().includes('free')) return 'Free';
  if (price.includes('€') || price.includes('EUR')) return price;
  
  // Try to parse as number and add currency
  const numericPrice = parseFloat(price);
  if (!isNaN(numericPrice)) {
    return `€${numericPrice}`;
  }
  
  return price;
};

/**
 * Single event item component
 */
const EventItem: React.FC<{
  event: Event;
  onClick?: (event: Event) => void;
  isCompact?: boolean;
}> = ({ event, onClick, isCompact = false }) => {
  const handleClick = () => {
    onClick?.(event);
  };

  const handleExternalLink = (e: React.MouseEvent) => {
    e.stopPropagation();
    if (event.link) {
      window.open(event.link, '_blank', 'noopener,noreferrer');
    }
  };

  return (
    <div
      className={clsx(
        'border rounded-lg p-3 hover:bg-blue-50 transition-all duration-150 cursor-pointer',
        'border-gray-200 hover:border-blue-300 hover:shadow-sm',
        isCompact && 'p-2'
      )}
      onClick={handleClick}
    >
      <div className="flex justify-between items-start gap-2">
        <div className="flex-1 min-w-0">
          <h4 className={clsx(
            'font-semibold text-gray-900 truncate hover:text-blue-700',
            isCompact ? 'text-sm' : 'text-base'
          )}>
            {event.title}
          </h4>
          
          <div className="flex flex-wrap gap-3 mt-1 text-xs text-gray-600">
            <div className="flex items-center gap-1">
              <Calendar className="w-3 h-3 text-blue-500" />
              <span>{formatEventDate(event.date)}</span>
            </div>
            
            <div className="flex items-center gap-1">
              <Clock className="w-3 h-3 text-green-500" />
              <span>{formatEventTime(event.time)}</span>
            </div>
            
            {event.location && (
              <div className="flex items-center gap-1">
                <MapPin className="w-3 h-3 text-red-500" />
                <span className="truncate max-w-24">{event.location}</span>
              </div>
            )}
          </div>
          
          <div className="flex items-center justify-between mt-2">
            <div className="flex items-center gap-1 text-xs text-green-600">
              <Euro className="w-3 h-3" />
              <span className="font-medium">{formatEventPrice(event.price)}</span>
            </div>
            
            {event.link && (
              <button
                onClick={handleExternalLink}
                className={clsx(
                  'flex items-center gap-1 px-2 py-1 text-xs',
                  'text-blue-600 hover:text-blue-800 hover:bg-blue-100',
                  'rounded transition-colors duration-150'
                )}
                title="Open event link"
              >
                <span>View</span>
                <ExternalLink className="w-3 h-3" />
              </button>
            )}
          </div>
          
          {event.description && !isCompact && (
            <p className="text-xs text-gray-500 mt-2 line-clamp-2 leading-relaxed">
              {event.description}
            </p>
          )}
        </div>
      </div>
    </div>
  );
};

export const EventClusterPopup: React.FC<EventClusterPopupProps> = ({
  cluster,
  onClose,
  onEventClick,
  onZoomToCluster,
  maxHeight = '400px',
  className
}) => {
  const { events, isCluster, count, category } = cluster;

  // Sort events by date
  const sortedEvents = useMemo(() => {
    return [...events].sort((a, b) => {
      const dateA = new Date(a.date);
      const dateB = new Date(b.date);

      // Handle invalid dates
      const timeA = dateA.getTime();
      const timeB = dateB.getTime();

      if (isNaN(timeA) && isNaN(timeB)) return 0;
      if (isNaN(timeA)) return 1;  // Push invalid dates to end
      if (isNaN(timeB)) return -1;

      return timeA - timeB;
    });
  }, [events]);

  // Determine if we should show compact view
  const isCompact = count > 5;

  // Get popup title
  const title = isCluster 
    ? `${count} Events in This Area`
    : events[0].title;

  // Get category display
  const categoryDisplay = category && category !== 'other' && category !== 'mixed'
    ? category.charAt(0).toUpperCase() + category.slice(1)
    : null;

  return (
    <div
      className={clsx(
        'bg-white rounded-lg shadow-xl border border-gray-200',
        'min-w-80 max-w-96 overflow-hidden',
        className
      )}
      style={{ maxHeight }}
      onClick={(e) => e.stopPropagation()}
    >
      {/* Header */}
      <div className="flex items-center justify-between p-4 border-b border-gray-200 bg-gray-50">
        <div className="flex-1 min-w-0">
          <h3 className="font-semibold text-lg text-gray-900 truncate">
            {title}
          </h3>
          {categoryDisplay && (
            <p className="text-sm text-gray-600 mt-1">
              Category: {categoryDisplay}
            </p>
          )}
        </div>
        
        <div className="flex items-center gap-2 ml-3">
          {isCluster && onZoomToCluster && (
            <button
              onClick={() => onZoomToCluster(cluster)}
              className={clsx(
                'px-2 py-1 text-xs bg-blue-100 text-blue-700',
                'rounded hover:bg-blue-200 transition-colors'
              )}
              title="Zoom to show all events"
            >
              Zoom In
            </button>
          )}
          
          {onClose && (
            <button
              onClick={onClose}
              className={clsx(
                'p-1 text-gray-400 hover:text-gray-600 transition-colors',
                'rounded hover:bg-gray-100'
              )}
              title="Close popup"
            >
              <X className="w-4 h-4" />
            </button>
          )}
        </div>
      </div>

      {/* Event List */}
      <div
        className="overflow-y-auto"
        style={{ maxHeight: 'calc(100% - 80px)' }}
      >
        <div className="p-3 space-y-2">
          {sortedEvents.map((event) => (
            <EventItem
              key={event.id}
              event={event}
              onClick={onEventClick}
              isCompact={isCompact}
            />
          ))}
        </div>
      </div>

      {/* Footer with statistics */}
      {isCluster && (
        <div className="px-4 py-2 bg-gray-50 border-t border-gray-200">
          <div className="flex justify-between text-xs text-gray-600">
            <span>{count} total events</span>
            {category === 'mixed' ? (
              <span>Multiple categories</span>
            ) : (
              categoryDisplay && <span>{categoryDisplay} events</span>
            )}
          </div>
        </div>
      )}
    </div>
  );
};

/**
 * Enhanced popup for single events with comprehensive details
 */
export const SingleEventPopup: React.FC<{
  event: Event;
  onClose?: () => void;
  onEventClick?: (event: Event) => void;
  className?: string;
}> = ({ event, onClose, onEventClick, className }) => {
  const handleEventClick = () => {
    onEventClick?.(event);
  };

  const handleExternalLink = (e: React.MouseEvent) => {
    e.stopPropagation();
    if (event.link) {
      window.open(event.link, '_blank', 'noopener,noreferrer');
    }
  };

  return (
    <div
      className={clsx(
        'bg-white rounded-lg shadow-xl border border-gray-200',
        'w-80 max-w-sm overflow-hidden cursor-pointer',
        'transform transition-all duration-200 ease-out',
        'hover:shadow-2xl hover:scale-105',
        className
      )}
      onClick={handleEventClick}
    >
      {/* Header with title and close button */}
      <div className="p-4 border-b border-gray-100">
        <div className="flex justify-between items-start gap-2">
          <h3 className="font-bold text-lg text-gray-900 leading-tight">
            {event.title}
          </h3>
          {onClose && (
            <button
              onClick={(e) => {
                e.stopPropagation();
                onClose();
              }}
              className={clsx(
                'p-1 text-gray-400 hover:text-gray-600 transition-colors',
                'rounded hover:bg-gray-100'
              )}
              title="Close popup"
            >
              <X className="w-4 h-4" />
            </button>
          )}
        </div>
        
        {/* Event status badge */}
        {event.event_status && event.event_status !== 'active' && (
          <div className="mt-2">
            <span className={clsx(
              'inline-block px-2 py-1 text-xs font-medium rounded-full',
              event.event_status === 'cancelled' && 'bg-red-100 text-red-800',
              event.event_status === 'postponed' && 'bg-yellow-100 text-yellow-800',
              event.event_status === 'sold_out' && 'bg-orange-100 text-orange-800'
            )}>
              {event.event_status.replace('_', ' ').toUpperCase()}
            </span>
          </div>
        )}
      </div>
      
      {/* Main content */}
      <div className="p-4">
        {event.description && (
          <p className="text-sm text-gray-600 mb-4 line-clamp-3 leading-relaxed">
            {event.description}
          </p>
        )}
        
        <div className="space-y-3 text-sm">
          <div className="flex items-center gap-3 text-gray-700">
            <Calendar className="w-4 h-4 text-blue-500" />
            <span className="font-medium">{formatEventDate(event.date)}</span>
          </div>
          
          <div className="flex items-center gap-3 text-gray-700">
            <Clock className="w-4 h-4 text-green-500" />
            <span className="font-medium">{formatEventTime(event.time)}</span>
          </div>
          
          {event.location && (
            <div className="flex items-start gap-3 text-gray-700">
              <MapPin className="w-4 h-4 text-red-500 mt-0.5" />
              <span className="font-medium leading-5">{event.location}</span>
            </div>
          )}
          
          {/* Organizer information */}
          {event.organizer && (
            <div className="flex items-center gap-3 text-gray-700">
              <div className="w-4 h-4 bg-purple-500 rounded-full flex items-center justify-center">
                <span className="text-white text-xs font-bold">O</span>
              </div>
              <span className="font-medium">{event.organizer}</span>
            </div>
          )}
          
          {/* Age restriction */}
          {event.age_restriction && (
            <div className="flex items-center gap-3 text-gray-700">
              <div className="w-4 h-4 bg-orange-500 rounded-full flex items-center justify-center">
                <span className="text-white text-xs font-bold">!</span>
              </div>
              <span className="text-sm">Age: {event.age_restriction}</span>
            </div>
          )}
        </div>
      </div>
      
      {/* Footer with price and action button */}
      <div className="px-4 py-3 bg-gray-50 border-t border-gray-100">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            <Euro className="w-4 h-4 text-green-600" />
            <span className="font-semibold text-green-700 text-base">
              {formatEventPrice(event.price)}
            </span>
          </div>
          
          {event.link && (
            <button
              onClick={handleExternalLink}
              className={clsx(
                'flex items-center gap-2 px-3 py-1.5',
                'bg-blue-600 text-white text-sm font-medium rounded-md',
                'hover:bg-blue-700 active:bg-blue-800',
                'transition-colors duration-150',
                'shadow-sm hover:shadow-md'
              )}
              title="View full event details"
            >
              <span>View Event</span>
              <ExternalLink className="w-3 h-3" />
            </button>
          )}
        </div>
        
        {/* Event source */}
        {event.source && (
          <div className="mt-2 text-xs text-gray-500">
            Source: {event.source}
          </div>
        )}
      </div>
    </div>
  );
};

export default EventClusterPopup;