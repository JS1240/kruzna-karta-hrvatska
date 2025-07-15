import React from 'react';
import { Calendar, Clock, MapPin, Euro, Star, Eye } from 'lucide-react';
import { Event } from '@/types/event';
import { format } from 'date-fns';
import clsx from 'clsx';

interface EventCardProps {
  event: Event;
  onClick?: (event: Event) => void;
  showViewCount?: boolean;
  variant?: 'default' | 'compact' | 'featured';
  className?: string;
}

export const EventCard: React.FC<EventCardProps> = ({
  event,
  onClick,
  showViewCount = false,
  variant = 'default',
  className,
}) => {
  const handleClick = () => {
    onClick?.(event);
  };

  const formattedDate = React.useMemo(() => {
    try {
      return format(new Date(event.date), 'MMM dd, yyyy');
    } catch {
      return event.date;
    }
  }, [event.date]);

  const statusColor = React.useMemo(() => {
    switch (event.event_status) {
      case 'active':
        return 'bg-green-100 text-green-800';
      case 'sold_out':
        return 'bg-red-100 text-red-800';
      case 'cancelled':
        return 'bg-gray-100 text-gray-800';
      case 'postponed':
        return 'bg-yellow-100 text-yellow-800';
      default:
        return 'bg-gray-100 text-gray-800';
    }
  }, [event.event_status]);

  const baseClasses = clsx(
    'bg-white rounded-xl shadow-sm hover:shadow-md transition-all duration-200 cursor-pointer group',
    'border border-gray-200 hover:border-primary-300',
    className
  );

  const contentClasses = clsx(
    'p-4',
    variant === 'compact' ? 'p-3' : 'p-4'
  );

  const imageClasses = clsx(
    'w-full object-cover rounded-t-xl',
    variant === 'compact' ? 'h-32' : 'h-48',
    variant === 'featured' ? 'h-56' : ''
  );

  return (
    <div className={baseClasses} onClick={handleClick}>
      {event.image && (
        <div className="relative overflow-hidden">
          <img
            src={event.image}
            alt={event.title}
            className={imageClasses}
          />
          {event.is_featured && (
            <div className="absolute top-3 left-3">
              <div className="flex items-center gap-1 bg-accent-500 text-white px-2 py-1 rounded-full text-xs font-medium">
                <Star className="w-3 h-3" />
                Featured
              </div>
            </div>
          )}
          <div className="absolute top-3 right-3">
            <span className={clsx('text-xs px-2 py-1 rounded-full font-medium', statusColor)}>
              {event.event_status.replace('_', ' ')}
            </span>
          </div>
        </div>
      )}

      <div className={contentClasses}>
        <div className="flex items-start justify-between mb-2">
          <h3 className={clsx(
            'font-semibold text-gray-900 group-hover:text-primary-600 transition-colors',
            variant === 'compact' ? 'text-sm line-clamp-2' : 'text-lg line-clamp-2'
          )}>
            {event.title}
          </h3>
          {showViewCount && event.view_count > 0 && (
            <div className="flex items-center gap-1 text-xs text-gray-500 ml-2">
              <Eye className="w-3 h-3" />
              {event.view_count}
            </div>
          )}
        </div>

        <div className="space-y-2 text-sm text-gray-600">
          <div className="flex items-center gap-2">
            <Calendar className="w-4 h-4 text-primary-500 flex-shrink-0" />
            <span>{formattedDate}</span>
          </div>

          <div className="flex items-center gap-2">
            <Clock className="w-4 h-4 text-primary-500 flex-shrink-0" />
            <span>{event.time}</span>
          </div>

          <div className="flex items-center gap-2">
            <MapPin className="w-4 h-4 text-primary-500 flex-shrink-0" />
            <span className="line-clamp-1">{event.location}</span>
          </div>

          {event.price && (
            <div className="flex items-center gap-2">
              <Euro className="w-4 h-4 text-primary-500 flex-shrink-0" />
              <span className="font-medium text-primary-600">{event.price}</span>
            </div>
          )}
        </div>

        {event.description && variant !== 'compact' && (
          <p className="text-sm text-gray-600 mt-3 line-clamp-2">
            {event.description}
          </p>
        )}

        <div className="flex items-center justify-between mt-4">
          <div className="flex items-center gap-2">
            {event.category && (
              <span className="inline-block px-2 py-1 bg-primary-100 text-primary-800 rounded-full text-xs font-medium">
                {event.category.name}
              </span>
            )}
            {event.venue && (
              <span className="inline-block px-2 py-1 bg-gray-100 text-gray-700 rounded-full text-xs">
                {event.venue.name}
              </span>
            )}
          </div>

          {event.organizer && (
            <span className="text-xs text-gray-500">
              by {event.organizer}
            </span>
          )}
        </div>

        {event.tags && event.tags.length > 0 && variant !== 'compact' && (
          <div className="flex flex-wrap gap-1 mt-3">
            {event.tags.slice(0, 3).map((tag, index) => (
              <span
                key={index}
                className="inline-block px-2 py-1 bg-gray-100 text-gray-600 rounded text-xs"
              >
                #{tag}
              </span>
            ))}
            {event.tags.length > 3 && (
              <span className="text-xs text-gray-500">
                +{event.tags.length - 3} more
              </span>
            )}
          </div>
        )}
      </div>
    </div>
  );
};

export default EventCard;