
import React, { useState, useEffect } from 'react';
import { motion } from 'framer-motion';
import { Calendar, Clock, MapPin, Filter, Star, Bell } from 'lucide-react';
import Header from '@/components/Header';
import Footer from '@/components/Footer';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import {
  Tooltip,
  TooltipContent,
  TooltipProvider,
  TooltipTrigger,
} from "@/components/ui/tooltip";
import { Skeleton } from '@/components/ui/skeleton';
import { Badge } from '@/components/ui/badge';
import { toast } from 'sonner';

// Event categories for filtering
const categories = [
  { id: 'all', name: 'All Events' },
  { id: 'music', name: 'Music' },
  { id: 'art', name: 'Art & Culture' },
  { id: 'food', name: 'Food & Drink' },
  { id: 'tech', name: 'Tech' },
  { id: 'sports', name: 'Sports' },
];

// Time periods for the tab navigation
const timePeriods = [
  { id: 'today', name: 'Today' },
  { id: 'week', name: 'This Week' },
  { id: 'month', name: 'This Month' },
  { id: 'summer', name: 'Summer' },
];

// Mock data for upcoming events
const upcomingEvents = [
  {
    id: 1,
    title: 'Ultra Europe Music Festival',
    date: 'July 11-13, 2025',
    time: '4:00 PM - 2:00 AM',
    location: 'Split',
    category: 'music',
    image: '/event-images/concert.jpg',
    featured: true,
    rating: 4.8,
    period: 'summer',
  },
  {
    id: 2,
    title: 'Croatian Wine Festival',
    date: 'June 5, 2025',
    time: '12:00 PM - 8:00 PM',
    location: 'Zagreb',
    category: 'food',
    image: '/event-images/party.jpg',
    featured: false,
    rating: 4.5,
    period: 'month',
  },
  {
    id: 3,
    title: 'Tech Startup Conference',
    date: 'May 25, 2025',
    time: '9:00 AM - 5:00 PM',
    location: 'Zagreb',
    category: 'tech',
    image: '/event-images/conference.jpg',
    featured: true,
    rating: 4.2,
    period: 'week',
  },
  {
    id: 4,
    title: 'Dalmatian Cultural Festival',
    date: 'May 21, 2025',
    time: '10:00 AM - 10:00 PM',
    location: 'Zadar',
    category: 'art',
    image: '/event-images/meetup.jpg',
    featured: false,
    rating: 4.0,
    period: 'today',
  },
  {
    id: 5,
    title: 'Adriatic Yoga Retreat',
    date: 'August 15-20, 2025',
    time: 'All Day',
    location: 'Hvar',
    category: 'sports',
    image: '/event-images/workout.jpg',
    featured: true,
    rating: 4.9,
    period: 'summer',
  },
  {
    id: 6,
    title: 'Zagreb Art Exhibition',
    date: 'May 21, 2025',
    time: '11:00 AM - 7:00 PM',
    location: 'Zagreb',
    category: 'art',
    image: '/event-images/conference.jpg',
    featured: false,
    rating: 4.1,
    period: 'today',
  },
  {
    id: 7,
    title: 'Croatian Food Fair',
    date: 'May 25, 2025',
    time: '12:00 PM - 9:00 PM',
    location: 'Split',
    category: 'food',
    image: '/event-images/party.jpg',
    featured: false,
    rating: 4.3,
    period: 'week',
  },
  {
    id: 8,
    title: 'Dubrovnik Summer Festival',
    date: 'July 10 - August 25, 2025',
    time: 'Various Times',
    location: 'Dubrovnik',
    category: 'art',
    image: '/event-images/concert.jpg',
    featured: true,
    rating: 4.7,
    period: 'summer',
  }
];

interface EventCardProps {
  event: typeof upcomingEvents[0];
  isAnimated?: boolean;
}

// Component for each individual event card
const EventCard: React.FC<EventCardProps> = ({ event, isAnimated = true }) => {
  const [isReminding, setIsReminding] = useState(false);

  const handleRemindMe = (e: React.MouseEvent) => {
    e.stopPropagation();
    setIsReminding(true);
    
    // Simulate sending a reminder (would connect to backend in real app)
    setTimeout(() => {
      toast.success("We'll remind you about this event!", {
        description: `You will receive a notification before "${event.title}"`,
        duration: 3000,
      });
      setIsReminding(false);
    }, 800);
  };

  const cardVariants = {
    hidden: { opacity: 0, y: 20 },
    visible: { opacity: 1, y: 0, transition: { duration: 0.5 } },
    hover: { 
      y: -10, 
      boxShadow: '0 20px 25px -5px rgba(0, 0, 0, 0.1), 0 10px 10px -5px rgba(0, 0, 0, 0.04)',
      transition: { type: 'spring', stiffness: 300 }
    }
  };

  const MotionWrapper = isAnimated ? motion.div : React.Fragment;
  const motionProps = isAnimated ? {
    variants: cardVariants,
    initial: "hidden",
    animate: "visible",
    whileHover: "hover"
  } : {};
  
  return (
    <MotionWrapper {...motionProps}>
      <div className="bg-white rounded-xl overflow-hidden shadow-lg h-full flex flex-col transition-all duration-300 cursor-pointer">
        <div className="relative h-48 overflow-hidden">
          <img 
            src={event.image} 
            alt={event.title}
            className="w-full h-full object-cover transition-transform duration-500 hover:scale-110" 
          />
          <div className="absolute top-2 right-2">
            <Badge variant="secondary" className="bg-white/80 text-navy-blue font-medium">
              <Star className="w-3 h-3 mr-1 fill-yellow-400 stroke-yellow-400" />
              {event.rating}
            </Badge>
          </div>
          {event.featured && (
            <div className="absolute top-2 left-2">
              <Badge variant="secondary" className="bg-navy-blue text-white font-medium">
                Featured
              </Badge>
            </div>
          )}
        </div>
        
        <div className="p-4 flex-grow flex flex-col">
          <div className="flex flex-col gap-1 mb-2">
            <h3 className="text-lg font-semibold text-navy-blue line-clamp-1">{event.title}</h3>
            <div className="flex items-center text-sm text-gray-600">
              <Calendar size={14} className="mr-1" />
              {event.date}
            </div>
            <div className="flex items-center text-sm text-gray-600">
              <Clock size={14} className="mr-1" />
              {event.time}
            </div>
            <div className="flex items-center text-sm text-gray-600">
              <MapPin size={14} className="mr-1" />
              {event.location}
            </div>
          </div>
          
          <div className="flex justify-between items-center mt-auto pt-3">
            <Badge className="bg-light-blue text-navy-blue hover:bg-medium-blue hover:text-white">
              {categories.find(cat => cat.id === event.category)?.name || event.category}
            </Badge>
            <TooltipProvider>
              <Tooltip>
                <TooltipTrigger asChild>
                  <Button 
                    size="icon" 
                    variant="ghost" 
                    className="rounded-full" 
                    onClick={handleRemindMe}
                    disabled={isReminding}
                  >
                    {isReminding ? (
                      <Skeleton className="h-5 w-5 rounded-full" />
                    ) : (
                      <Bell className="h-5 w-5" />
                    )}
                  </Button>
                </TooltipTrigger>
                <TooltipContent>
                  <p>Remind me</p>
                </TooltipContent>
              </Tooltip>
            </TooltipProvider>
          </div>
        </div>
      </div>
    </MotionWrapper>
  );
};

// The main Upcoming page component
const Upcoming = () => {
  const [searchQuery, setSearchQuery] = useState('');
  const [selectedCategory, setSelectedCategory] = useState('all');
  const [activeTab, setActiveTab] = useState('today');
  const [loading, setLoading] = useState(true);
  const [events, setEvents] = useState<typeof upcomingEvents>([]);

  // Simulate loading events from an API
  useEffect(() => {
    setLoading(true);
    
    // Simulate network request delay
    const timer = setTimeout(() => {
      // Filter events based on selected tab (time period)
      const filteredEvents = upcomingEvents.filter(event => {
        return activeTab === 'all' || event.period === activeTab;
      });
      
      setEvents(filteredEvents);
      setLoading(false);
    }, 800);
    
    return () => clearTimeout(timer);
  }, [activeTab]);
  
  // Filter events based on search query and selected category
  const filteredEvents = events.filter(event => {
    const matchesSearch = event.title.toLowerCase().includes(searchQuery.toLowerCase()) || 
                         event.location.toLowerCase().includes(searchQuery.toLowerCase());
    const matchesCategory = selectedCategory === 'all' || event.category === selectedCategory;
    
    return matchesSearch && matchesCategory;
  });
  
  const handleCategoryChange = (category: string) => {
    setSelectedCategory(category);
  };
  
  return (
    <div className="min-h-screen flex flex-col bg-cream">
      <Header />
      
      <main className="flex-grow container mx-auto px-4 py-8">
        <div className="bg-white rounded-lg shadow-lg p-6 border border-light-blue">
          <div className="flex flex-col gap-6">
            {/* Page title */}
            <div className="text-center mb-2">
              <h1 className="text-3xl md:text-4xl font-bold text-navy-blue mb-2">Upcoming Events</h1>
              <p className="text-medium-blue text-lg">Discover exciting events happening across Croatia</p>
            </div>
            
            {/* Search and filter section */}
            <div className="flex flex-col md:flex-row gap-4">
              <div className="flex-grow">
                <Input
                  placeholder="Search events by name or location..."
                  value={searchQuery}
                  onChange={(e) => setSearchQuery(e.target.value)}
                  className="w-full"
                />
              </div>
              <div className="flex overflow-x-auto pb-2 gap-2 md:pb-0 no-scrollbar">
                {categories.map((category) => (
                  <Button
                    key={category.id}
                    variant={selectedCategory === category.id ? "default" : "outline"}
                    className="whitespace-nowrap"
                    onClick={() => handleCategoryChange(category.id)}
                  >
                    {category.name}
                  </Button>
                ))}
              </div>
            </div>
            
            {/* Time period tabs */}
            <Tabs value={activeTab} onValueChange={setActiveTab} className="w-full">
              <TabsList className="w-full justify-start overflow-x-auto">
                {timePeriods.map((period) => (
                  <TabsTrigger key={period.id} value={period.id} className="flex-1">
                    {period.name}
                  </TabsTrigger>
                ))}
              </TabsList>
              
              {/* Events grid for each time period */}
              {timePeriods.map((period) => (
                <TabsContent key={period.id} value={period.id} className="mt-6">
                  {loading ? (
                    // Skeleton loading state
                    <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-6">
                      {[1, 2, 3, 4, 5, 6].map((i) => (
                        <div key={i} className="bg-white rounded-xl overflow-hidden shadow h-[350px]">
                          <Skeleton className="h-48 w-full" />
                          <div className="p-4">
                            <Skeleton className="h-6 w-3/4 mb-4" />
                            <Skeleton className="h-4 w-full mb-2" />
                            <Skeleton className="h-4 w-2/3 mb-2" />
                            <Skeleton className="h-4 w-1/2" />
                          </div>
                        </div>
                      ))}
                    </div>
                  ) : filteredEvents.length > 0 ? (
                    <motion.div 
                      className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-6"
                      initial="hidden"
                      animate="visible"
                      variants={{
                        visible: {
                          transition: {
                            staggerChildren: 0.1,
                          }
                        }
                      }}
                    >
                      {filteredEvents.map((event) => (
                        <EventCard key={event.id} event={event} />
                      ))}
                    </motion.div>
                  ) : (
                    // No events found message
                    <motion.div 
                      className="text-center py-12"
                      initial={{ opacity: 0 }}
                      animate={{ opacity: 1 }}
                    >
                      <div className="text-6xl mb-4">🔍</div>
                      <h3 className="text-xl font-medium text-navy-blue mb-2">No events found</h3>
                      <p className="text-medium-blue">
                        Try adjusting your search or filters to find events
                      </p>
                    </motion.div>
                  )}
                </TabsContent>
              ))}
            </Tabs>
          </div>
        </div>
      </main>
      
      <Footer />
    </div>
  );
};

export default Upcoming;
