import React from 'react';
import { Star, ChevronRight, Calendar, MapPin } from 'lucide-react';
import { useFeaturedEvents } from '@/hooks/useEvents';
import { Event } from '@/types/event';
import { EventCard } from './EventCard';
import { format } from 'date-fns';
import clsx from 'clsx';

interface FeaturedEventsProps {
  onEventClick?: (event: Event) => void;
  className?: string;
  maxEvents?: number;
}

const FeaturedEventSkeleton: React.FC = () => (
  <div className="bg-white rounded-xl shadow-sm border border-gray-200 animate-pulse">
    <div className="h-48 bg-gray-200 rounded-t-xl"></div>
    <div className="p-4">
      <div className="h-6 bg-gray-200 rounded mb-2"></div>
      <div className="h-4 bg-gray-200 rounded w-3/4 mb-2"></div>
      <div className="h-4 bg-gray-200 rounded w-1/2 mb-2"></div>
      <div className="h-4 bg-gray-200 rounded w-2/3"></div>
    </div>
  </div>
);

const FeaturedEventHero: React.FC<{
  event: Event;
  onClick?: (event: Event) => void;
}> = ({ event, onClick }) => {
  const formattedDate = React.useMemo(() => {
    try {
      return format(new Date(event.date), 'MMMM dd, yyyy');
    } catch {
      return event.date;
    }
  }, [event.date]);

  return (
    <div
      className="relative h-96 rounded-xl overflow-hidden cursor-pointer group"
      onClick={() => onClick?.(event)}
    >
      {event.image && (
        <img
          src={event.image}
          alt={event.title}
          className="w-full h-full object-cover transition-transform duration-300 group-hover:scale-105"
        />
      )}
      <div className="absolute inset-0 bg-gradient-to-t from-black/80 via-black/40 to-transparent"></div>
      
      <div className="absolute top-4 left-4">
        <div className="flex items-center gap-1 bg-accent-500 text-white px-3 py-1 rounded-full text-sm font-medium">
          <Star className="w-4 h-4" />
          Featured Event
        </div>
      </div>

      <div className="absolute bottom-0 left-0 right-0 p-6 text-white">
        <div className="flex items-center gap-2 text-sm mb-2">
          <Calendar className="w-4 h-4" />
          <span>{formattedDate}</span>
          <span className="text-gray-300">•</span>
          <span>{event.time}</span>
        </div>
        
        <h2 className="text-2xl font-bold mb-2 line-clamp-2">{event.title}</h2>
        
        <div className="flex items-center gap-2 text-sm mb-4">
          <MapPin className="w-4 h-4" />
          <span>{event.location}</span>
        </div>
        
        {event.description && (
          <p className="text-gray-200 line-clamp-2 mb-4">{event.description}</p>
        )}
        
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-3">
            {event.category && (
              <span className="bg-white/20 text-white px-2 py-1 rounded-full text-xs">
                {event.category.name}
              </span>
            )}
            {event.price && (
              <span className="bg-primary-500 text-white px-2 py-1 rounded-full text-xs font-medium">
                {event.price}
              </span>
            )}
          </div>
          
          <div className="flex items-center gap-1 text-sm hover:text-accent-300 transition-colors">
            <span>View Details</span>
            <ChevronRight className="w-4 h-4" />
          </div>
        </div>
      </div>
    </div>
  );
};

export const FeaturedEvents: React.FC<FeaturedEventsProps> = ({
  onEventClick,
  className,
  maxEvents = 6,
}) => {
  const { data: eventsResponse, isLoading, error } = useFeaturedEvents(1, maxEvents);

  if (error) {
    return (
      <div className={clsx('container py-8', className)}>
        <div className="text-center py-12">
          <div className="text-red-500 text-lg font-medium mb-2">
            Failed to load featured events
          </div>
          <p className="text-gray-600">
            Please try again later or contact support if the problem persists.
          </p>
        </div>
      </div>
    );
  }

  const events = eventsResponse?.events || [];
  const [heroEvent, ...remainingEvents] = events;

  return (
    <section className={clsx('container py-12', className)}>
      <div className="mb-8">
        <div className="flex items-center gap-2 mb-2">
          <Star className="w-6 h-6 text-accent-500" />
          <h2 className="text-3xl font-bold text-gray-900">Featured Events</h2>
        </div>
        <p className="text-gray-600">
          Discover the most exciting events happening in Croatia
        </p>
      </div>

      {isLoading ? (
        <div className="space-y-8">
          <div className="h-96 bg-gray-200 rounded-xl animate-pulse"></div>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {Array.from({ length: 6 }).map((_, i) => (
              <FeaturedEventSkeleton key={i} />
            ))}
          </div>
        </div>
      ) : events.length === 0 ? (
        <div className="text-center py-12">
          <Star className="w-12 h-12 text-gray-400 mx-auto mb-4" />
          <h3 className="text-xl font-medium text-gray-900 mb-2">
            No Featured Events
          </h3>
          <p className="text-gray-600">
            Check back later for featured events in your area.
          </p>
        </div>
      ) : (
        <div className="space-y-8">
          {/* Hero Featured Event */}
          {heroEvent && (
            <FeaturedEventHero
              event={heroEvent}
              onClick={onEventClick}
            />
          )}

          {/* Grid of Other Featured Events */}
          {remainingEvents.length > 0 && (
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
              {remainingEvents.map((event) => (
                <EventCard
                  key={event.id}
                  event={event}
                  onClick={onEventClick}
                  variant="featured"
                  showViewCount={true}
                />
              ))}
            </div>
          )}
        </div>
      )}
    </section>
  );
};

export default FeaturedEvents;