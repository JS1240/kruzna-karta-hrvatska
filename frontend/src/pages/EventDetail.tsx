import React, { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { 
  Calendar, 
  MapPin, 
  Clock, 
  Users, 
  Heart,
  Share2,
  Star,
  Euro,
  ArrowLeft,
  Ticket,
  CheckCircle,
  AlertCircle,
  RefreshCw
} from 'lucide-react';
import { formatDistanceToNow } from 'date-fns';
import Header from '@/components/Header';
import Footer from '@/components/Footer';
import PageTransition from '@/components/PageTransition';
import TicketSelection from '@/components/TicketSelection';
import BookingCheckout from '@/components/BookingCheckout';
import EventReviews from '@/components/EventReviews';
import { getCurrentUser } from '@/lib/auth';
import { toast } from '@/hooks/use-toast';
import { eventsApi } from '@/lib/api';

interface TicketType {
  id: string;
  name: string;
  description: string;
  price: number;
  currency: string;
  total_quantity: number;
  available_quantity: number;
  min_purchase: number;
  max_purchase: number;
  sale_start_date?: string;
  sale_end_date?: string;
}

interface Event {
  id: string;
  title: string;
  description: string;
  date: string;
  time: string;
  location: string;
  venue: string;
  category: string;
  image?: string;
  organizer: {
    id: string;
    name: string;
    avatar?: string;
    verified: boolean;
  };
  ticketTypes: TicketType[];
  totalCapacity: number;
  soldTickets: number;
  rating: number;
  reviewCount: number;
  tags: string[];
  latitude?: number;
  longitude?: number;
  isLiked: boolean;
  isSaved: boolean;
  created_at: string;
  updated_at: string;
}

// Helper function to transform API event data to local Event interface
const transformApiEvent = (apiEvent: any): Event => {
  return {
    id: apiEvent.id?.toString() || '',
    title: apiEvent.title || apiEvent.name || 'Untitled Event',
    description: apiEvent.description || 'No description available.',
    date: apiEvent.date || new Date().toISOString().split('T')[0],
    time: apiEvent.time || '00:00',
    location: apiEvent.location || apiEvent.city || 'Croatia',
    venue: apiEvent.venue || apiEvent.location || 'TBA',
    category: apiEvent.category || 'Other',
    image: apiEvent.image || '/event-images/placeholder.jpg',
    organizer: {
      id: apiEvent.organizer?.id || 'unknown',
      name: apiEvent.organizer?.name || 'Event Organizer',
      avatar: apiEvent.organizer?.avatar || '',
      verified: apiEvent.organizer?.verified || false,
    },
    ticketTypes: apiEvent.ticket_types || [],
    totalCapacity: apiEvent.total_capacity || 0,
    soldTickets: apiEvent.sold_tickets || 0,
    rating: apiEvent.rating || 0,
    reviewCount: apiEvent.review_count || 0,
    tags: apiEvent.tags || [],
    latitude: apiEvent.latitude,
    longitude: apiEvent.longitude,
    isLiked: false, // Will be determined by user data
    isSaved: false, // Will be determined by user data
    created_at: apiEvent.created_at || new Date().toISOString(),
    updated_at: apiEvent.updated_at || new Date().toISOString(),
  };
};

const EventDetail: React.FC = () => {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const [event, setEvent] = useState<Event | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [selectedTab, setSelectedTab] = useState('overview');
  const [showBooking, setShowBooking] = useState(false);
  const [selectedTickets, setSelectedTickets] = useState<Array<{ ticketType: TicketType; quantity: number }>>([]);
  
  const user = getCurrentUser();

  useEffect(() => {
    const fetchEvent = async () => {
      if (!id) {
        setError('Event ID not provided');
        setLoading(false);
        return;
      }

      try {
        setLoading(true);
        setError(null);
        
        // Fetch event details from API
        const apiEvent = await eventsApi.getEvent(parseInt(id));
        
        if (!apiEvent) {
          setError('Event not found');
          setEvent(null);
          return;
        }
        
        // Transform API event to local format
        const transformedEvent = transformApiEvent(apiEvent);
        
        // TODO: Fetch user's interaction data (likes, saves) if user is logged in
        if (user) {
          try {
            // This would be actual API calls to check user's relationship with event
            // const userInteractions = await eventsApi.getUserEventInteractions(user.id, transformedEvent.id);
            // transformedEvent.isLiked = userInteractions.isLiked;
            // transformedEvent.isSaved = userInteractions.isSaved;
          } catch (interactionError) {
            // Non-critical error, just log it
            console.warn('Failed to fetch user interactions:', interactionError);
          }
        }
        
        setEvent(transformedEvent);
        
      } catch (err) {
        console.error('Failed to fetch event:', err);
        setError('Failed to load event details');
        setEvent(null);
      } finally {
        setLoading(false);
      }
    };

    fetchEvent();
  }, [id, user]);

  const handleLike = () => {
    if (!user) {
      toast({
        title: "Please log in",
        description: "You need to be logged in to like events",
        variant: "destructive",
      });
      return;
    }

    setEvent(prev => prev ? { ...prev, isLiked: !prev.isLiked } : null);
    toast({
      title: event?.isLiked ? "Removed from favorites" : "Added to favorites",
      description: event?.isLiked ? "Event removed from your favorites" : "Event added to your favorites",
    });
  };

  const handleShare = () => {
    if (navigator.share) {
      navigator.share({
        title: event?.title,
        text: event?.description,
        url: window.location.href,
      });
    } else {
      navigator.clipboard.writeText(window.location.href);
      toast({
        title: "Link copied",
        description: "Event link has been copied to clipboard",
      });
    }
  };

  const handleBookNow = () => {
    if (!user) {
      toast({
        title: "Please log in",
        description: "You need to be logged in to book tickets",
        variant: "destructive",
      });
      return;
    }
    setSelectedTab('tickets');
  };

  const handleStartBooking = (tickets: Array<{ ticketType: TicketType; quantity: number }>) => {
    setSelectedTickets(tickets);
    setShowBooking(true);
  };

  const handleBookingComplete = (bookingReference: string) => {
    setShowBooking(false);
    setSelectedTickets([]);
    
    // Navigate to a booking confirmation page or show success message
    toast({
      title: "Booking successful!",
      description: `Your booking reference is ${bookingReference}. Check your email for tickets.`,
    });
  };

  if (loading) {
    return (
      <PageTransition>
        <div className="min-h-screen flex flex-col bg-cream">
          <Header />
          <main className="flex-grow container mx-auto px-4 py-8">
            <div className="animate-pulse space-y-6">
              <div className="h-8 bg-gray-200 rounded w-1/4"></div>
              <div className="h-64 bg-gray-200 rounded"></div>
              <div className="space-y-3">
                <div className="h-4 bg-gray-200 rounded"></div>
                <div className="h-4 bg-gray-200 rounded w-5/6"></div>
                <div className="h-4 bg-gray-200 rounded w-4/6"></div>
              </div>
            </div>
          </main>
          <Footer />
        </div>
      </PageTransition>
    );
  }

  // Error state
  if (error || (!loading && !event)) {
    return (
      <PageTransition>
        <div className="min-h-screen flex flex-col bg-cream">
          <Header />
          <main className="flex-grow container mx-auto px-4 py-8 text-center">
            <AlertCircle className="h-16 w-16 mx-auto text-gray-400 mb-4" />
            <h2 className="text-2xl font-bold text-gray-900 mb-2">
              {error || 'Event not found'}
            </h2>
            <p className="text-gray-600 mb-6">
              {error ? 'Please try again later or check your connection.' : 'The event you\'re looking for doesn\'t exist.'}
            </p>
            <div className="space-x-4">
              <Button onClick={() => navigate('/')}>
                <ArrowLeft className="h-4 w-4 mr-2" />
                Back to Events
              </Button>
              {error && (
                <Button variant="outline" onClick={() => window.location.reload()}>
                  <RefreshCw className="h-4 w-4 mr-2" />
                  Retry
                </Button>
              )}
            </div>
          </main>
          <Footer />
        </div>
      </PageTransition>
    );
  }

  // Still loading or no event data
  if (!event) {
    return (
      <PageTransition>
        <div className="min-h-screen flex flex-col bg-cream">
          <Header />
          <main className="flex-grow container mx-auto px-4 py-8 text-center">
            <div className="flex items-center justify-center">
              <div className="text-center">
                <div className="animate-spin rounded-full h-16 w-16 border-b-2 border-navy-blue mx-auto mb-4"></div>
                <p className="text-gray-600">Loading event details...</p>
              </div>
            </div>
          </main>
          <Footer />
        </div>
      </PageTransition>
    );
  }

  const eventDate = new Date(event.date + 'T' + event.time);
  const availabilityPercentage = ((event.totalCapacity - event.soldTickets) / event.totalCapacity) * 100;

  return (
    <PageTransition>
      <div className="min-h-screen flex flex-col bg-cream">
        <Header />
        
        <main className="flex-grow container mx-auto px-4 py-8">
          {/* Back Button */}
          <Button 
            variant="ghost" 
            onClick={() => navigate(-1)}
            className="mb-6"
          >
            <ArrowLeft className="h-4 w-4 mr-2" />
            Back
          </Button>

          <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
            {/* Main Content */}
            <div className="lg:col-span-2 space-y-6">
              {/* Hero Section */}
              <Card className="overflow-hidden">
                <div className="relative">
                  {event.image && (
                    <img 
                      src={event.image} 
                      alt={event.title}
                      className="w-full h-64 sm:h-80 object-cover"
                    />
                  )}
                  <div className="absolute inset-0 bg-gradient-to-t from-black/60 to-transparent" />
                  <div className="absolute bottom-4 left-4 right-4 text-white">
                    <div className="flex items-center gap-2 mb-2">
                      <Badge variant="secondary" className="bg-white/20 text-white border-0 shadow-sm backdrop-blur-sm">
                        {event.category}
                      </Badge>
                      {event.organizer.verified && (
                        <CheckCircle className="h-4 w-4 text-blue-400" />
                      )}
                    </div>
                    <h1 className="text-2xl sm:text-3xl font-bold mb-2">{event.title}</h1>
                    <div className="flex items-center gap-4 text-sm">
                      <div className="flex items-center gap-1">
                        <Calendar className="h-4 w-4" />
                        {eventDate.toLocaleDateString()}
                      </div>
                      <div className="flex items-center gap-1">
                        <Clock className="h-4 w-4" />
                        {event.time}
                      </div>
                      <div className="flex items-center gap-1">
                        <MapPin className="h-4 w-4" />
                        {event.location}
                      </div>
                    </div>
                  </div>
                </div>
              </Card>

              {/* Event Details */}
              <Tabs value={selectedTab} onValueChange={setSelectedTab}>
                <TabsList className="grid w-full grid-cols-3">
                  <TabsTrigger value="overview">Overview</TabsTrigger>
                  <TabsTrigger value="tickets">Tickets</TabsTrigger>
                  <TabsTrigger value="reviews">Reviews</TabsTrigger>
                </TabsList>

                <TabsContent value="overview" className="space-y-6">
                  <Card>
                    <CardHeader>
                      <CardTitle>About This Event</CardTitle>
                    </CardHeader>
                    <CardContent>
                      <p className="text-gray-700 leading-relaxed">{event.description}</p>
                      
                      <div className="mt-6 grid grid-cols-1 sm:grid-cols-2 gap-4">
                        <div>
                          <h4 className="font-medium text-gray-900 mb-2">Event Details</h4>
                          <div className="space-y-2 text-sm text-gray-600">
                            <div className="flex items-center gap-2">
                              <Calendar className="h-4 w-4" />
                              {eventDate.toLocaleDateString('en-US', { 
                                weekday: 'long', 
                                year: 'numeric', 
                                month: 'long', 
                                day: 'numeric' 
                              })}
                            </div>
                            <div className="flex items-center gap-2">
                              <Clock className="h-4 w-4" />
                              {event.time}
                            </div>
                            <div className="flex items-center gap-2">
                              <MapPin className="h-4 w-4" />
                              {event.venue}, {event.location}
                            </div>
                            <div className="flex items-center gap-2">
                              <Users className="h-4 w-4" />
                              {event.soldTickets} / {event.totalCapacity} attending
                            </div>
                          </div>
                        </div>
                        
                        <div>
                          <h4 className="font-medium text-gray-900 mb-2">Organizer</h4>
                          <div className="flex items-center gap-3">
                            <div className="h-10 w-10 bg-navy-blue rounded-full flex items-center justify-center text-white font-bold">
                              {event.organizer.name.charAt(0)}
                            </div>
                            <div>
                              <div className="flex items-center gap-2">
                                <span className="font-medium">{event.organizer.name}</span>
                                {event.organizer.verified && (
                                  <CheckCircle className="h-4 w-4 text-blue-500" />
                                )}
                              </div>
                              <span className="text-sm text-gray-600">Event Organizer</span>
                            </div>
                          </div>
                        </div>
                      </div>

                      {event.tags.length > 0 && (
                        <div className="mt-6">
                          <h4 className="font-medium text-gray-900 mb-2">Tags</h4>
                          <div className="flex flex-wrap gap-2">
                            {event.tags.map((tag) => (
                              <Badge key={tag} variant="outline">
                                #{tag}
                              </Badge>
                            ))}
                          </div>
                        </div>
                      )}
                    </CardContent>
                  </Card>
                </TabsContent>

                <TabsContent value="tickets">
                  <TicketSelection 
                    event={event}
                    onBookingStart={handleStartBooking}
                  />
                </TabsContent>

                <TabsContent value="reviews">
                  <EventReviews eventId={event.id} />
                </TabsContent>
              </Tabs>
            </div>

            {/* Sidebar */}
            <div className="space-y-6">
              {/* Booking Card */}
              <Card className="sticky top-24">
                <CardHeader>
                  <div className="flex items-center justify-between">
                    <CardTitle className="text-lg">Book Tickets</CardTitle>
                    <div className="flex items-center gap-1">
                      <Star className="h-4 w-4 text-yellow-500 fill-current" />
                      <span className="font-medium">{event.rating}</span>
                      <span className="text-sm text-gray-600">({event.reviewCount})</span>
                    </div>
                  </div>
                </CardHeader>
                <CardContent className="space-y-4">
                  {/* Price Range */}
                  <div>
                    <div className="flex items-center gap-2 mb-2">
                      <Euro className="h-4 w-4 text-gray-600" />
                      <span className="text-lg font-bold">
                        {Math.min(...event.ticketTypes.map(t => t.price))} - {Math.max(...event.ticketTypes.map(t => t.price))} HRK
                      </span>
                    </div>
                    <p className="text-sm text-gray-600">Price varies by ticket type</p>
                  </div>

                  {/* Availability */}
                  <div>
                    <div className="flex items-center justify-between mb-2">
                      <span className="text-sm font-medium">Availability</span>
                      <span className="text-sm text-gray-600">
                        {event.totalCapacity - event.soldTickets} left
                      </span>
                    </div>
                    <div className="w-full bg-gray-200 rounded-full h-2">
                      <div 
                        className={`h-2 rounded-full ${
                          availabilityPercentage > 50 ? 'bg-green-500' : 
                          availabilityPercentage > 25 ? 'bg-yellow-500' : 'bg-red-500'
                        }`}
                        style={{ width: `${availabilityPercentage}%` }}
                      />
                    </div>
                  </div>

                  {/* Action Buttons */}
                  <div className="space-y-3">
                    <Button 
                      onClick={handleBookNow}
                      className="w-full"
                      size="lg"
                    >
                      <Ticket className="h-4 w-4 mr-2" />
                      Book Now
                    </Button>
                    
                    <div className="flex gap-2">
                      <Button 
                        variant="outline" 
                        onClick={handleLike}
                        className={`flex-1 ${event.isLiked ? 'text-red-500 border-red-200' : ''}`}
                      >
                        <Heart className={`h-4 w-4 mr-2 ${event.isLiked ? 'fill-current' : ''}`} />
                        {event.isLiked ? 'Liked' : 'Like'}
                      </Button>
                      <Button variant="outline" onClick={handleShare}>
                        <Share2 className="h-4 w-4" />
                      </Button>
                    </div>
                  </div>

                  {/* Quick Info */}
                  <div className="pt-4 border-t text-xs text-gray-500 space-y-1">
                    <p>✓ Instant confirmation</p>
                    <p>✓ Mobile tickets</p>
                    <p>✓ Secure payment</p>
                  </div>
                </CardContent>
              </Card>

              {/* Event Stats */}
              <Card>
                <CardHeader>
                  <CardTitle className="text-lg">Event Statistics</CardTitle>
                </CardHeader>
                <CardContent className="space-y-3">
                  <div className="flex justify-between">
                    <span className="text-gray-600">Interested</span>
                    <span className="font-medium">{event.soldTickets + 150}</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-gray-600">Attending</span>
                    <span className="font-medium">{event.soldTickets}</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-gray-600">Available</span>
                    <span className="font-medium">{event.totalCapacity - event.soldTickets}</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-gray-600">Created</span>
                    <span className="font-medium">
                      {formatDistanceToNow(new Date(event.created_at), { addSuffix: true })}
                    </span>
                  </div>
                </CardContent>
              </Card>
            </div>
          </div>
        </main>

        <Footer />

        {/* Booking Checkout Modal */}
        {event && (
          <BookingCheckout
            event={event}
            selectedTickets={selectedTickets}
            isOpen={showBooking}
            onClose={() => setShowBooking(false)}
            onBookingComplete={handleBookingComplete}
          />
        )}
      </div>
    </PageTransition>
  );
};

export default EventDetail;