import React from "react";
import { CalendarIcon, ArrowRight } from "lucide-react";
import { Card, CardContent } from "@/components/ui/card";
import {
  Carousel,
  CarouselContent,
  CarouselItem,
  CarouselPrevious,
  CarouselNext,
} from "@/components/ui/carousel";

interface NewsCardProps {
  title: string;
  date: string;
  description: string;
  imageUrl: string;
}

const NewsCard = ({ title, date, description, imageUrl }: NewsCardProps) => {
  return (
    <Card className="overflow-hidden border-none shadow-md h-full flex flex-col">
      <div className="h-48 w-full overflow-hidden">
        <img
          src={imageUrl}
          alt={title}
          className="h-full w-full object-cover transition-transform hover:scale-105"
        />
      </div>
      <CardContent className="flex-grow flex flex-col p-4">
        <div className="flex items-center text-sm text-gray-500 mb-2">
          <CalendarIcon size={14} className="mr-1" />
          <span>{date}</span>
        </div>
        <h3 className="text-xl font-bold text-navy-blue mb-2">{title}</h3>
        <p className="text-gray-600 mb-4 flex-grow">{description}</p>
        <a
          href="#"
          className="text-medium-blue font-medium flex items-center hover:text-navy-blue transition-colors"
        >
          Read more <ArrowRight size={16} className="ml-1" />
        </a>
      </CardContent>
    </Card>
  );
};

const LatestNews = () => {
  const news = [
    {
      id: 1,
      title: "New Festival Season Announced",
      date: "01/07/2025",
      description:
        "Croatia prepares for an exciting summer of music and entertainment.",
      imageUrl: "/event-images/concert.jpg",
    },
    {
      id: 2,
      title: "Cultural Events Return to Historic Venues",
      date: "28/06/2025",
      description:
        "Historic venues across Croatia reopen for cultural performances.",
      imageUrl: "/event-images/party.jpg",
    },
    {
      id: 3,
      title: "Tech Conference Circuit Expands",
      date: "25/06/2025",
      description:
        "Major tech events announce dates for upcoming Croatian conferences.",
      imageUrl: "/event-images/conference.jpg",
    },
    {
      id: 4,
      title: "Wellness Retreats Growing in Popularity",
      date: "20/06/2025",
      description:
        "Coastal wellness retreats see surge in bookings for summer season.",
      imageUrl: "/event-images/workout.jpg",
    },
    {
      id: 5,
      title: "Business Networking Events Announced",
      date: "18/06/2025",
      description:
        "New business meetups scheduled across major Croatian cities.",
      imageUrl: "/event-images/meetup.jpg",
    },
  ];

  return (
    <section className="mb-12 bg-white rounded-lg shadow-lg p-6 border border-light-blue">
      <h2 className="text-2xl font-bold mb-6 font-sreda text-navy-blue">
        Latest News
      </h2>

      <Carousel
        opts={{
          align: "start",
          loop: true,
        }}
        className="w-full"
      >
        <CarouselContent className="-ml-2 md:-ml-4">
          {news.map((item) => (
            <CarouselItem
              key={item.id}
              className="pl-2 md:pl-4 basis-full sm:basis-1/2 md:basis-1/3 lg:basis-1/3"
            >
              <div className="h-full">
                <NewsCard
                  title={item.title}
                  date={item.date}
                  description={item.description}
                  imageUrl={item.imageUrl}
                />
              </div>
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

export default LatestNews;
