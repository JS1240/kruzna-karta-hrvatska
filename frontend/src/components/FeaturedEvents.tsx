import React, { useState, useEffect } from "react";
import { CalendarIcon, Loader2 } from "lucide-react";
import { Card, CardContent } from "./ui/card";
import { ScrollArea } from "./ui/scroll-area";
import {
  Carousel,
  CarouselContent,
  CarouselItem,
  CarouselPrevious,
  CarouselNext,
} from "./ui/carousel";
import { useNavigate } from "react-router-dom";
import { eventsApi, Event } from "@/lib/api";
import AnimatedBackground from "./AnimatedBackground";

const CompactFeaturedEventCard = ({
  id,
  title,
  image,
  date,
  location,
}: {
  id: string;
  title: string;
  image: string;
  date: string;
  location: string;
}) => {
  const navigate = useNavigate();
  return (
    <div
      className="flex flex-col items-start bg-cream rounded-xl shadow-md hover:shadow-xl transition-shadow cursor-pointer p-3 gap-2 h-full min-h-[180px] border border-light-blue group"
      onClick={() => navigate(`/events/${id}`)}
      tabIndex={0}
      role="button"
      aria-label={`View details for ${title}`}
      onKeyDown={(e) => {
        if (e.key === "Enter" || e.key === " ") navigate(`/events/${id}`);
      }}
    >
      <div className="relative w-full h-28 rounded-lg overflow-hidden mb-1">
        <img
          src={image}
          alt={title}
          className="w-full h-full object-cover group-hover:scale-105 transition-transform duration-200"
        />
        <span className="absolute top-2 right-2 bg-navy-blue text-white text-xs px-2 py-0.5 rounded shadow font-semibold opacity-90">
          {location}
        </span>
      </div>
      <div className="font-bold text-base text-navy-blue truncate w-full mb-0.5">
        {title}
      </div>
      <div className="flex items-center gap-2 text-xs text-gray-600">
        <CalendarIcon size={14} />
        <span>{date}</span>
      </div>
    </div>
  );
};

interface FeaturedEvent {
  id: string;
  title: string;
  date: string;
  image: string;
  location: string;
}

const FeaturedEvents = () => {
  const [events, setEvents] = useState<FeaturedEvent[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const fetchFeaturedEvents = async () => {
      try {
        setLoading(true);
        setError(null);
        
        // Fetch featured events from API
        const response = await eventsApi.getEvents({ 
          skip: 0, 
          limit: 6,
          featured: true  // Assuming API supports featured flag
        });
        
        // Transform API events to featured event format
        const featuredEvents: FeaturedEvent[] = response.events
          .filter(event => event.image && event.image.trim() !== '') // Only events with images
          .slice(0, 5) // Limit to 5 events
          .map(event => ({
            id: event.id.toString(),
            title: event.title || event.name || 'Untitled Event',
            date: formatEventDate(event.date),
            image: event.image || '/event-images/placeholder.jpg',
            location: event.location || event.city || 'Croatia'
          }));

        // If we don't have enough events, try to get more from regular events
        if (featuredEvents.length < 3) {
          const regularResponse = await eventsApi.getEvents({ 
            skip: 0, 
            limit: 10 
          });
          
          const additionalEvents: FeaturedEvent[] = regularResponse.events
            .filter(event => 
              event.image && 
              event.image.trim() !== '' &&
              !featuredEvents.some(fe => fe.id === event.id.toString())
            )
            .slice(0, 5 - featuredEvents.length)
            .map(event => ({
              id: event.id.toString(),
              title: event.title || event.name || 'Untitled Event',
              date: formatEventDate(event.date),
              image: event.image || '/event-images/placeholder.jpg',
              location: event.location || event.city || 'Croatia'
            }));
          
          featuredEvents.push(...additionalEvents);
        }
        
        setEvents(featuredEvents);
      } catch (err) {
        console.error('Failed to fetch featured events:', err);
        setError('Failed to load featured events');
      } finally {
        setLoading(false);
      }
    };

    fetchFeaturedEvents();
  }, []);

  const formatEventDate = (dateString: string): string => {
    try {
      const date = new Date(dateString);
      return date.toLocaleDateString('en-US', {
        month: 'long',
        day: 'numeric',
        year: 'numeric'
      });
    } catch {
      return dateString;
    }
  };

  // Loading state
  if (loading) {
    return (
      <section className="mb-12 bg-white rounded-lg shadow-lg p-6 border border-light-blue">
        <h2 className="text-2xl font-bold mb-6 font-sreda text-navy-blue">
          Featured Events
        </h2>
        <div className="flex items-center justify-center h-48">
          <div className="flex items-center space-x-2">
            <Loader2 className="h-6 w-6 animate-spin" />
            <span>Loading featured events...</span>
          </div>
        </div>
      </section>
    );
  }

  // Error state
  if (error) {
    return (
      <section className="mb-12 bg-white rounded-lg shadow-lg p-6 border border-light-blue">
        <h2 className="text-2xl font-bold mb-6 font-sreda text-navy-blue">
          Featured Events
        </h2>
        <div className="flex items-center justify-center h-48 text-center">
          <div>
            <p className="text-red-600 mb-4">{error}</p>
            <button 
              onClick={() => window.location.reload()} 
              className="text-blue-600 hover:underline"
            >
              Try again
            </button>
          </div>
        </div>
      </section>
    );
  }

  // Empty state
  if (events.length === 0) {
    return (
      <section className="mb-12 bg-white rounded-lg shadow-lg p-6 border border-light-blue">
        <h2 className="text-2xl font-bold mb-6 font-sreda text-navy-blue">
          Featured Events
        </h2>
        <div className="flex items-center justify-center h-48 text-center">
          <div>
            <p className="text-gray-600 mb-4">No featured events available at the moment.</p>
            <p className="text-sm text-gray-500">Check back later for upcoming events!</p>
          </div>
        </div>
      </section>
    );
  }

  return (
    <section className="mb-12">
      <AnimatedBackground
        blueOnly={true}
        blueIntensity="light"
        gentleMovement={true}
        gentleMode="ultra"
        subtleOpacity={true}
        opacityMode="minimal"
        adjustableBlur={true}
        blurType="edge"
        blurIntensity="light"
        responsive={true}
        overlayMode="light"
        overlayStyle="glass"
        textContrast="auto"
        overlayPadding="p-6"
        className="rounded-lg overflow-hidden shadow-lg border border-light-blue"
      >
          <h2 className="text-2xl font-bold mb-6 font-sreda text-navy-blue">
            Featured Events
          </h2>
      <Carousel
        opts={{
          align: "start",
          loop: true,
        }}
        className="w-full"
      >
        <CarouselContent className="-ml-2 md:-ml-4">
          {events.map((event) => (
            <CarouselItem
              key={event.id}
              className="pl-2 md:pl-4 basis-full sm:basis-1/2 md:basis-1/4 lg:basis-1/5"
            >
              <CompactFeaturedEventCard
                id={event.id}
                title={event.title}
                image={event.image}
                date={event.date}
                location={event.location}
              />
            </CarouselItem>
          ))}
        </CarouselContent>
          <div className="flex justify-end gap-2 mt-4">
            <CarouselPrevious className="static h-8 w-8 translate-y-0" />
            <CarouselNext className="static h-8 w-8 translate-y-0" />
          </div>
        </Carousel>
      </AnimatedBackground>
    </section>
  );
};

export default FeaturedEvents;
