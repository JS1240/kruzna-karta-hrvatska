import React, { useState, useEffect } from 'react';
import { useNavigate, useLocation } from 'react-router-dom';
import { Card, CardContent, CardHeader, CardTitle } from '../components/ui/card';
import { Button } from '../components/ui/button';
import { Badge } from '../components/ui/badge';
import { Alert, AlertDescription } from '../components/ui/alert';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '../components/ui/tabs';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '../components/ui/select';
import { 
  ChartContainer,
  ChartTooltip,
  ChartTooltipContent,
  ChartLegend,
  ChartLegendContent
} from '../components/ui/chart';
import { 
  LineChart, 
  Line, 
  BarChart, 
  Bar, 
  PieChart, 
  Pie, 
  Cell, 
  AreaChart, 
  Area,
  XAxis, 
  YAxis, 
  CartesianGrid, 
  ResponsiveContainer 
} from 'recharts';
import { 
  Plus, 
  Calendar, 
  MapPin, 
  Clock, 
  Eye, 
  Edit, 
  Trash2, 
  DollarSign,
  Users,
  TrendingUp,
  CheckCircle,
  AlertCircle,
  XCircle,
  BarChart3,
  PieChart as PieChartIcon,
  Activity,
  Target
} from 'lucide-react';
import Header from '../components/Header';
import Footer from '../components/Footer';
import PageTransition from '../components/PageTransition';

interface Event {
  id: number;
  title: string;
  date: string;
  time: string;
  location: string;
  approval_status: string;
  event_status: string;
  category: {
    id: number;
    name: string;
  } | null;
  venue: {
    id: number;
    name: string;
  } | null;
  ticket_types_count: number;
  view_count: number;
  created_at: string;
}

interface Stats {
  events: {
    total: number;
    pending: number;
    approved: number;
    rejected: number;
  };
  bookings: {
    total_bookings: number;
    total_revenue: number;
    platform_commission: number;
    organizer_revenue: number;
  };
}

interface RevenueTrend {
  period: string;
  total_revenue: number;
  commission: number;
  organizer_revenue: number;
  booking_count: number;
}

interface EventPerformance {
  event_id: number;
  title: string;
  date: string;
  location: string;
  total_bookings: number;
  total_revenue: number;
  commission: number;
  organizer_revenue: number;
  tickets_sold: number;
  view_count: number;
  conversion_rate: number;
}

interface TicketTypeAnalytics {
  name: string;
  price: number;
  total_bookings: number;
  tickets_sold: number;
  total_revenue: number;
  organizer_revenue: number;
  total_quantity: number;
  available_quantity: number;
  sold_percentage: number;
}

interface ConversionMetrics {
  overall_conversion_rate: number;
  total_views: number;
  total_bookings: number;
  conversion_by_status: Array<{
    status: string;
    views: number;
    bookings: number;
    conversion_rate: number;
  }>;
}

interface GeographicRevenue {
  location: string;
  event_count: number;
  total_bookings: number;
  total_revenue: number;
  organizer_revenue: number;
  avg_revenue_per_event: number;
}

const OrganizerDashboard = () => {
  const navigate = useNavigate();
  const location = useLocation();
  const [events, setEvents] = useState<Event[]>([]);
  const [stats, setStats] = useState<Stats | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [activeTab, setActiveTab] = useState('overview');
  const [message, setMessage] = useState<{ text: string; type: 'success' | 'error' } | null>(null);
  
  // Analytics state
  const [revenueTrends, setRevenueTrends] = useState<RevenueTrend[]>([]);
  const [eventPerformance, setEventPerformance] = useState<EventPerformance[]>([]);
  const [ticketAnalytics, setTicketAnalytics] = useState<TicketTypeAnalytics[]>([]);
  const [conversionMetrics, setConversionMetrics] = useState<ConversionMetrics | null>(null);
  const [geographicRevenue, setGeographicRevenue] = useState<GeographicRevenue[]>([]);
  const [analyticsLoading, setAnalyticsLoading] = useState(false);
  const [revenuePeriod, setRevenuePeriod] = useState('month');

  useEffect(() => {
    // Check for navigation message
    if (location.state?.message) {
      setMessage({
        text: location.state.message,
        type: location.state.type || 'success'
      });
      // Clear the state
      navigate(location.pathname, { replace: true });
    }

    fetchData();
  }, [location, navigate]);

  useEffect(() => {
    if (activeTab === 'analytics') {
      fetchAnalyticsData();
    }
  }, [activeTab, revenuePeriod]);

  useEffect(() => {
    if (message) {
      const timer = setTimeout(() => setMessage(null), 5000);
      return () => clearTimeout(timer);
    }
  }, [message]);

  const fetchAnalyticsData = async () => {
    setAnalyticsLoading(true);

    try {
      const token = localStorage.getItem('token');
      if (!token) {
        navigate('/login');
        return;
      }

      const apiBase = import.meta.env.VITE_API_BASE_URL || "http://localhost:8000/api";
      
      // Fetch all analytics data in parallel
      const [
        trendsResponse,
        performanceResponse,
        ticketsResponse,
        conversionResponse,
        geoResponse
      ] = await Promise.all([
        fetch(`${apiBase}/user-events/analytics/revenue-trends?period=${revenuePeriod}`, {
          headers: { 'Authorization': `Bearer ${token}` }
        }),
        fetch(`${apiBase}/user-events/analytics/event-performance`, {
          headers: { 'Authorization': `Bearer ${token}` }
        }),
        fetch(`${apiBase}/user-events/analytics/ticket-types`, {
          headers: { 'Authorization': `Bearer ${token}` }
        }),
        fetch(`${apiBase}/user-events/analytics/booking-conversion`, {
          headers: { 'Authorization': `Bearer ${token}` }
        }),
        fetch(`${apiBase}/user-events/analytics/geographic-revenue`, {
          headers: { 'Authorization': `Bearer ${token}` }
        })
      ]);

      if (trendsResponse.ok) {
        const trendsData = await trendsResponse.json();
        setRevenueTrends(trendsData.trends || []);
      }

      if (performanceResponse.ok) {
        const performanceData = await performanceResponse.json();
        setEventPerformance(performanceData.events || []);
      }

      if (ticketsResponse.ok) {
        const ticketsData = await ticketsResponse.json();
        setTicketAnalytics(ticketsData.ticket_types || []);
      }

      if (conversionResponse.ok) {
        const conversionData = await conversionResponse.json();
        setConversionMetrics(conversionData);
      }

      if (geoResponse.ok) {
        const geoData = await geoResponse.json();
        setGeographicRevenue(geoData.locations || []);
      }

    } catch (error) {
      console.error('Error fetching analytics data:', error);
    } finally {
      setAnalyticsLoading(false);
    }
  };

  const fetchData = async () => {
    setLoading(true);
    setError('');

    try {
      const token = localStorage.getItem('token');
      if (!token) {
        navigate('/login');
        return;
      }

      const apiBase = import.meta.env.VITE_API_BASE_URL || "http://localhost:8000/api";
      
      // Fetch events and stats in parallel
      const [eventsResponse, statsResponse] = await Promise.all([
        fetch(`${apiBase}/user-events/my-events`, {
          headers: { 'Authorization': `Bearer ${token}` }
        }),
        fetch(`${apiBase}/user-events/stats/organizer`, {
          headers: { 'Authorization': `Bearer ${token}` }
        })
      ]);

      if (eventsResponse.status === 401 || statsResponse.status === 401) {
        localStorage.removeItem('token');
        navigate('/login');
        return;
      }

      if (eventsResponse.status === 403) {
        setError('You need to be a venue owner or manager to access this dashboard. Please contact support to upgrade your account.');
        return;
      }

      const eventsData = await eventsResponse.json();
      const statsData = await statsResponse.json();

      if (eventsResponse.ok) {
        setEvents(eventsData.events || []);
      } else {
        setError(eventsData.detail || 'Failed to load events');
      }

      if (statsResponse.ok) {
        setStats(statsData);
      }

    } catch (error) {
      console.error('Error fetching data:', error);
      setError('Network error. Please check your connection.');
    } finally {
      setLoading(false);
    }
  };

  const getStatusBadge = (status: string) => {
    switch (status) {
      case 'pending':
        return <Badge variant="secondary" className="bg-yellow-100 text-yellow-800"><AlertCircle className="h-3 w-3 mr-1" />Pending Review</Badge>;
      case 'approved':
        return <Badge variant="default" className="bg-green-100 text-green-800"><CheckCircle className="h-3 w-3 mr-1" />Approved</Badge>;
      case 'rejected':
        return <Badge variant="destructive"><XCircle className="h-3 w-3 mr-1" />Rejected</Badge>;
      default:
        return <Badge variant="outline">{status}</Badge>;
    }
  };

  const getEventStatusBadge = (status: string) => {
    switch (status) {
      case 'active':
        return <Badge variant="default">Active</Badge>;
      case 'draft':
        return <Badge variant="outline">Draft</Badge>;
      case 'cancelled':
        return <Badge variant="destructive">Cancelled</Badge>;
      case 'sold_out':
        return <Badge variant="secondary">Sold Out</Badge>;
      default:
        return <Badge variant="outline">{status}</Badge>;
    }
  };

  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleDateString('en-US', {
      year: 'numeric',
      month: 'short',
      day: 'numeric'
    });
  };

  const formatCurrency = (amount: number) => {
    return new Intl.NumberFormat('hr-HR', {
      style: 'currency',
      currency: 'EUR'
    }).format(amount);
  };

  const chartColors = ['#3b82f6', '#10b981', '#f59e0b', '#ef4444', '#8b5cf6', '#06b6d4'];
  
  const chartConfig = {
    total_revenue: {
      label: 'Total Revenue',
      color: '#3b82f6'
    },
    organizer_revenue: {
      label: 'Your Revenue',
      color: '#10b981'
    },
    commission: {
      label: 'Platform Fee',
      color: '#ef4444'
    },
    booking_count: {
      label: 'Bookings',
      color: '#8b5cf6'
    }
  };

  const formatPeriodLabel = (period: string) => {
    if (!period) return '';
    const date = new Date(period);
    return date.toLocaleDateString('en-US', {
      month: 'short',
      year: 'numeric',
      ...(revenuePeriod === 'week' && { day: 'numeric' })
    });
  };

  if (loading) {
    return (
      <PageTransition>
        <div className="min-h-screen flex flex-col bg-cream">
          <Header />
          <main className="flex-grow container mx-auto px-4 py-8">
            <div className="flex justify-center items-center h-64">
              <div className="animate-spin rounded-full h-12 w-12 border-4 border-navy-blue border-t-transparent"></div>
            </div>
          </main>
          <Footer />
        </div>
      </PageTransition>
    );
  }

  if (error) {
    return (
      <PageTransition>
        <div className="min-h-screen flex flex-col bg-cream">
          <Header />
          <main className="flex-grow container mx-auto px-4 py-8">
            <Alert className="border-red-200 bg-red-50 max-w-2xl mx-auto">
              <AlertCircle className="h-4 w-4" />
              <AlertDescription className="text-red-700">
                {error}
              </AlertDescription>
            </Alert>
          </main>
          <Footer />
        </div>
      </PageTransition>
    );
  }

  return (
    <PageTransition>
      <div className="min-h-screen flex flex-col bg-cream">
        <Header />
        
        <main className="flex-grow container mx-auto px-4 py-8">
          <div className="max-w-7xl mx-auto">
            {/* Header */}
            <div className="flex justify-between items-center mb-8">
              <div>
                <h1 className="text-3xl font-bold text-navy-blue font-sreda">
                  Organizer Dashboard
                </h1>
                <p className="text-lg text-gray-600">
                  Manage your events and track performance
                </p>
              </div>
              <Button onClick={() => navigate('/create-event')} className="flex items-center space-x-2">
                <Plus className="h-4 w-4" />
                <span>Create Event</span>
              </Button>
            </div>

            {/* Success/Error Messages */}
            {message && (
              <Alert className={`mb-6 ${message.type === 'success' ? 'border-green-200 bg-green-50' : 'border-red-200 bg-red-50'}`}>
                <AlertDescription className={message.type === 'success' ? 'text-green-700' : 'text-red-700'}>
                  {message.text}
                </AlertDescription>
              </Alert>
            )}

            <Tabs value={activeTab} onValueChange={setActiveTab}>
              <TabsList className="grid w-full grid-cols-3">
                <TabsTrigger value="overview">Overview</TabsTrigger>
                <TabsTrigger value="events">My Events</TabsTrigger>
                <TabsTrigger value="analytics">Analytics</TabsTrigger>
              </TabsList>

              {/* Overview Tab */}
              <TabsContent value="overview" className="space-y-6">
                {stats && (
                  <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
                    <Card>
                      <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                        <CardTitle className="text-sm font-medium">Total Events</CardTitle>
                        <Calendar className="h-4 w-4 text-muted-foreground" />
                      </CardHeader>
                      <CardContent>
                        <div className="text-2xl font-bold">{stats.events.total}</div>
                      </CardContent>
                    </Card>

                    <Card>
                      <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                        <CardTitle className="text-sm font-medium">Pending Review</CardTitle>
                        <AlertCircle className="h-4 w-4 text-yellow-500" />
                      </CardHeader>
                      <CardContent>
                        <div className="text-2xl font-bold">{stats.events.pending}</div>
                      </CardContent>
                    </Card>

                    <Card>
                      <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                        <CardTitle className="text-sm font-medium">Total Bookings</CardTitle>
                        <Users className="h-4 w-4 text-muted-foreground" />
                      </CardHeader>
                      <CardContent>
                        <div className="text-2xl font-bold">{stats.bookings.total_bookings}</div>
                      </CardContent>
                    </Card>

                    <Card>
                      <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                        <CardTitle className="text-sm font-medium">Your Revenue</CardTitle>
                        <DollarSign className="h-4 w-4 text-green-500" />
                      </CardHeader>
                      <CardContent>
                        <div className="text-2xl font-bold">{formatCurrency(stats.bookings.organizer_revenue)}</div>
                        <p className="text-xs text-muted-foreground">
                          Platform fee: {formatCurrency(stats.bookings.platform_commission)}
                        </p>
                      </CardContent>
                    </Card>
                  </div>
                )}

                {/* Recent Events */}
                <Card>
                  <CardHeader>
                    <CardTitle>Recent Events</CardTitle>
                  </CardHeader>
                  <CardContent>
                    {events.length === 0 ? (
                      <div className="text-center py-8">
                        <Calendar className="h-12 w-12 text-gray-400 mx-auto mb-4" />
                        <h3 className="text-lg font-medium text-gray-900 mb-2">No events yet</h3>
                        <p className="text-gray-600 mb-4">Get started by creating your first event</p>
                        <Button onClick={() => navigate('/create-event')}>
                          <Plus className="h-4 w-4 mr-2" />
                          Create Event
                        </Button>
                      </div>
                    ) : (
                      <div className="space-y-4">
                        {events.slice(0, 5).map((event) => (
                          <div key={event.id} className="flex items-center justify-between p-4 border rounded-lg">
                            <div className="flex-1">
                              <h4 className="font-medium">{event.title}</h4>
                              <div className="flex items-center space-x-4 text-sm text-gray-600 mt-1">
                                <span className="flex items-center">
                                  <Calendar className="h-3 w-3 mr-1" />
                                  {formatDate(event.date)}
                                </span>
                                <span className="flex items-center">
                                  <Clock className="h-3 w-3 mr-1" />
                                  {event.time}
                                </span>
                                <span className="flex items-center">
                                  <Eye className="h-3 w-3 mr-1" />
                                  {event.view_count} views
                                </span>
                              </div>
                            </div>
                            <div className="flex items-center space-x-2">
                              {getStatusBadge(event.approval_status)}
                              {getEventStatusBadge(event.event_status)}
                            </div>
                          </div>
                        ))}
                      </div>
                    )}
                  </CardContent>
                </Card>
              </TabsContent>

              {/* Events Tab */}
              <TabsContent value="events" className="space-y-6">
                <Card>
                  <CardHeader>
                    <CardTitle>All Events</CardTitle>
                  </CardHeader>
                  <CardContent>
                    {events.length === 0 ? (
                      <div className="text-center py-8">
                        <Calendar className="h-12 w-12 text-gray-400 mx-auto mb-4" />
                        <h3 className="text-lg font-medium text-gray-900 mb-2">No events yet</h3>
                        <p className="text-gray-600 mb-4">Get started by creating your first event</p>
                        <Button onClick={() => navigate('/create-event')}>
                          <Plus className="h-4 w-4 mr-2" />
                          Create Event
                        </Button>
                      </div>
                    ) : (
                      <div className="space-y-4">
                        {events.map((event) => (
                          <div key={event.id} className="border rounded-lg p-6">
                            <div className="flex justify-between items-start mb-4">
                              <div className="flex-1">
                                <h3 className="text-lg font-semibold mb-2">{event.title}</h3>
                                <div className="flex flex-wrap items-center gap-4 text-sm text-gray-600">
                                  <span className="flex items-center">
                                    <Calendar className="h-4 w-4 mr-1" />
                                    {formatDate(event.date)} at {event.time}
                                  </span>
                                  <span className="flex items-center">
                                    <MapPin className="h-4 w-4 mr-1" />
                                    {event.location}
                                  </span>
                                  {event.category && (
                                    <Badge variant="outline">{event.category.name}</Badge>
                                  )}
                                  {event.venue && (
                                    <span className="text-xs">Venue: {event.venue.name}</span>
                                  )}
                                </div>
                              </div>
                              <div className="flex items-center space-x-2">
                                {getStatusBadge(event.approval_status)}
                                {getEventStatusBadge(event.event_status)}
                              </div>
                            </div>

                            <div className="flex justify-between items-center">
                              <div className="flex items-center space-x-4 text-sm text-gray-600">
                                <span className="flex items-center">
                                  <Eye className="h-4 w-4 mr-1" />
                                  {event.view_count} views
                                </span>
                                <span>
                                  {event.ticket_types_count} ticket type{event.ticket_types_count !== 1 ? 's' : ''}
                                </span>
                                <span>
                                  Created {formatDate(event.created_at)}
                                </span>
                              </div>
                              
                              <div className="flex space-x-2">
                                <Button
                                  variant="outline"
                                  size="sm"
                                  onClick={() => navigate(`/events/${event.id}`)}
                                >
                                  <Eye className="h-4 w-4 mr-1" />
                                  View
                                </Button>
                                {(event.approval_status === 'pending' || event.approval_status === 'rejected') && (
                                  <Button
                                    variant="outline"
                                    size="sm"
                                    onClick={() => navigate(`/edit-event/${event.id}`)}
                                  >
                                    <Edit className="h-4 w-4 mr-1" />
                                    Edit
                                  </Button>
                                )}
                              </div>
                            </div>
                          </div>
                        ))}
                      </div>
                    )}
                  </CardContent>
                </Card>
              </TabsContent>

              {/* Analytics Tab */}
              <TabsContent value="analytics" className="space-y-6">
                {analyticsLoading && (
                  <div className="flex justify-center items-center h-32">
                    <div className="animate-spin rounded-full h-8 w-8 border-4 border-navy-blue border-t-transparent"></div>
                  </div>
                )}

                {/* Revenue Overview Cards */}
                {stats && (
                  <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
                    <Card>
                      <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                        <CardTitle className="text-sm font-medium">Total Revenue</CardTitle>
                        <DollarSign className="h-4 w-4 text-muted-foreground" />
                      </CardHeader>
                      <CardContent>
                        <div className="text-2xl font-bold">{formatCurrency(stats.bookings.total_revenue)}</div>
                        <p className="text-xs text-muted-foreground">
                          From {stats.bookings.total_bookings} bookings
                        </p>
                      </CardContent>
                    </Card>

                    <Card>
                      <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                        <CardTitle className="text-sm font-medium">Your Revenue</CardTitle>
                        <TrendingUp className="h-4 w-4 text-green-500" />
                      </CardHeader>
                      <CardContent>
                        <div className="text-2xl font-bold text-green-600">{formatCurrency(stats.bookings.organizer_revenue)}</div>
                        <p className="text-xs text-muted-foreground">
                          After 5% platform fee
                        </p>
                      </CardContent>
                    </Card>

                    <Card>
                      <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                        <CardTitle className="text-sm font-medium">Conversion Rate</CardTitle>
                        <Target className="h-4 w-4 text-muted-foreground" />
                      </CardHeader>
                      <CardContent>
                        <div className="text-2xl font-bold">
                          {conversionMetrics ? `${conversionMetrics.overall_conversion_rate}%` : '0%'}
                        </div>
                        <p className="text-xs text-muted-foreground">
                          Views to bookings
                        </p>
                      </CardContent>
                    </Card>

                    <Card>
                      <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                        <CardTitle className="text-sm font-medium">Active Events</CardTitle>
                        <Activity className="h-4 w-4 text-muted-foreground" />
                      </CardHeader>
                      <CardContent>
                        <div className="text-2xl font-bold">{stats.events.approved}</div>
                        <p className="text-xs text-muted-foreground">
                          {stats.events.pending} pending review
                        </p>
                      </CardContent>
                    </Card>
                  </div>
                )}

                {/* Revenue Trends Chart */}
                <Card>
                  <CardHeader>
                    <div className="flex items-center justify-between">
                      <CardTitle className="flex items-center space-x-2">
                        <BarChart3 className="h-5 w-5" />
                        <span>Revenue Trends</span>
                      </CardTitle>
                      <Select value={revenuePeriod} onValueChange={setRevenuePeriod}>
                        <SelectTrigger className="w-32">
                          <SelectValue />
                        </SelectTrigger>
                        <SelectContent>
                          <SelectItem value="week">Weekly</SelectItem>
                          <SelectItem value="month">Monthly</SelectItem>
                          <SelectItem value="quarter">Quarterly</SelectItem>
                          <SelectItem value="year">Yearly</SelectItem>
                        </SelectContent>
                      </Select>
                    </div>
                  </CardHeader>
                  <CardContent>
                    {revenueTrends.length > 0 ? (
                      <ChartContainer config={chartConfig} className="h-[400px]">
                        <AreaChart data={revenueTrends.map(trend => ({
                          ...trend,
                          period_label: formatPeriodLabel(trend.period)
                        }))}>
                          <CartesianGrid strokeDasharray="3 3" />
                          <XAxis dataKey="period_label" />
                          <YAxis />
                          <ChartTooltip 
                            content={<ChartTooltipContent />}
                            formatter={(value, name) => [
                              name === 'booking_count' ? `${value} bookings` : formatCurrency(Number(value)),
                              name === 'total_revenue' ? 'Total Revenue' :
                              name === 'organizer_revenue' ? 'Your Revenue' :
                              name === 'commission' ? 'Platform Fee' : 'Bookings'
                            ]}
                          />
                          <Area 
                            type="monotone" 
                            dataKey="total_revenue" 
                            stackId="1"
                            stroke="#3b82f6" 
                            fill="#3b82f6" 
                            fillOpacity={0.6} 
                          />
                          <Area 
                            type="monotone" 
                            dataKey="organizer_revenue" 
                            stackId="2"
                            stroke="#10b981" 
                            fill="#10b981" 
                            fillOpacity={0.6} 
                          />
                          <ChartLegend content={<ChartLegendContent />} />
                        </AreaChart>
                      </ChartContainer>
                    ) : (
                      <div className="h-[400px] flex items-center justify-center text-gray-500">
                        No revenue data available for the selected period
                      </div>
                    )}
                  </CardContent>
                </Card>

                {/* Event Performance Chart */}
                <Card>
                  <CardHeader>
                    <CardTitle className="flex items-center space-x-2">
                      <BarChart3 className="h-5 w-5" />
                      <span>Event Performance</span>
                    </CardTitle>
                  </CardHeader>
                  <CardContent>
                    {eventPerformance.length > 0 ? (
                      <ChartContainer config={chartConfig} className="h-[400px]">
                        <BarChart data={eventPerformance.slice(0, 10)}>
                          <CartesianGrid strokeDasharray="3 3" />
                          <XAxis 
                            dataKey="title" 
                            angle={-45}
                            textAnchor="end"
                            height={120}
                            interval={0}
                          />
                          <YAxis />
                          <ChartTooltip 
                            content={<ChartTooltipContent />}
                            formatter={(value, name) => [
                              name === 'total_bookings' || name === 'tickets_sold' || name === 'view_count' 
                                ? `${value}` 
                                : formatCurrency(Number(value)),
                              name === 'total_revenue' ? 'Total Revenue' :
                              name === 'organizer_revenue' ? 'Your Revenue' :
                              name === 'total_bookings' ? 'Bookings' :
                              name === 'tickets_sold' ? 'Tickets Sold' :
                              name === 'view_count' ? 'Views' : name
                            ]}
                          />
                          <Bar dataKey="organizer_revenue" fill="#10b981" />
                          <ChartLegend content={<ChartLegendContent />} />
                        </BarChart>
                      </ChartContainer>
                    ) : (
                      <div className="h-[400px] flex items-center justify-center text-gray-500">
                        No event performance data available
                      </div>
                    )}
                  </CardContent>
                </Card>

                {/* Ticket Types Analytics */}
                {ticketAnalytics.length > 0 && (
                  <Card>
                    <CardHeader>
                      <CardTitle className="flex items-center space-x-2">
                        <PieChartIcon className="h-5 w-5" />
                        <span>Ticket Types Performance</span>
                      </CardTitle>
                    </CardHeader>
                    <CardContent>
                      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                        <ChartContainer config={chartConfig} className="h-[300px]">
                          <PieChart>
                            <Pie
                              data={ticketAnalytics}
                              dataKey="total_revenue"
                              nameKey="name"
                              cx="50%"
                              cy="50%"
                              outerRadius={80}
                              label={({ name, value }) => `${name}: ${formatCurrency(value)}`}
                            >
                              {ticketAnalytics.map((entry, index) => (
                                <Cell key={`cell-${index}`} fill={chartColors[index % chartColors.length]} />
                              ))}
                            </Pie>
                            <ChartTooltip 
                              content={<ChartTooltipContent />}
                              formatter={(value) => [formatCurrency(Number(value)), 'Revenue']}
                            />
                          </PieChart>
                        </ChartContainer>
                        
                        <div className="space-y-4">
                          {ticketAnalytics.map((ticket, index) => (
                            <div key={ticket.name} className="flex items-center justify-between p-3 border rounded-lg">
                              <div className="flex items-center space-x-3">
                                <div 
                                  className="w-4 h-4 rounded" 
                                  style={{ backgroundColor: chartColors[index % chartColors.length] }}
                                />
                                <div>
                                  <div className="font-medium">{ticket.name}</div>
                                  <div className="text-sm text-gray-600">
                                    {formatCurrency(ticket.price)} • {ticket.sold_percentage}% sold
                                  </div>
                                </div>
                              </div>
                              <div className="text-right">
                                <div className="font-semibold">{formatCurrency(ticket.organizer_revenue)}</div>
                                <div className="text-sm text-gray-600">{ticket.tickets_sold} sold</div>
                              </div>
                            </div>
                          ))}
                        </div>
                      </div>
                    </CardContent>
                  </Card>
                )}

                {/* Geographic Revenue */}
                {geographicRevenue.length > 0 && (
                  <Card>
                    <CardHeader>
                      <CardTitle className="flex items-center space-x-2">
                        <MapPin className="h-5 w-5" />
                        <span>Revenue by Location</span>
                      </CardTitle>
                    </CardHeader>
                    <CardContent>
                      <div className="space-y-4">
                        {geographicRevenue.map((location, index) => (
                          <div key={location.location} className="flex items-center justify-between p-4 border rounded-lg">
                            <div>
                              <div className="font-medium">{location.location}</div>
                              <div className="text-sm text-gray-600">
                                {location.event_count} events • {location.total_bookings} bookings
                              </div>
                            </div>
                            <div className="text-right">
                              <div className="font-semibold">{formatCurrency(location.organizer_revenue)}</div>
                              <div className="text-sm text-gray-600">
                                Avg: {formatCurrency(location.avg_revenue_per_event)}/event
                              </div>
                            </div>
                          </div>
                        ))}
                      </div>
                    </CardContent>
                  </Card>
                )}

                {/* Conversion Metrics */}
                {conversionMetrics && (
                  <Card>
                    <CardHeader>
                      <CardTitle className="flex items-center space-x-2">
                        <Target className="h-5 w-5" />
                        <span>Conversion Analytics</span>
                      </CardTitle>
                    </CardHeader>
                    <CardContent>
                      <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-6">
                        <div className="text-center p-4 bg-blue-50 rounded-lg">
                          <div className="text-2xl font-bold text-blue-600">
                            {conversionMetrics.overall_conversion_rate}%
                          </div>
                          <div className="text-sm text-gray-600">Overall Conversion Rate</div>
                        </div>
                        <div className="text-center p-4 bg-gray-50 rounded-lg">
                          <div className="text-2xl font-bold text-gray-900">
                            {conversionMetrics.total_views.toLocaleString()}
                          </div>
                          <div className="text-sm text-gray-600">Total Views</div>
                        </div>
                        <div className="text-center p-4 bg-green-50 rounded-lg">
                          <div className="text-2xl font-bold text-green-600">
                            {conversionMetrics.total_bookings.toLocaleString()}
                          </div>
                          <div className="text-sm text-gray-600">Total Bookings</div>
                        </div>
                      </div>

                      {conversionMetrics.conversion_by_status.length > 0 && (
                        <div>
                          <h4 className="font-medium mb-4">Conversion by Event Status</h4>
                          <div className="space-y-3">
                            {conversionMetrics.conversion_by_status.map((status) => (
                              <div key={status.status} className="flex items-center justify-between p-3 border rounded-lg">
                                <div>
                                  <div className="font-medium capitalize">{status.status.replace('_', ' ')}</div>
                                  <div className="text-sm text-gray-600">
                                    {status.views} views • {status.bookings} bookings
                                  </div>
                                </div>
                                <div className="text-right">
                                  <div className="font-semibold">{status.conversion_rate}%</div>
                                  <div className="text-sm text-gray-600">conversion</div>
                                </div>
                              </div>
                            ))}
                          </div>
                        </div>
                      )}
                    </CardContent>
                  </Card>
                )}
              </TabsContent>
            </Tabs>
          </div>
        </main>

        <Footer />
      </div>
    </PageTransition>
  );
};

export default OrganizerDashboard;