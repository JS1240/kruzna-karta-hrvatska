import React, { useState, useEffect } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Badge } from '@/components/ui/badge';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { 
  QrCode, 
  Scan, 
  CheckCircle, 
  AlertCircle, 
  User, 
  Ticket,
  Search,
  Clock,
  Users,
  TrendingUp,
  Camera,
  RefreshCw
} from 'lucide-react';
import { toast } from '@/hooks/use-toast';

interface CheckInAttempt {
  id: string;
  timestamp: string;
  ticketId: string;
  attendeeName: string;
  status: 'success' | 'error' | 'duplicate';
  message: string;
}

interface CheckInStats {
  totalExpected: number;
  checkedIn: number;
  pending: number;
  checkInRate: number;
  lastCheckIn?: string;
}

interface EventCheckInProps {
  eventId: string;
  eventTitle: string;
  eventDate: string;
  eventTime: string;
}

const EventCheckIn: React.FC<EventCheckInProps> = ({
  eventId,
  eventTitle,
  eventDate,
  eventTime,
}) => {
  const [scannerActive, setScannerActive] = useState(false);
  const [manualInput, setManualInput] = useState('');
  const [checkInHistory, setCheckInHistory] = useState<CheckInAttempt[]>([]);
  const [stats, setStats] = useState<CheckInStats>({
    totalExpected: 267,
    checkedIn: 45,
    pending: 222,
    checkInRate: 16.9,
    lastCheckIn: '2025-08-15T19:15:00Z',
  });
  const [loading, setLoading] = useState(false);

  // Mock attendee database for check-in validation
  const mockAttendees = new Map([
    ['QR123456789', { id: '1', name: 'Ana Marić', ticketType: 'VIP', checkedIn: false }],
    ['QR123456790', { id: '2', name: 'Marko Kovač', ticketType: 'Standard', checkedIn: false }],
    ['QR123456791', { id: '3', name: 'Petra Novak', ticketType: 'Standard', checkedIn: true }],
    ['QR123456792', { id: '4', name: 'Ivo Petrić', ticketType: 'Early Bird', checkedIn: false }],
    ['BK20250001', { id: '1', name: 'Ana Marić', ticketType: 'VIP', checkedIn: false }],
    ['BK20250002', { id: '2', name: 'Marko Kovač', ticketType: 'Standard', checkedIn: false }],
    ['BK20250003', { id: '3', name: 'Petra Novak', ticketType: 'Standard', checkedIn: true }],
    ['BK20250004', { id: '4', name: 'Ivo Petrić', ticketType: 'Early Bird', checkedIn: false }],
  ]);

  const validateAndCheckIn = (code: string): CheckInAttempt => {
    const cleanCode = code.trim().toUpperCase();
    const attendee = mockAttendees.get(cleanCode);
    
    if (!attendee) {
      return {
        id: Date.now().toString(),
        timestamp: new Date().toISOString(),
        ticketId: cleanCode,
        attendeeName: 'Unknown',
        status: 'error',
        message: 'Invalid ticket code',
      };
    }

    if (attendee.checkedIn) {
      return {
        id: Date.now().toString(),
        timestamp: new Date().toISOString(),
        ticketId: cleanCode,
        attendeeName: attendee.name,
        status: 'duplicate',
        message: 'Already checked in',
      };
    }

    // Mark as checked in
    mockAttendees.set(cleanCode, { ...attendee, checkedIn: true });

    return {
      id: Date.now().toString(),
      timestamp: new Date().toISOString(),
      ticketId: cleanCode,
      attendeeName: attendee.name,
      status: 'success',
      message: 'Successfully checked in',
    };
  };

  const handleManualCheckIn = () => {
    if (!manualInput.trim()) {
      toast({
        title: "Invalid input",
        description: "Please enter a booking reference or QR code",
        variant: "destructive",
      });
      return;
    }

    setLoading(true);
    
    // Simulate processing delay
    setTimeout(() => {
      const result = validateAndCheckIn(manualInput);
      
      setCheckInHistory(prev => [result, ...prev.slice(0, 9)]); // Keep last 10 attempts
      
      if (result.status === 'success') {
        setStats(prev => ({
          ...prev,
          checkedIn: prev.checkedIn + 1,
          pending: prev.pending - 1,
          checkInRate: ((prev.checkedIn + 1) / prev.totalExpected) * 100,
          lastCheckIn: result.timestamp,
        }));
        
        toast({
          title: "Check-in successful!",
          description: `${result.attendeeName} has been checked in.`,
        });
      } else if (result.status === 'duplicate') {
        toast({
          title: "Already checked in",
          description: `${result.attendeeName} is already checked in.`,
          variant: "destructive",
        });
      } else {
        toast({
          title: "Check-in failed",
          description: result.message,
          variant: "destructive",
        });
      }
      
      setManualInput('');
      setLoading(false);
    }, 500);
  };

  const startQRScanner = () => {
    setScannerActive(true);
    
    // Simulate QR scanner
    toast({
      title: "QR Scanner activated",
      description: "Point your camera at the QR code to scan",
    });

    // Mock QR code detection after 3 seconds
    setTimeout(() => {
      const mockQRCode = 'QR123456792'; // Simulate scanning Ivo's ticket
      const result = validateAndCheckIn(mockQRCode);
      
      setCheckInHistory(prev => [result, ...prev.slice(0, 9)]);
      
      if (result.status === 'success') {
        setStats(prev => ({
          ...prev,
          checkedIn: prev.checkedIn + 1,
          pending: prev.pending - 1,
          checkInRate: ((prev.checkedIn + 1) / prev.totalExpected) * 100,
          lastCheckIn: result.timestamp,
        }));
        
        toast({
          title: "QR scan successful!",
          description: `${result.attendeeName} has been checked in.`,
        });
      }
      
      setScannerActive(false);
    }, 3000);
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'success':
        return 'bg-green-100 text-green-800 border-green-200';
      case 'error':
        return 'bg-red-100 text-red-800 border-red-200';
      case 'duplicate':
        return 'bg-yellow-100 text-yellow-800 border-yellow-200';
      default:
        return 'bg-gray-100 text-gray-800 border-gray-200';
    }
  };

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'success':
        return <CheckCircle className="h-4 w-4" />;
      case 'error':
      case 'duplicate':
        return <AlertCircle className="h-4 w-4" />;
      default:
        return <RefreshCw className="h-4 w-4" />;
    }
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div>
        <h2 className="text-2xl font-bold text-navy-blue mb-2">Event Check-in</h2>
        <div className="flex items-center gap-4 text-sm text-gray-600">
          <span>{eventTitle}</span>
          <span>•</span>
          <span>{new Date(eventDate + 'T' + eventTime).toLocaleDateString()} at {eventTime}</span>
        </div>
      </div>

      {/* Statistics */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <Card>
          <CardContent className="pt-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-gray-600">Expected</p>
                <p className="text-2xl font-bold">{stats.totalExpected}</p>
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
              <CheckCircle className="h-8 w-8 text-green-500" />
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
                <p className="text-sm font-medium text-gray-600">Check-in Rate</p>
                <p className="text-2xl font-bold">{stats.checkInRate.toFixed(1)}%</p>
              </div>
              <TrendingUp className="h-8 w-8 text-blue-500" />
            </div>
          </CardContent>
        </Card>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Check-in Methods */}
        <div className="space-y-6">
          {/* QR Scanner */}
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <QrCode className="h-5 w-5" />
                QR Code Scanner
              </CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="text-center">
                {scannerActive ? (
                  <div className="space-y-4">
                    <div className="w-48 h-48 mx-auto bg-gray-100 rounded-lg flex items-center justify-center border-2 border-dashed border-gray-300">
                      <div className="text-center">
                        <Camera className="h-12 w-12 mx-auto text-gray-400 mb-2 animate-pulse" />
                        <p className="text-sm text-gray-600">Scanning for QR code...</p>
                      </div>
                    </div>
                    <Button
                      variant="outline"
                      onClick={() => setScannerActive(false)}
                    >
                      Stop Scanner
                    </Button>
                  </div>
                ) : (
                  <div className="space-y-4">
                    <div className="w-48 h-48 mx-auto bg-gray-50 rounded-lg flex items-center justify-center">
                      <QrCode className="h-16 w-16 text-gray-400" />
                    </div>
                    <Button
                      onClick={startQRScanner}
                      className="gap-2"
                      size="lg"
                    >
                      <Scan className="h-4 w-4" />
                      Start QR Scanner
                    </Button>
                  </div>
                )}
              </div>
            </CardContent>
          </Card>

          {/* Manual Check-in */}
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Search className="h-5 w-5" />
                Manual Check-in
              </CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              <div>
                <Input
                  placeholder="Enter booking reference or QR code"
                  value={manualInput}
                  onChange={(e) => setManualInput(e.target.value)}
                  onKeyPress={(e) => {
                    if (e.key === 'Enter' && !loading) {
                      handleManualCheckIn();
                    }
                  }}
                  disabled={loading}
                />
              </div>
              <Button
                onClick={handleManualCheckIn}
                disabled={!manualInput.trim() || loading}
                className="w-full gap-2"
              >
                {loading ? (
                  <RefreshCw className="h-4 w-4 animate-spin" />
                ) : (
                  <CheckCircle className="h-4 w-4" />
                )}
                {loading ? 'Processing...' : 'Check In'}
              </Button>
              
              <div className="text-center">
                <p className="text-xs text-gray-500">
                  Try: BK20250001, BK20250002, QR123456789, or QR123456790
                </p>
              </div>
            </CardContent>
          </Card>
        </div>

        {/* Check-in History */}
        <div>
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Clock className="h-5 w-5" />
                Recent Check-ins
              </CardTitle>
            </CardHeader>
            <CardContent>
              {checkInHistory.length === 0 ? (
                <div className="text-center py-8">
                  <Ticket className="h-12 w-12 mx-auto text-gray-400 mb-4" />
                  <p className="text-gray-600">No check-ins yet</p>
                  <p className="text-sm text-gray-500">
                    Check-in attempts will appear here
                  </p>
                </div>
              ) : (
                <div className="space-y-3 max-h-96 overflow-y-auto">
                  {checkInHistory.map((attempt) => (
                    <Alert key={attempt.id} className={getStatusColor(attempt.status)}>
                      <div className="flex items-center gap-2">
                        {getStatusIcon(attempt.status)}
                        <AlertDescription className="flex-1">
                          <div className="flex items-center justify-between">
                            <div>
                              <span className="font-medium">{attempt.attendeeName}</span>
                              <span className="text-xs block">{attempt.ticketId}</span>
                            </div>
                            <div className="text-right">
                              <div className="text-xs">
                                {new Date(attempt.timestamp).toLocaleTimeString()}
                              </div>
                              <Badge
                                variant="outline"
                                className={`text-xs ${
                                  attempt.status === 'success'
                                    ? 'border-green-500 text-green-700'
                                    : attempt.status === 'duplicate'
                                    ? 'border-yellow-500 text-yellow-700'
                                    : 'border-red-500 text-red-700'
                                }`}
                              >
                                {attempt.message}
                              </Badge>
                            </div>
                          </div>
                        </AlertDescription>
                      </div>
                    </Alert>
                  ))}
                </div>
              )}
            </CardContent>
          </Card>
        </div>
      </div>

      {/* Quick Stats */}
      {stats.lastCheckIn && (
        <Card>
          <CardContent className="pt-6">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2">
                <User className="h-5 w-5 text-gray-500" />
                <span className="text-sm text-gray-600">
                  Last check-in: {new Date(stats.lastCheckIn).toLocaleTimeString()}
                </span>
              </div>
              <div className="text-sm text-gray-600">
                Progress: {stats.checkedIn} / {stats.totalExpected} attendees
              </div>
            </div>
            <div className="mt-3">
              <div className="w-full bg-gray-200 rounded-full h-2">
                <div
                  className="bg-green-500 h-2 rounded-full transition-all duration-300"
                  style={{ width: `${Math.min(stats.checkInRate, 100)}%` }}
                />
              </div>
            </div>
          </CardContent>
        </Card>
      )}
    </div>
  );
};

export default EventCheckIn;