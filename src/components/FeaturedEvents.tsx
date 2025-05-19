
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

interface EventCardProps {
  title: string;
  date: string;
  imageUrl: string;
}

const EventCard = ({ title, date, imageUrl }: EventCardProps) => {
  return (
    <Card className="overflow-hidden border-none shadow-md">
      <div className="relative h-48 w-full overflow-hidden">
        <img 
          src={imageUrl} 
          alt={title} 
          className="h-full w-full object-cover transition-transform hover:scale-105"
        />
        <div className="absolute inset-0 bg-gradient-to-t from-black/70 to-transparent flex flex-col justify-end p-4">
          <h3 className="text-xl font-bold text-white">{title}</h3>
          <div className="flex items-center gap-2 text-white/90 text-sm mt-1">
            <CalendarIcon size={14} />
            <span>{date}</span>
          </div>
        </div>
      </div>
    </Card>
  );
};

const FeaturedEvents = () => {
  const events = [
    {
      id: 1,
      title: "Ultra Europe Festival",
      date: "July 15-17, 2025",
      imageUrl: "/event-images/concert.jpg"
    },
    {
      id: 2,
      title: "Zagreb Tech Conference",
      date: "September 5-7, 2025",
      imageUrl: "/event-images/conference.jpg"
    },
    {
      id: 3,
      title: "Adriatic Yoga Retreat",
      date: "August 10-15, 2025",
      imageUrl: "/event-images/workout.jpg"
    },
    {
      id: 4,
      title: "Split Summer Festival",
      date: "June 20-25, 2025",
      imageUrl: "/event-images/party.jpg"
    },
    {
      id: 5,
      title: "Dubrovnik Business Forum",
      date: "October 8-10, 2025",
      imageUrl: "/event-images/meetup.jpg"
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
            <CarouselItem key={event.id} className="pl-2 md:pl-4 basis-full sm:basis-1/2 md:basis-1/3 lg:basis-1/3">
              <EventCard 
                title={event.title} 
                date={event.date} 
                imageUrl={event.imageUrl} 
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
