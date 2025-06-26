import React from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogTrigger } from '@/components/ui/dialog';
import { 
  QrCode, 
  Download, 
  Share2, 
  Calendar, 
  MapPin, 
  Clock,
  User,
  Ticket,
  Check,
  AlertCircle
} from 'lucide-react';
import { toast } from '@/hooks/use-toast';

interface TicketQRProps {
  ticket: {
    id: string;
    ticketType: string;
    price: number;
    qrCode: string;
    checkedIn: boolean;
    checkedInAt?: string;
  };
  event: {
    title: string;
    date: string;
    time: string;
    venue: string;
    location: string;
  };
  booking: {
    bookingReference: string;
    currency: string;
  };
  holderName: string;
}

const TicketQR: React.FC<TicketQRProps> = ({ ticket, event, booking, holderName }) => {
  // Simple QR code pattern - in real app this would be generated from the qrCode value
  const generateQRPattern = (qrCode: string) => {
    const size = 25; // 25x25 grid
    const pattern = [];
    
    // Generate a pseudo-random pattern based on QR code
    for (let i = 0; i < size; i++) {
      pattern[i] = [];
      for (let j = 0; j < size; j++) {
        // Use the QR code string to generate consistent pattern
        const seed = (qrCode.charCodeAt((i * size + j) % qrCode.length) * (i + 1) * (j + 1)) % 100;
        pattern[i][j] = seed > 50;
      }
    }
    
    return pattern;
  };

  const qrPattern = generateQRPattern(ticket.qrCode);

  const handleDownload = () => {
    toast({
      title: "Ticket downloaded",
      description: "Your mobile ticket has been downloaded as PDF.",
    });
  };

  const handleShare = () => {
    if (navigator.share) {
      navigator.share({
        title: `Ticket for ${event.title}`,
        text: `My ticket for ${event.title}`,
        url: window.location.href,
      });
    } else {
      navigator.clipboard.writeText(window.location.href);
      toast({
        title: "Link copied",
        description: "Ticket link has been copied to clipboard",
      });
    }
  };

  return (
    <Dialog>
      <DialogTrigger asChild>
        <Button variant="outline" size="sm">
          <QrCode className="h-4 w-4 mr-2" />
          Show Ticket
        </Button>
      </DialogTrigger>
      <DialogContent className="max-w-md">
        <DialogHeader>
          <DialogTitle>Mobile Ticket</DialogTitle>
        </DialogHeader>
        
        <div className="space-y-4">
          {/* Ticket Card */}
          <Card className="overflow-hidden bg-gradient-to-br from-navy-blue to-blue-600 text-brand-white">
            <CardHeader className="pb-2">
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-2">
                  <Ticket className="h-5 w-5" />
                  <span className="text-sm font-medium">E-TICKET</span>
                </div>
                {ticket.checkedIn ? (
                  <Badge className="bg-green-500 text-brand-white">
                    <Check className="h-3 w-3 mr-1" />
                    Used
                  </Badge>
                ) : (
                  <Badge variant="accent-gold" className="bg-accent-gold text-brand-black">
                    Valid
                  </Badge>
                )}
              </div>
            </CardHeader>
            
            <CardContent className="space-y-4">
              {/* Event Info */}
              <div>
                <h3 className="font-bold text-lg mb-2">{event.title}</h3>
                <div className="space-y-1 text-sm">
                  <div className="flex items-center gap-2">
                    <Calendar className="h-4 w-4" />
                    {new Date(event.date + 'T' + event.time).toLocaleDateString('en-US', {
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
                </div>
              </div>

              {/* QR Code */}
              <div className="bg-white rounded-lg p-4 flex flex-col items-center">
                <div className="mb-2">
                  <div className="w-32 h-32 bg-black rounded p-2 relative overflow-hidden">
                    {/* Simplified QR code pattern */}
                    <div className="grid grid-cols-8 gap-px h-full">
                      {Array.from({ length: 64 }, (_, i) => (
                        <div
                          key={i}
                          className={`${
                            (ticket.qrCode.charCodeAt(i % ticket.qrCode.length) * (i + 1)) % 100 > 50
                              ? 'bg-white' 
                              : 'bg-black'
                          }`}
                        />
                      ))}
                    </div>
                    {/* Corner markers */}
                    <div className="absolute top-2 left-2 w-6 h-6 border-2 border-white bg-black"></div>
                    <div className="absolute top-2 right-2 w-6 h-6 border-2 border-white bg-black"></div>
                    <div className="absolute bottom-2 left-2 w-6 h-6 border-2 border-white bg-black"></div>
                  </div>
                </div>
                <p className="text-xs text-gray-600 text-center">
                  Show this code at entrance
                </p>
                <p className="text-xs text-gray-500 font-mono mt-1">
                  {ticket.qrCode}
                </p>
              </div>

              {/* Ticket Details */}
              <div className="grid grid-cols-2 gap-4 text-sm">
                <div>
                  <p className="text-blue-200">Ticket Type</p>
                  <p className="font-medium">{ticket.ticketType}</p>
                </div>
                <div>
                  <p className="text-blue-200">Price</p>
                  <p className="font-medium">{ticket.price} {booking.currency}</p>
                </div>
                <div>
                  <p className="text-blue-200">Holder</p>
                  <p className="font-medium">{holderName}</p>
                </div>
                <div>
                  <p className="text-blue-200">Booking Ref</p>
                  <p className="font-medium">{booking.bookingReference}</p>
                </div>
              </div>

              {/* Status */}
              {ticket.checkedIn && ticket.checkedInAt && (
                <div className="bg-green-500/20 border border-green-400 rounded-lg p-3">
                  <div className="flex items-center gap-2 text-green-100">
                    <Check className="h-4 w-4" />
                    <span className="text-sm font-medium">
                      Used on {new Date(ticket.checkedInAt).toLocaleString()}
                    </span>
                  </div>
                </div>
              )}
            </CardContent>
          </Card>

          {/* Important Notice */}
          <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-3">
            <div className="flex items-start gap-2">
              <AlertCircle className="h-4 w-4 text-yellow-600 mt-0.5" />
              <div className="text-sm">
                <p className="font-medium text-yellow-800">Important:</p>
                <ul className="text-yellow-700 mt-1 space-y-1">
                  <li>• Arrive 30 minutes before event start</li>
                  <li>• Valid government ID required</li>
                  <li>• Take screenshot as backup</li>
                  <li>• Do not share or duplicate this ticket</li>
                </ul>
              </div>
            </div>
          </div>

          {/* Actions */}
          <div className="flex gap-2">
            <Button onClick={handleDownload} className="flex-1">
              <Download className="h-4 w-4 mr-2" />
              Download PDF
            </Button>
            <Button variant="outline" onClick={handleShare}>
              <Share2 className="h-4 w-4" />
            </Button>
          </div>
        </div>
      </DialogContent>
    </Dialog>
  );
};

export default TicketQR;