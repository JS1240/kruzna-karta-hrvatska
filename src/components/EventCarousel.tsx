import React, { useEffect, useRef } from 'react';

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
          <div
            key={event.id + '-' + idx}
            className="flex-shrink-0 w-64 mx-4 bg-cream rounded-lg shadow p-4 flex flex-col items-center justify-center"
          >
            <img
              src={event.image}
              alt={event.title}
              className="w-full h-32 object-cover rounded mb-2"
            />
            <div className="font-bold text-lg text-navy-blue mb-1 text-center truncate w-full">{event.title}</div>
            <div className="text-sm text-gray-600 mb-1">{event.date}</div>
            <div className="text-xs text-blue_green-700">{event.location}</div>
          </div>
        ))}
      </div>
    </div>
  );
};

export default EventCarousel;
