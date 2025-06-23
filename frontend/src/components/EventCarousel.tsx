import React, { useEffect, useRef } from "react";
import EventCard from "./EventCard";
import { preloadImages } from "@/utils/imageUtils";

interface Event {
  id: string;
  title: string;
  image: string;
  date: string;
  location: string;
}

interface EventCarouselProps {
  events: Event[];
  speed?: number; // pixels per second
  loading?: boolean;
  error?: string | null;
}

const EventCarousel: React.FC<EventCarouselProps> = ({
  events,
  speed = 40,
  loading = false,
  error = null,
}) => {
  const containerRef = useRef<HTMLDivElement>(null);
  const contentRef = useRef<HTMLDivElement>(null);

  // Preload images when events change
  useEffect(() => {
    if (events.length > 0) {
      const imageUrls = events.map(event => event.image).filter(Boolean);
      preloadImages(imageUrls).catch(console.warn);
    }
  }, [events]);

  useEffect(() => {
    const container = containerRef.current;
    const content = contentRef.current;
    if (!container || !content || loading || events.length === 0) return;

    let animationFrame: number;
    let start: number | null = null;
    let translateX = 0;
    const contentWidth = content.scrollWidth;

    function animate(ts: number) {
      if (start === null) start = ts;
      const elapsed = ts - start;
      translateX = -((elapsed / 1000) * speed) % contentWidth;
      content.style.transform = `translateX(${translateX}px)`;
      animationFrame = requestAnimationFrame(animate);
    }
    animationFrame = requestAnimationFrame(animate);
    return () => cancelAnimationFrame(animationFrame);
  }, [events, speed, loading]);

  // Duplicate events for seamless loop
  const allEvents = [...events, ...events];

  // Loading skeleton
  if (loading) {
    return (
      <div className="relative w-full overflow-hidden h-64 bg-white rounded-lg shadow-xl border border-gray-200">
        <div className="flex items-center h-full space-x-4 px-4">
          {Array.from({ length: 3 }).map((_, idx) => (
            <div key={idx} className="flex-shrink-0 w-48 h-48 bg-gray-200 rounded-lg animate-pulse">
              <div className="h-32 bg-gray-300 rounded-t-lg"></div>
              <div className="p-3 space-y-2">
                <div className="h-4 bg-gray-300 rounded w-3/4"></div>
                <div className="h-3 bg-gray-300 rounded w-1/2"></div>
                <div className="h-3 bg-gray-300 rounded w-2/3"></div>
              </div>
            </div>
          ))}
        </div>
      </div>
    );
  }

  // Error state
  if (error) {
    return (
      <div className="relative w-full overflow-hidden h-64 bg-white rounded-lg shadow-xl border border-gray-200">
        <div className="flex items-center justify-center h-full">
          <div className="text-center p-6">
            <div className="text-red-500 mb-2">
              <svg className="w-12 h-12 mx-auto" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-2.5L13.732 4c-.77-.833-1.732-.833-2.5 0L4.268 18.5c-.77.833.192 2.5 1.732 2.5z" />
              </svg>
            </div>
            <h3 className="text-lg font-medium text-gray-900 mb-1">Unable to load events</h3>
            <p className="text-gray-600 text-sm">Please try again later</p>
          </div>
        </div>
      </div>
    );
  }

  // Empty state
  if (events.length === 0) {
    return (
      <div className="relative w-full overflow-hidden h-64 bg-white rounded-lg shadow-xl border border-gray-200">
        <div className="flex items-center justify-center h-full">
          <div className="text-center p-6">
            <div className="text-gray-400 mb-2">
              <svg className="w-12 h-12 mx-auto" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 7V3m8 4V3m-9 8h10M5 21h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v12a2 2 0 002 2z" />
              </svg>
            </div>
            <h3 className="text-lg font-medium text-gray-900 mb-1">No events available</h3>
            <p className="text-gray-600 text-sm">Check back later for upcoming events</p>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div
      ref={containerRef}
      className="relative w-full overflow-hidden h-64 bg-white rounded-lg shadow-xl border border-gray-200"
    >
      <div
        ref={contentRef}
        className="flex items-center h-full transition-transform duration-0"
        style={{ willChange: "transform" }}
      >
        {allEvents.map((event, idx) => (
          <EventCard
            key={event.id + "-" + idx}
            id={event.id}
            title={event.title}
            image={event.image}
            date={event.date}
            location={event.location}
          />
        ))}
      </div>
    </div>
  );
};

export default EventCarousel;
