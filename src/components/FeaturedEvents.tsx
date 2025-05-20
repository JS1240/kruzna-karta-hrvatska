import React from 'react';
import { CalendarIcon } from 'lucide-react';
import { Card, CardContent } from "@/components/ui/card";
import { ScrollArea } from "@/components/ui/scroll-area";
import { 
  Carousel,
  CarouselContent,
  CarouselItem,
  CarouselPrevious,
  CarouselNext
} from "@/components/ui/carousel";
import { useNavigate } from 'react-router-dom';

const CompactFeaturedEventCard = ({ id, title, image, date, location }: { id: string, title: string, image: string, date: string, location: string }) => {
  const navigate = useNavigate();
  return (
    <div
      className="flex flex-col items-start bg-cream rounded-xl shadow-md hover:shadow-xl transition-shadow cursor-pointer p-3 gap-2 h-full min-h-[180px] border border-light-blue group"
      onClick={() => navigate(`/events/${id}`)}
      tabIndex={0}
      role="button"
      aria-label={`View details for ${title}`}
      onKeyDown={e => { if (e.key === 'Enter' || e.key === ' ') navigate(`/events/${id}`); }}
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
      <div className="font-bold text-base text-navy-blue truncate w-full mb-0.5">{title}</div>
      <div className="flex items-center gap-2 text-xs text-gray-600">
        <CalendarIcon size={14} />
        <span>{date}</span>
      </div>
    </div>
  );
};

const FeaturedEvents = () => {
  const events = [
    {
      id: 1,
      title: "Ultra Europe Festival",
      date: "July 15-17, 2025",
      image: "/event-images/concert.jpg",
      location: "Split"
    },
    {
      id: 2,
      title: "Zagreb Tech Conference",
      date: "September 5-7, 2025",
      image: "/event-images/conference.jpg",
      location: "Zagreb"
    },
    {
      id: 3,
      title: "Adriatic Yoga Retreat",
      date: "August 10-15, 2025",
      image: "/event-images/workout.jpg",
      location: "Adriatic Coast"
    },
    {
      id: 4,
      title: "Split Summer Festival",
      date: "June 20-25, 2025",
      image: "/event-images/party.jpg",
      location: "Split"
    },
    {
      id: 5,
      title: "Dubrovnik Business Forum",
      date: "October 8-10, 2025",
      image: "/event-images/meetup.jpg",
      location: "Dubrovnik"
    }
  ];

  return (
    <section className="mb-12 bg-white rounded-lg shadow-lg p-6 border border-light-blue">
      <h2 className="text-2xl font-bold mb-6 font-sreda text-navy-blue">Featured Events</h2>
      <Carousel
        opts={{
          align: "start",
          loop: true
        }}
        className="w-full"
      >
        <CarouselContent className="-ml-2 md:-ml-4">
          {events.map((event) => (
            <CarouselItem key={event.id} className="pl-2 md:pl-4 basis-full sm:basis-1/2 md:basis-1/4 lg:basis-1/5">
              <CompactFeaturedEventCard 
                id={String(event.id)}
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
    </section>
  );
};

export default FeaturedEvents;
