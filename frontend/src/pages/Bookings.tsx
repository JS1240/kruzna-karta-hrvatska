import React, { useState, useEffect } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Input } from '@/components/ui/input';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogTrigger } from '@/components/ui/dialog';
import { 
  Calendar, 
  MapPin, 
  Clock, 
  Ticket,
  QrCode,
  Download,
  Mail,
  Search,
  Filter,
  ChevronRight,
  AlertCircle,
  CheckCircle,
  RefreshCw,
  ExternalLink
} from 'lucide-react';
import { formatDistanceToNow } from 'date-fns';
import { useNavigate } from 'react-router-dom';
import Header from '@/components/Header';
import Footer from '@/components/Footer';
import PageTransition from '@/components/PageTransition';
import TicketQR from '@/components/TicketQR';
import { getCurrentUser } from '@/lib/auth';
import { toast } from '@/hooks/use-toast';
import { eventsApi } from '@/lib/api';

interface Booking {
  id: string;
  bookingReference: string;
  eventId: string;
  eventTitle: string;
  eventDate: string;
  eventTime: string;
  eventLocation: string;
  eventVenue: string;
  status: 'confirmed' | 'pending' | 'cancelled' | 'refunded';
  totalAmount: number;
  currency: string;
  ticketCount: number;
  bookingDate: string;
  tickets: Array<{
    id: string;
    ticketType: string;
    price: number;
    qrCode: string;
    checkedIn: boolean;
    checkedInAt?: string;
  }>;
  refundable: boolean;
  refundDeadline?: string;
}

// Transform API booking data to local Booking interface
const transformApiBooking = (apiBooking: any): Booking => {
  return {
    id: apiBooking.id?.toString() || '',
    bookingReference: apiBooking.booking_reference || apiBooking.reference || 'N/A',
    eventId: apiBooking.event_id?.toString() || '',
    eventTitle: apiBooking.event?.title || apiBooking.event_title || 'Unknown Event',
    eventDate: apiBooking.event?.date || apiBooking.event_date || '',
    eventTime: apiBooking.event?.time || apiBooking.event_time || '00:00',
    eventLocation: apiBooking.event?.location || apiBooking.event_location || 'TBA',
    eventVenue: apiBooking.event?.venue || apiBooking.event_venue || 'TBA',
    status: apiBooking.status || 'pending',
    totalAmount: apiBooking.total_amount || 0,
    currency: apiBooking.currency || 'HRK',
    ticketCount: apiBooking.ticket_count || apiBooking.tickets?.length || 0,
    bookingDate: apiBooking.booking_date || apiBooking.created_at || new Date().toISOString(),
    tickets: apiBooking.tickets?.map((ticket: any) => ({
      id: ticket.id?.toString() || '',
      ticketType: ticket.ticket_type || ticket.type || 'General',
      price: ticket.price || 0,
      qrCode: ticket.qr_code || ticket.qrCode || '',
      checkedIn: ticket.checked_in || false,
      checkedInAt: ticket.checked_in_at || ticket.checkedInAt,
    })) || [],
    refundable: apiBooking.refundable ?? true,
    refundDeadline: apiBooking.refund_deadline || apiBooking.refundDeadline,
  };
};

const Bookings: React.FC = () => {
  const [bookings, setBookings] = useState<Booking[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [searchTerm, setSearchTerm] = useState('');
  const [selectedTab, setSelectedTab] = useState('all');
  const [selectedBooking, setSelectedBooking] = useState<Booking | null>(null);
  
  const user = getCurrentUser();
  const navigate = useNavigate();

  useEffect(() => {
    const fetchUserBookings = async () => {
      if (!user) {
        setLoading(false);
        setBookings([]);
        return;
      }

      try {
        setLoading(true);
        setError(null);
        
        // TODO: Replace with actual bookings API call
        // const response = await bookingsApi.getUserBookings(user.id);
        // const transformedBookings = response.bookings.map(transformApiBooking);
        // setBookings(transformedBookings);
        
        // For now, show empty state instead of mock data
        setBookings([]);
        
      } catch (err) {
        console.error('Failed to fetch user bookings:', err);
        setError('Failed to load your bookings');
        setBookings([]);
      } finally {
        setLoading(false);
      }
    };

    fetchUserBookings();
  }, [user]);

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'confirmed':
        return 'bg-green-100 text-green-800';
      case 'pending':
        return 'bg-accent-gold text-brand-black';
      case 'cancelled':
        return 'bg-red-100 text-red-800';
      case 'refunded':
        return 'bg-gray-100 text-gray-800';
      default:
        return 'bg-gray-100 text-gray-800';
    }
  };

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'confirmed':
        return <CheckCircle className="h-4 w-4" />;
      case 'pending':
        return <RefreshCw className="h-4 w-4" />;
      case 'cancelled':
      case 'refunded':
        return <AlertCircle className="h-4 w-4" />;
      default:
        return <AlertCircle className="h-4 w-4" />;
    }
  };

  const filterBookings = () => {
    let filtered = bookings;

    // Filter by search term
    if (searchTerm) {
      filtered = filtered.filter(booking => 
        booking.eventTitle.toLowerCase().includes(searchTerm.toLowerCase()) ||
        booking.bookingReference.toLowerCase().includes(searchTerm.toLowerCase()) ||
        booking.eventLocation.toLowerCase().includes(searchTerm.toLowerCase())
      );
    }

    // Filter by tab
    const now = new Date();
    switch (selectedTab) {
      case 'upcoming':
        filtered = filtered.filter(booking => 
          new Date(booking.eventDate) > now && booking.status === 'confirmed'
        );
        break;
      case 'past':
        filtered = filtered.filter(booking => 
          new Date(booking.eventDate) <= now
        );
        break;
      case 'cancelled':
        filtered = filtered.filter(booking => 
          booking.status === 'cancelled' || booking.status === 'refunded'
        );
        break;
    }

    return filtered.sort((a, b) => new Date(b.bookingDate).getTime() - new Date(a.bookingDate).getTime());
  };

  const handleDownloadTickets = (booking: Booking) => {
    // Simulate ticket download
    toast({
      title: "Tickets downloaded",
      description: `PDF tickets for ${booking.eventTitle} have been downloaded.`,
    });
  };

  const handleEmailTickets = (booking: Booking) => {
    // Simulate email resend
    toast({
      title: "Tickets sent",
      description: `Tickets for ${booking.eventTitle} have been sent to your email.`,
    });
  };

  const handleCancelBooking = (booking: Booking) => {
    // Simulate booking cancellation
    setBookings(prev => prev.map(b => 
      b.id === booking.id ? { ...b, status: 'cancelled' as const } : b
    ));
    
    toast({
      title: "Booking cancelled",
      description: `Your booking for ${booking.eventTitle} has been cancelled. Refund will be processed within 5-7 business days.`,
    });
  };

  if (!user) {
    return (
      <PageTransition>
        <div className="min-h-screen flex flex-col bg-cream">
          <Header />
          <main className="flex-grow container mx-auto px-4 py-8 text-center">
            <AlertCircle className="h-16 w-16 mx-auto text-gray-400 mb-4" />
            <h2 className="text-2xl font-bold text-gray-900 mb-2">Please log in</h2>
            <p className="text-gray-600 mb-6">You need to be logged in to view your bookings.</p>
          </main>
          <Footer />
        </div>
      </PageTransition>
    );
  }

  if (loading) {
    return (
      <PageTransition>
        <div className="min-h-screen flex flex-col bg-cream">
          <Header />
          <main className="flex-grow container mx-auto px-4 py-8">
            <div className="animate-pulse space-y-6">
              <div className="h-8 bg-gray-200 rounded w-1/4"></div>
              <div className="space-y-4">
                {[1, 2, 3].map(i => (
                  <div key={i} className="h-32 bg-gray-200 rounded"></div>
                ))}
              </div>
            </div>
          </main>
          <Footer />
        </div>
      </PageTransition>
    );
  }

  // Error state
  if (error) {
    return (
      <PageTransition>
        <div className="min-h-screen flex flex-col bg-cream">
          <Header />
          <main className="flex-grow container mx-auto px-4 py-8">
            <div className="text-center py-12">
              <AlertCircle className="h-16 w-16 mx-auto text-red-500 mb-4" />
              <h2 className="text-2xl font-bold text-gray-900 mb-2">Error Loading Bookings</h2>
              <p className="text-gray-600 mb-6">{error}</p>
              <Button onClick={() => window.location.reload()}>
                <RefreshCw className="h-4 w-4 mr-2" />
                Try Again
              </Button>
            </div>
          </main>
          <Footer />
        </div>
      </PageTransition>
    );
  }

  // No user logged in state
  if (!user) {
    return (
      <PageTransition>
        <div className="min-h-screen flex flex-col bg-cream">
          <Header />
          <main className="flex-grow container mx-auto px-4 py-8">
            <div className="text-center py-12">
              <Ticket className="h-16 w-16 mx-auto text-gray-400 mb-4" />
              <h2 className="text-2xl font-bold text-gray-900 mb-2">Please Log In</h2>
              <p className="text-gray-600 mb-6">You need to be logged in to view your bookings.</p>
              <Button onClick={() => navigate('/login')}>
                Log In
              </Button>
            </div>
          </main>
          <Footer />
        </div>
      </PageTransition>
    );
  }

  const filteredBookings = filterBookings();

  return (
    <PageTransition>
      <div className="min-h-screen flex flex-col bg-cream">
        <Header />
        
        <main className="flex-grow container mx-auto px-4 py-8">
          {/* Header */}
          <div className="mb-8">
            <h1 className="text-3xl font-bold text-navy-blue mb-2">My Bookings</h1>
            <p className="text-gray-600">Manage your event tickets and bookings</p>
          </div>

          {/* Search and Filter */}
          <div className="flex flex-col sm:flex-row gap-4 mb-6">
            <div className="relative flex-1">
              <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-gray-400" />
              <Input
                placeholder="Search bookings..."
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
                className="pl-10"
              />
            </div>
          </div>

          {/* Tabs */}
          <Tabs value={selectedTab} onValueChange={setSelectedTab} className="space-y-6">
            <TabsList className="grid w-full grid-cols-4">
              <TabsTrigger value="all">All Bookings</TabsTrigger>
              <TabsTrigger value="upcoming">Upcoming</TabsTrigger>
              <TabsTrigger value="past">Past</TabsTrigger>
              <TabsTrigger value="cancelled">Cancelled</TabsTrigger>
            </TabsList>

            <TabsContent value={selectedTab}>
              {filteredBookings.length === 0 ? (
                <Card>
                  <CardContent className="py-12 text-center">
                    <Ticket className="h-12 w-12 mx-auto text-gray-400 mb-4" />
                    <h3 className="text-lg font-semibold text-gray-900 mb-2">
                      No bookings found
                    </h3>
                    <p className="text-gray-600">
                      {searchTerm ? 'Try adjusting your search criteria.' : 'You haven\'t made any bookings yet.'}
                    </p>
                  </CardContent>
                </Card>
              ) : (
                <div className="space-y-4">
                  {filteredBookings.map((booking) => (
                    <Card key={booking.id} className="hover:shadow-lg transition-shadow">
                      <CardContent className="p-6">
                        <div className="flex flex-col lg:flex-row lg:items-center justify-between gap-4">
                          {/* Main Info */}
                          <div className="flex-1">
                            <div className="flex items-center gap-3 mb-2">
                              <h3 className="text-lg font-semibold">{booking.eventTitle}</h3>
                              <Badge className={getStatusColor(booking.status)}>
                                <div className="flex items-center gap-1">
                                  {getStatusIcon(booking.status)}
                                  {booking.status.charAt(0).toUpperCase() + booking.status.slice(1)}
                                </div>
                              </Badge>
                            </div>
                            
                            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-3 text-sm text-gray-600">
                              <div className="flex items-center gap-1">
                                <Calendar className="h-4 w-4" />
                                {new Date(booking.eventDate + 'T' + booking.eventTime).toLocaleDateString()}
                              </div>
                              <div className="flex items-center gap-1">
                                <Clock className="h-4 w-4" />
                                {booking.eventTime}
                              </div>
                              <div className="flex items-center gap-1">
                                <MapPin className="h-4 w-4" />
                                {booking.eventVenue}
                              </div>
                              <div className="flex items-center gap-1">
                                <Ticket className="h-4 w-4" />
                                {booking.ticketCount} ticket{booking.ticketCount !== 1 ? 's' : ''}
                              </div>
                            </div>
                            
                            <div className="mt-3 flex items-center gap-4 text-sm">
                              <span className="font-medium">
                                Ref: {booking.bookingReference}
                              </span>
                              <span>
                                Total: {booking.totalAmount} {booking.currency}
                              </span>
                              <span className="text-gray-500">
                                Booked {formatDistanceToNow(new Date(booking.bookingDate), { addSuffix: true })}
                              </span>
                            </div>
                          </div>

                          {/* Actions */}
                          <div className="flex flex-col sm:flex-row gap-2">
                            <Dialog>
                              <DialogTrigger asChild>
                                <Button variant="outline" onClick={() => setSelectedBooking(booking)}>
                                  View Details
                                  <ChevronRight className="h-4 w-4 ml-1" />
                                </Button>
                              </DialogTrigger>
                              <DialogContent className="max-w-2xl max-h-[80vh] overflow-y-auto">
                                <DialogHeader>
                                  <DialogTitle>Booking Details</DialogTitle>
                                </DialogHeader>
                                {selectedBooking && (
                                  <div className="space-y-6">
                                    {/* Event Info */}
                                    <div>
                                      <h4 className="font-medium mb-3">Event Information</h4>
                                      <div className="bg-gray-50 rounded-lg p-4 space-y-2">
                                        <h5 className="font-medium">{selectedBooking.eventTitle}</h5>
                                        <div className="grid grid-cols-1 sm:grid-cols-2 gap-2 text-sm text-gray-600">
                                          <div>📅 {new Date(selectedBooking.eventDate + 'T' + selectedBooking.eventTime).toLocaleDateString()}</div>
                                          <div>🕒 {selectedBooking.eventTime}</div>
                                          <div>📍 {selectedBooking.eventVenue}</div>
                                          <div>🎫 {selectedBooking.ticketCount} ticket(s)</div>
                                        </div>
                                      </div>
                                    </div>

                                    {/* Tickets */}
                                    <div>
                                      <h4 className="font-medium mb-3">Your Tickets</h4>
                                      <div className="space-y-3">
                                        {selectedBooking.tickets.map((ticket, index) => (
                                          <div key={ticket.id} className="border rounded-lg p-4">
                                            <div className="flex justify-between items-center mb-2">
                                              <span className="font-medium">Ticket #{index + 1}</span>
                                              {ticket.checkedIn ? (
                                                <Badge className="bg-green-100 text-green-800">
                                                  ✓ Checked In
                                                </Badge>
                                              ) : (
                                                <Badge variant="outline">Not Used</Badge>
                                              )}
                                            </div>
                                            <div className="text-sm text-gray-600 space-y-1">
                                              <div>Type: {ticket.ticketType}</div>
                                              <div>Price: {ticket.price} {selectedBooking.currency}</div>
                                              <div>QR Code: {ticket.qrCode}</div>
                                              {ticket.checkedIn && ticket.checkedInAt && (
                                                <div>Used: {new Date(ticket.checkedInAt).toLocaleString()}</div>
                                              )}
                                            </div>
                                            <div className="mt-3 flex gap-2">
                                              <TicketQR
                                                ticket={ticket}
                                                event={{
                                                  title: selectedBooking.eventTitle,
                                                  date: selectedBooking.eventDate,
                                                  time: selectedBooking.eventTime,
                                                  venue: selectedBooking.eventVenue,
                                                  location: selectedBooking.eventLocation,
                                                }}
                                                booking={{
                                                  bookingReference: selectedBooking.bookingReference,
                                                  currency: selectedBooking.currency,
                                                }}
                                                holderName={user?.name || user?.email || 'Guest'}
                                              />
                                            </div>
                                          </div>
                                        ))}
                                      </div>
                                    </div>

                                    {/* Actions */}
                                    <div className="flex gap-2 pt-4 border-t">
                                      <Button 
                                        onClick={() => handleDownloadTickets(selectedBooking)}
                                        className="flex-1"
                                      >
                                        <Download className="h-4 w-4 mr-2" />
                                        Download Tickets
                                      </Button>
                                      <Button 
                                        variant="outline"
                                        onClick={() => handleEmailTickets(selectedBooking)}
                                      >
                                        <Mail className="h-4 w-4 mr-2" />
                                        Email Tickets
                                      </Button>
                                    </div>

                                    {/* Cancellation */}
                                    {selectedBooking.refundable && selectedBooking.status === 'confirmed' && (
                                      <div className="bg-red-50 border border-red-200 rounded-lg p-4">
                                        <h4 className="font-medium text-red-900 mb-2">Cancellation Policy</h4>
                                        <p className="text-sm text-red-700 mb-3">
                                          This booking can be cancelled until {selectedBooking.refundDeadline ? 
                                            new Date(selectedBooking.refundDeadline).toLocaleDateString() : 'the event date'}.
                                        </p>
                                        <Button 
                                          variant="destructive"
                                          size="sm"
                                          onClick={() => handleCancelBooking(selectedBooking)}
                                        >
                                          Cancel Booking
                                        </Button>
                                      </div>
                                    )}
                                  </div>
                                )}
                              </DialogContent>
                            </Dialog>

                            {booking.status === 'confirmed' && (
                              <Button onClick={() => handleDownloadTickets(booking)}>
                                <Download className="h-4 w-4 mr-2" />
                                Download
                              </Button>
                            )}
                          </div>
                        </div>
                      </CardContent>
                    </Card>
                  ))}
                </div>
              )}
            </TabsContent>
          </Tabs>
        </main>

        <Footer />
      </div>
    </PageTransition>
  );
};

export default Bookings;