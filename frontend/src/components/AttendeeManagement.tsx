import React, { useState, useEffect } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Badge } from '@/components/ui/badge';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogTrigger } from '@/components/ui/dialog';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { 
  Users, 
  Search, 
  Filter, 
  Download, 
  Mail, 
  CheckCircle,
  Clock,
  AlertCircle,
  RefreshCw,
  QrCode,
  MapPin,
  Calendar,
  Ticket,
  MoreHorizontal,
  UserCheck,
  UserX,
  Send,
  FileSpreadsheet
} from 'lucide-react';
import { formatDistanceToNow } from 'date-fns';
import { toast } from '@/hooks/use-toast';

interface Attendee {
  id: string;
  bookingReference: string;
  firstName: string;
  lastName: string;
  email: string;
  phone: string;
  ticketType: string;
  ticketId: string;
  qrCode: string;
  bookingDate: string;
  checkInStatus: 'pending' | 'checked-in' | 'no-show';
  checkInTime?: string;
  paymentStatus: 'pending' | 'completed' | 'refunded';
  specialRequests?: string;
  totalPaid: number;
  currency: string;
}

interface AttendeeStats {
  totalAttendees: number;
  checkedIn: number;
  pending: number;
  noShows: number;
  totalRevenue: number;
  averageTicketPrice: number;
}

interface AttendeeManagementProps {
  eventId: string;
  eventTitle: string;
  eventDate: string;
  eventTime: string;
}

// Mock data
const mockAttendees: Attendee[] = [
  {
    id: '1',
    bookingReference: 'BK20250001',
    firstName: 'Ana',
    lastName: 'Marić',
    email: 'ana.maric@example.com',
    phone: '+385 91 234 5678',
    ticketType: 'VIP Experience',
    ticketId: 'T001',
    qrCode: 'QR123456789',
    bookingDate: '2025-06-20T14:30:00Z',
    checkInStatus: 'checked-in',
    checkInTime: '2025-08-15T18:45:00Z',
    paymentStatus: 'completed',
    specialRequests: 'Wheelchair accessible seating',
    totalPaid: 450,
    currency: 'HRK',
  },
  {
    id: '2',
    bookingReference: 'BK20250002',
    firstName: 'Marko',
    lastName: 'Kovač',
    email: 'marko.kovac@example.com',
    phone: '+385 92 345 6789',
    ticketType: 'Standard Admission',
    ticketId: 'T002',
    qrCode: 'QR123456790',
    bookingDate: '2025-06-18T10:15:00Z',
    checkInStatus: 'pending',
    paymentStatus: 'completed',
    totalPaid: 220,
    currency: 'HRK',
  },
  {
    id: '3',
    bookingReference: 'BK20250003',
    firstName: 'Petra',
    lastName: 'Novak',
    email: 'petra.novak@example.com',
    phone: '+385 93 456 7890',
    ticketType: 'Standard Admission',
    ticketId: 'T003',
    qrCode: 'QR123456791',
    bookingDate: '2025-06-15T16:20:00Z',
    checkInStatus: 'no-show',
    paymentStatus: 'completed',
    totalPaid: 220,
    currency: 'HRK',
  },
  {
    id: '4',
    bookingReference: 'BK20250004',
    firstName: 'Ivo',
    lastName: 'Petrić',
    email: 'ivo.petric@example.com',
    phone: '+385 94 567 8901',
    ticketType: 'Early Bird',
    ticketId: 'T004',
    qrCode: 'QR123456792',
    bookingDate: '2025-06-10T09:30:00Z',
    checkInStatus: 'checked-in',
    checkInTime: '2025-08-15T19:10:00Z',
    paymentStatus: 'completed',
    totalPaid: 150,
    currency: 'HRK',
  },
];

const AttendeeManagement: React.FC<AttendeeManagementProps> = ({
  eventId,
  eventTitle,
  eventDate,
  eventTime,
}) => {
  const [attendees, setAttendees] = useState<Attendee[]>([]);
  const [filteredAttendees, setFilteredAttendees] = useState<Attendee[]>([]);
  const [loading, setLoading] = useState(true);
  const [searchTerm, setSearchTerm] = useState('');
  const [statusFilter, setStatusFilter] = useState<string>('all');
  const [ticketTypeFilter, setTicketTypeFilter] = useState<string>('all');
  const [selectedAttendee, setSelectedAttendee] = useState<Attendee | null>(null);
  const [selectedTab, setSelectedTab] = useState('list');

  useEffect(() => {
    // Simulate API call
    setTimeout(() => {
      setAttendees(mockAttendees);
      setLoading(false);
    }, 1000);
  }, [eventId]);

  useEffect(() => {
    // Filter attendees based on search and filters
    let filtered = attendees;

    // Search filter
    if (searchTerm) {
      filtered = filtered.filter(attendee =>
        attendee.firstName.toLowerCase().includes(searchTerm.toLowerCase()) ||
        attendee.lastName.toLowerCase().includes(searchTerm.toLowerCase()) ||
        attendee.email.toLowerCase().includes(searchTerm.toLowerCase()) ||
        attendee.bookingReference.toLowerCase().includes(searchTerm.toLowerCase())
      );
    }

    // Status filter
    if (statusFilter !== 'all') {
      filtered = filtered.filter(attendee => attendee.checkInStatus === statusFilter);
    }

    // Ticket type filter
    if (ticketTypeFilter !== 'all') {
      filtered = filtered.filter(attendee => attendee.ticketType === ticketTypeFilter);
    }

    setFilteredAttendees(filtered);
  }, [attendees, searchTerm, statusFilter, ticketTypeFilter]);

  const calculateStats = (): AttendeeStats => {
    const totalAttendees = attendees.length;
    const checkedIn = attendees.filter(a => a.checkInStatus === 'checked-in').length;
    const pending = attendees.filter(a => a.checkInStatus === 'pending').length;
    const noShows = attendees.filter(a => a.checkInStatus === 'no-show').length;
    const totalRevenue = attendees.reduce((sum, a) => sum + a.totalPaid, 0);
    const averageTicketPrice = totalAttendees > 0 ? totalRevenue / totalAttendees : 0;

    return {
      totalAttendees,
      checkedIn,
      pending,
      noShows,
      totalRevenue,
      averageTicketPrice,
    };
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'checked-in':
        return 'bg-green-100 text-green-800';
      case 'pending':
        return 'bg-yellow-100 text-yellow-800';
      case 'no-show':
        return 'bg-red-100 text-red-800';
      default:
        return 'bg-gray-100 text-gray-800';
    }
  };

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'checked-in':
        return <CheckCircle className="h-4 w-4" />;
      case 'pending':
        return <Clock className="h-4 w-4" />;
      case 'no-show':
        return <AlertCircle className="h-4 w-4" />;
      default:
        return <RefreshCw className="h-4 w-4" />;
    }
  };

  const handleCheckIn = (attendeeId: string) => {
    setAttendees(prev => prev.map(attendee =>
      attendee.id === attendeeId
        ? {
            ...attendee,
            checkInStatus: 'checked-in' as const,
            checkInTime: new Date().toISOString(),
          }
        : attendee
    ));

    toast({
      title: "Attendee checked in",
      description: "The attendee has been successfully checked in.",
    });
  };

  const handleMarkNoShow = (attendeeId: string) => {
    setAttendees(prev => prev.map(attendee =>
      attendee.id === attendeeId
        ? { ...attendee, checkInStatus: 'no-show' as const }
        : attendee
    ));

    toast({
      title: "Marked as no-show",
      description: "The attendee has been marked as no-show.",
    });
  };

  const handleSendEmail = (attendee: Attendee) => {
    toast({
      title: "Email sent",
      description: `Reminder email sent to ${attendee.email}`,
    });
  };

  const handleExportData = (format: 'csv' | 'excel') => {
    toast({
      title: "Export started",
      description: `Attendee data is being exported as ${format.toUpperCase()}`,
    });
  };

  const getUniqueTicketTypes = () => {
    return [...new Set(attendees.map(a => a.ticketType))];
  };

  const stats = calculateStats();

  if (loading) {
    return (
      <div className="space-y-6">
        <div className="animate-pulse">
          <div className="h-8 bg-gray-200 rounded w-1/3 mb-4"></div>
          <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-6">
            {Array.from({ length: 4 }).map((_, i) => (
              <div key={i} className="h-24 bg-gray-200 rounded"></div>
            ))}
          </div>
          <div className="h-64 bg-gray-200 rounded"></div>
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div>
        <h2 className="text-2xl font-bold text-navy-blue mb-2">Attendee Management</h2>
        <div className="flex items-center gap-4 text-sm text-gray-600">
          <div className="flex items-center gap-1">
            <Calendar className="h-4 w-4" />
            {eventTitle}
          </div>
          <div className="flex items-center gap-1">
            <Clock className="h-4 w-4" />
            {new Date(eventDate + 'T' + eventTime).toLocaleDateString()} at {eventTime}
          </div>
        </div>
      </div>

      {/* Statistics Cards */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <Card>
          <CardContent className="pt-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-gray-600">Total Attendees</p>
                <p className="text-2xl font-bold">{stats.totalAttendees}</p>
              </div>
              <Users className="h-8 w-8 text-blue-500" />
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="pt-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-gray-600">Checked In</p>
                <p className="text-2xl font-bold text-green-600">{stats.checkedIn}</p>
              </div>
              <UserCheck className="h-8 w-8 text-green-500" />
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="pt-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-gray-600">Pending</p>
                <p className="text-2xl font-bold text-yellow-600">{stats.pending}</p>
              </div>
              <Clock className="h-8 w-8 text-yellow-500" />
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="pt-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-gray-600">Total Revenue</p>
                <p className="text-2xl font-bold">{stats.totalRevenue.toLocaleString()} HRK</p>
              </div>
              <Ticket className="h-8 w-8 text-blue-500" />
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Tabs */}
      <Tabs value={selectedTab} onValueChange={setSelectedTab}>
        <TabsList>
          <TabsTrigger value="list">Attendee List</TabsTrigger>
          <TabsTrigger value="checkin">Check-in</TabsTrigger>
          <TabsTrigger value="communication">Communication</TabsTrigger>
        </TabsList>

        <TabsContent value="list" className="space-y-4">
          {/* Filters and Search */}
          <div className="flex flex-col lg:flex-row gap-4">
            <div className="flex-1">
              <div className="relative">
                <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-gray-400" />
                <Input
                  placeholder="Search attendees..."
                  value={searchTerm}
                  onChange={(e) => setSearchTerm(e.target.value)}
                  className="pl-10"
                />
              </div>
            </div>
            
            <Select value={statusFilter} onValueChange={setStatusFilter}>
              <SelectTrigger className="w-48">
                <SelectValue placeholder="Filter by status" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="all">All Statuses</SelectItem>
                <SelectItem value="pending">Pending</SelectItem>
                <SelectItem value="checked-in">Checked In</SelectItem>
                <SelectItem value="no-show">No Show</SelectItem>
              </SelectContent>
            </Select>

            <Select value={ticketTypeFilter} onValueChange={setTicketTypeFilter}>
              <SelectTrigger className="w-48">
                <SelectValue placeholder="Filter by ticket type" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="all">All Ticket Types</SelectItem>
                {getUniqueTicketTypes().map(type => (
                  <SelectItem key={type} value={type}>{type}</SelectItem>
                ))}
              </SelectContent>
            </Select>

            <Button
              onClick={() => handleExportData('csv')}
              variant="outline"
              className="gap-2"
            >
              <Download className="h-4 w-4" />
              Export
            </Button>
          </div>

          {/* Attendee List */}
          <div className="space-y-3">
            {filteredAttendees.map((attendee) => (
              <Card key={attendee.id}>
                <CardContent className="pt-6">
                  <div className="flex flex-col lg:flex-row lg:items-center justify-between gap-4">
                    <div className="flex-1">
                      <div className="flex items-center gap-3 mb-2">
                        <h4 className="font-semibold">
                          {attendee.firstName} {attendee.lastName}
                        </h4>
                        <Badge className={getStatusColor(attendee.checkInStatus)}>
                          <div className="flex items-center gap-1">
                            {getStatusIcon(attendee.checkInStatus)}
                            {attendee.checkInStatus.replace('-', ' ').toUpperCase()}
                          </div>
                        </Badge>
                        <Badge variant="outline">{attendee.ticketType}</Badge>
                      </div>
                      
                      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-2 text-sm text-gray-600">
                        <div>{attendee.email}</div>
                        <div>{attendee.phone}</div>
                        <div>Ref: {attendee.bookingReference}</div>
                        <div>{attendee.totalPaid} {attendee.currency}</div>
                      </div>
                      
                      {attendee.checkInTime && (
                        <p className="text-xs text-green-600 mt-1">
                          Checked in {formatDistanceToNow(new Date(attendee.checkInTime), { addSuffix: true })}
                        </p>
                      )}
                    </div>

                    <div className="flex gap-2">
                      {attendee.checkInStatus === 'pending' && (
                        <>
                          <Button
                            size="sm"
                            onClick={() => handleCheckIn(attendee.id)}
                            className="gap-1"
                          >
                            <CheckCircle className="h-4 w-4" />
                            Check In
                          </Button>
                          <Button
                            size="sm"
                            variant="outline"
                            onClick={() => handleMarkNoShow(attendee.id)}
                          >
                            <UserX className="h-4 w-4" />
                          </Button>
                        </>
                      )}
                      
                      <Dialog>
                        <DialogTrigger asChild>
                          <Button
                            size="sm"
                            variant="outline"
                            onClick={() => setSelectedAttendee(attendee)}
                          >
                            <MoreHorizontal className="h-4 w-4" />
                          </Button>
                        </DialogTrigger>
                        <DialogContent className="max-w-2xl">
                          <DialogHeader>
                            <DialogTitle>Attendee Details</DialogTitle>
                          </DialogHeader>
                          {selectedAttendee && (
                            <div className="space-y-4">
                              <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                                <div>
                                  <h4 className="font-medium mb-2">Personal Information</h4>
                                  <div className="space-y-1 text-sm">
                                    <p><strong>Name:</strong> {selectedAttendee.firstName} {selectedAttendee.lastName}</p>
                                    <p><strong>Email:</strong> {selectedAttendee.email}</p>
                                    <p><strong>Phone:</strong> {selectedAttendee.phone}</p>
                                  </div>
                                </div>
                                
                                <div>
                                  <h4 className="font-medium mb-2">Booking Information</h4>
                                  <div className="space-y-1 text-sm">
                                    <p><strong>Reference:</strong> {selectedAttendee.bookingReference}</p>
                                    <p><strong>Ticket Type:</strong> {selectedAttendee.ticketType}</p>
                                    <p><strong>Amount Paid:</strong> {selectedAttendee.totalPaid} {selectedAttendee.currency}</p>
                                    <p><strong>Booking Date:</strong> {new Date(selectedAttendee.bookingDate).toLocaleDateString()}</p>
                                  </div>
                                </div>
                              </div>

                              {selectedAttendee.specialRequests && (
                                <div>
                                  <h4 className="font-medium mb-2">Special Requests</h4>
                                  <p className="text-sm bg-gray-50 p-3 rounded">{selectedAttendee.specialRequests}</p>
                                </div>
                              )}

                              <div className="flex gap-2 pt-4 border-t">
                                <Button
                                  onClick={() => handleSendEmail(selectedAttendee)}
                                  className="gap-2"
                                >
                                  <Mail className="h-4 w-4" />
                                  Send Email
                                </Button>
                                <Button variant="outline" className="gap-2">
                                  <QrCode className="h-4 w-4" />
                                  View QR Code
                                </Button>
                              </div>
                            </div>
                          )}
                        </DialogContent>
                      </Dialog>
                    </div>
                  </div>
                </CardContent>
              </Card>
            ))}

            {filteredAttendees.length === 0 && (
              <Card>
                <CardContent className="py-12 text-center">
                  <Users className="h-12 w-12 mx-auto text-gray-400 mb-4" />
                  <h3 className="text-lg font-semibold text-gray-900 mb-2">
                    No attendees found
                  </h3>
                  <p className="text-gray-600">
                    {searchTerm || statusFilter !== 'all' || ticketTypeFilter !== 'all'
                      ? 'Try adjusting your search or filters.'
                      : 'No attendees have booked tickets for this event yet.'}
                  </p>
                </CardContent>
              </Card>
            )}
          </div>
        </TabsContent>

        <TabsContent value="checkin" className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle>Quick Check-in</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="space-y-4">
                <div className="text-center">
                  <QrCode className="h-16 w-16 mx-auto text-gray-400 mb-4" />
                  <h3 className="text-lg font-semibold mb-2">Scan QR Code</h3>
                  <p className="text-gray-600 mb-4">
                    Use a QR code scanner to quickly check in attendees
                  </p>
                  <Button>
                    <QrCode className="h-4 w-4 mr-2" />
                    Start QR Scanner
                  </Button>
                </div>
                
                <div className="text-center text-gray-500">or</div>
                
                <div>
                  <Input
                    placeholder="Enter booking reference or ticket ID"
                    className="text-center"
                  />
                  <Button className="w-full mt-2">
                    Manual Check-in
                  </Button>
                </div>
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="communication" className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle>Send Announcements</CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              <div>
                <label className="text-sm font-medium">Recipients</label>
                <Select defaultValue="all">
                  <SelectTrigger>
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="all">All Attendees</SelectItem>
                    <SelectItem value="checked-in">Checked In</SelectItem>
                    <SelectItem value="pending">Pending</SelectItem>
                    <SelectItem value="vip">VIP Ticket Holders</SelectItem>
                  </SelectContent>
                </Select>
              </div>
              
              <div>
                <label className="text-sm font-medium">Message</label>
                <textarea
                  className="w-full mt-1 p-3 border rounded-lg"
                  rows={4}
                  placeholder="Enter your message to attendees..."
                />
              </div>
              
              <Button className="gap-2">
                <Send className="h-4 w-4" />
                Send Message
              </Button>
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>
    </div>
  );
};

export default AttendeeManagement;