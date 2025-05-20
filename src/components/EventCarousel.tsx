import React, { useEffect, useRef } from 'react';
import EventCard from './EventCard';

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
}

const EventCarousel: React.FC<EventCarouselProps> = ({ events, speed = 40 }) => {
  const containerRef = useRef<HTMLDivElement>(null);
  const contentRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const container = containerRef.current;
    const content = contentRef.current;
    if (!container || !content) return;

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
  }, [events, speed]);

  // Duplicate events for seamless loop
  const allEvents = [...events, ...events];

  return (
    <div
      ref={containerRef}
      className="relative w-full overflow-hidden h-64 bg-white rounded-lg shadow-xl border border-gray-200"
    >
      <div
        ref={contentRef}
        className="flex items-center h-full transition-transform duration-0"
        style={{ willChange: 'transform' }}
      >
        {allEvents.map((event, idx) => (
          <EventCard
            key={event.id + '-' + idx}
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
