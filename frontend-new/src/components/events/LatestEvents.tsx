import React from 'react';
import { Clock, ChevronRight, ChevronLeft } from 'lucide-react';
import { useEvents } from '@/hooks/useEvents';
import { Event } from '@/types/event';
import { EventCard } from './EventCard';
import clsx from 'clsx';

interface LatestEventsProps {
  onEventClick?: (event: Event) => void;
  className?: string;
  maxEvents?: number;
  showPagination?: boolean;
}

const LatestEventSkeleton: React.FC = () => (
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

export const LatestEvents: React.FC<LatestEventsProps> = ({
  onEventClick,
  className,
  maxEvents = 8,
  showPagination = false,
}) => {
  const [currentPage, setCurrentPage] = React.useState(1);
  const pageSize = maxEvents;

  const { data: eventsResponse, isLoading, error } = useEvents({
    page: currentPage,
    size: pageSize,
    event_status: 'active',
  });

  const handlePreviousPage = () => {
    setCurrentPage(prev => Math.max(1, prev - 1));
  };

  const handleNextPage = () => {
    if (eventsResponse && currentPage < eventsResponse.pages) {
      setCurrentPage(prev => prev + 1);
    }
  };

  if (error) {
    return (
      <div className={clsx('container py-8', className)}>
        <div className="text-center py-12">
          <div className="text-red-500 text-lg font-medium mb-2">
            Failed to load latest events
          </div>
          <p className="text-gray-600">
            Please try again later or contact support if the problem persists.
          </p>
        </div>
      </div>
    );
  }

  const events = eventsResponse?.events || [];
  const totalPages = eventsResponse?.pages || 0;
  const hasNextPage = currentPage < totalPages;
  const hasPreviousPage = currentPage > 1;

  return (
    <section className={clsx('container py-12', className)}>
      <div className="mb-8">
        <div className="flex items-center justify-between">
          <div>
            <div className="flex items-center gap-2 mb-2">
              <Clock className="w-6 h-6 text-primary-500" />
              <h2 className="text-3xl font-bold text-gray-900">Latest Events</h2>
            </div>
            <p className="text-gray-600">
              Recently added events you might be interested in
            </p>
          </div>
          
          {showPagination && eventsResponse && (
            <div className="flex items-center gap-2">
              <button
                onClick={handlePreviousPage}
                disabled={!hasPreviousPage}
                className={clsx(
                  'p-2 rounded-lg border transition-colors',
                  hasPreviousPage
                    ? 'border-gray-300 hover:bg-gray-50 text-gray-700'
                    : 'border-gray-200 text-gray-400 cursor-not-allowed'
                )}
              >
                <ChevronLeft className="w-5 h-5" />
              </button>
              
              <span className="text-sm text-gray-600 px-2">
                Page {currentPage} of {totalPages}
              </span>
              
              <button
                onClick={handleNextPage}
                disabled={!hasNextPage}
                className={clsx(
                  'p-2 rounded-lg border transition-colors',
                  hasNextPage
                    ? 'border-gray-300 hover:bg-gray-50 text-gray-700'
                    : 'border-gray-200 text-gray-400 cursor-not-allowed'
                )}
              >
                <ChevronRight className="w-5 h-5" />
              </button>
            </div>
          )}
        </div>
      </div>

      {isLoading ? (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-6">
          {Array.from({ length: pageSize }).map((_, i) => (
            <LatestEventSkeleton key={i} />
          ))}
        </div>
      ) : events.length === 0 ? (
        <div className="text-center py-12">
          <Clock className="w-12 h-12 text-gray-400 mx-auto mb-4" />
          <h3 className="text-xl font-medium text-gray-900 mb-2">
            No Events Found
          </h3>
          <p className="text-gray-600">
            Check back later for new events in your area.
          </p>
        </div>
      ) : (
        <>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-6">
            {events.map((event) => (
              <EventCard
                key={event.id}
                event={event}
                onClick={onEventClick}
                variant="default"
                showViewCount={true}
              />
            ))}
          </div>

          {/* Mobile pagination */}
          {showPagination && eventsResponse && totalPages > 1 && (
            <div className="flex items-center justify-center gap-4 mt-8 lg:hidden">
              <button
                onClick={handlePreviousPage}
                disabled={!hasPreviousPage}
                className={clsx(
                  'flex items-center gap-2 px-4 py-2 rounded-lg border transition-colors',
                  hasPreviousPage
                    ? 'border-gray-300 hover:bg-gray-50 text-gray-700'
                    : 'border-gray-200 text-gray-400 cursor-not-allowed'
                )}
              >
                <ChevronLeft className="w-4 h-4" />
                Previous
              </button>
              
              <span className="text-sm text-gray-600 px-2">
                {currentPage} / {totalPages}
              </span>
              
              <button
                onClick={handleNextPage}
                disabled={!hasNextPage}
                className={clsx(
                  'flex items-center gap-2 px-4 py-2 rounded-lg border transition-colors',
                  hasNextPage
                    ? 'border-gray-300 hover:bg-gray-50 text-gray-700'
                    : 'border-gray-200 text-gray-400 cursor-not-allowed'
                )}
              >
                Next
                <ChevronRight className="w-4 h-4" />
              </button>
            </div>
          )}

          {/* Show total events count */}
          {eventsResponse && (
            <div className="text-center mt-6 text-sm text-gray-500">
              Showing {events.length} of {eventsResponse.total} events
            </div>
          )}
        </>
      )}
    </section>
  );
};

export default LatestEvents;