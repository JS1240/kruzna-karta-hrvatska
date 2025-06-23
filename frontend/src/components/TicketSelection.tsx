import React, { useState } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { 
  Plus, 
  Minus, 
  Clock, 
  Users, 
  AlertTriangle, 
  CheckCircle,
  Euro,
  Ticket,
  Calendar
} from 'lucide-react';
import { toast } from '@/hooks/use-toast';

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
  date: string;
  time: string;
  ticketTypes: TicketType[];
}

interface TicketSelectionProps {
  event: Event;
  onBookingStart: (selectedTickets: Array<{ ticketType: TicketType; quantity: number }>) => void;
}

interface SelectedTicket {
  ticketTypeId: string;
  quantity: number;
}

const TicketSelection: React.FC<TicketSelectionProps> = ({ event, onBookingStart }) => {
  const [selectedTickets, setSelectedTickets] = useState<SelectedTicket[]>([]);
  const [promoCode, setPromoCode] = useState('');

  const updateTicketQuantity = (ticketTypeId: string, quantity: number) => {
    const ticketType = event.ticketTypes.find(tt => tt.id === ticketTypeId);
    if (!ticketType) return;

    // Validate quantity constraints
    if (quantity < 0) quantity = 0;
    if (quantity > ticketType.max_purchase) quantity = ticketType.max_purchase;
    if (quantity > ticketType.available_quantity) quantity = ticketType.available_quantity;

    setSelectedTickets(prev => {
      const existing = prev.find(st => st.ticketTypeId === ticketTypeId);
      if (existing) {
        if (quantity === 0) {
          return prev.filter(st => st.ticketTypeId !== ticketTypeId);
        }
        return prev.map(st => 
          st.ticketTypeId === ticketTypeId 
            ? { ...st, quantity }
            : st
        );
      } else if (quantity > 0) {
        return [...prev, { ticketTypeId, quantity }];
      }
      return prev;
    });
  };

  const getTicketQuantity = (ticketTypeId: string): number => {
    const selected = selectedTickets.find(st => st.ticketTypeId === ticketTypeId);
    return selected ? selected.quantity : 0;
  };

  const isTicketTypeAvailable = (ticketType: TicketType): boolean => {
    const now = new Date();
    
    if (ticketType.available_quantity === 0) return false;
    
    if (ticketType.sale_start_date && new Date(ticketType.sale_start_date) > now) {
      return false;
    }
    
    if (ticketType.sale_end_date && new Date(ticketType.sale_end_date) < now) {
      return false;
    }
    
    return true;
  };

  const getTicketTypeStatus = (ticketType: TicketType): { status: string; message: string; variant: string } => {
    const now = new Date();
    
    if (ticketType.available_quantity === 0) {
      return { status: 'sold-out', message: 'Sold Out', variant: 'destructive' };
    }
    
    if (ticketType.sale_start_date && new Date(ticketType.sale_start_date) > now) {
      return { 
        status: 'not-yet-available', 
        message: `Available from ${new Date(ticketType.sale_start_date).toLocaleDateString()}`,
        variant: 'secondary'
      };
    }
    
    if (ticketType.sale_end_date && new Date(ticketType.sale_end_date) < now) {
      return { status: 'expired', message: 'Sales Ended', variant: 'destructive' };
    }
    
    if (ticketType.available_quantity < 10) {
      return { status: 'limited', message: `Only ${ticketType.available_quantity} left`, variant: 'destructive' };
    }
    
    return { status: 'available', message: 'Available', variant: 'default' };
  };

  const calculateTotal = (): number => {
    return selectedTickets.reduce((total, selected) => {
      const ticketType = event.ticketTypes.find(tt => tt.id === selected.ticketTypeId);
      return total + (ticketType ? ticketType.price * selected.quantity : 0);
    }, 0);
  };

  const getTotalTickets = (): number => {
    return selectedTickets.reduce((total, selected) => total + selected.quantity, 0);
  };

  const handleContinueToCheckout = () => {
    if (selectedTickets.length === 0) {
      toast({
        title: "No tickets selected",
        description: "Please select at least one ticket to continue.",
        variant: "destructive",
      });
      return;
    }

    // Validate minimum purchase requirements
    for (const selected of selectedTickets) {
      const ticketType = event.ticketTypes.find(tt => tt.id === selected.ticketTypeId);
      if (ticketType && selected.quantity < ticketType.min_purchase) {
        toast({
          title: "Minimum purchase requirement",
          description: `${ticketType.name} requires a minimum of ${ticketType.min_purchase} ticket(s).`,
          variant: "destructive",
        });
        return;
      }
    }

    const selectedTicketData = selectedTickets.map(selected => {
      const ticketType = event.ticketTypes.find(tt => tt.id === selected.ticketTypeId)!;
      return { ticketType, quantity: selected.quantity };
    });

    onBookingStart(selectedTicketData);
  };

  const applyPromoCode = () => {
    if (!promoCode.trim()) {
      toast({
        title: "Enter promo code",
        description: "Please enter a promo code to apply.",
        variant: "destructive",
      });
      return;
    }

    // Mock promo code validation
    if (promoCode.toUpperCase() === 'EARLYBIRD10') {
      toast({
        title: "Promo code applied",
        description: "10% discount has been applied to your order!",
      });
    } else {
      toast({
        title: "Invalid promo code",
        description: "The promo code you entered is not valid.",
        variant: "destructive",
      });
    }
  };

  return (
    <div className="space-y-6">
      {/* Event Info Summary */}
      <Card>
        <CardContent className="pt-6">
          <div className="flex items-center gap-4 text-sm text-gray-600">
            <div className="flex items-center gap-1">
              <Calendar className="h-4 w-4" />
              {new Date(event.date + 'T' + event.time).toLocaleDateString('en-US', { 
                weekday: 'long', 
                month: 'long', 
                day: 'numeric',
                year: 'numeric'
              })}
            </div>
            <div className="flex items-center gap-1">
              <Clock className="h-4 w-4" />
              {event.time}
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Ticket Types */}
      <div className="space-y-4">
        <h3 className="text-lg font-semibold">Select Tickets</h3>
        
        {event.ticketTypes.map((ticketType) => {
          const isAvailable = isTicketTypeAvailable(ticketType);
          const status = getTicketTypeStatus(ticketType);
          const selectedQuantity = getTicketQuantity(ticketType.id);

          return (
            <Card key={ticketType.id} className={`${!isAvailable ? 'opacity-60' : ''}`}>
              <CardContent className="pt-6">
                <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
                  {/* Ticket Info */}
                  <div className="flex-1">
                    <div className="flex items-center gap-3 mb-2">
                      <h4 className="font-semibold text-lg">{ticketType.name}</h4>
                      <Badge 
                        variant={status.variant as any}
                        className="text-xs"
                      >
                        {status.message}
                      </Badge>
                    </div>
                    
                    <p className="text-gray-600 text-sm mb-3">{ticketType.description}</p>
                    
                    <div className="flex items-center gap-4 text-sm text-gray-500">
                      <div className="flex items-center gap-1">
                        <Euro className="h-3 w-3" />
                        <span className="font-medium text-lg text-gray-900">
                          {ticketType.price} {ticketType.currency}
                        </span>
                      </div>
                      <div className="flex items-center gap-1">
                        <Users className="h-3 w-3" />
                        <span>{ticketType.available_quantity} available</span>
                      </div>
                      {ticketType.max_purchase > 1 && (
                        <span>Max {ticketType.max_purchase} per order</span>
                      )}
                    </div>
                  </div>

                  {/* Quantity Selector */}
                  <div className="flex items-center gap-3">
                    {isAvailable ? (
                      <>
                        <Button
                          variant="outline"
                          size="sm"
                          onClick={() => updateTicketQuantity(ticketType.id, selectedQuantity - 1)}
                          disabled={selectedQuantity === 0}
                        >
                          <Minus className="h-4 w-4" />
                        </Button>
                        
                        <div className="w-16 text-center">
                          <Input
                            type="number"
                            value={selectedQuantity}
                            onChange={(e) => updateTicketQuantity(ticketType.id, parseInt(e.target.value) || 0)}
                            className="text-center"
                            min="0"
                            max={Math.min(ticketType.max_purchase, ticketType.available_quantity)}
                          />
                        </div>
                        
                        <Button
                          variant="outline"
                          size="sm"
                          onClick={() => updateTicketQuantity(ticketType.id, selectedQuantity + 1)}
                          disabled={selectedQuantity >= Math.min(ticketType.max_purchase, ticketType.available_quantity)}
                        >
                          <Plus className="h-4 w-4" />
                        </Button>
                      </>
                    ) : (
                      <div className="flex items-center gap-2 text-gray-500">
                        <AlertTriangle className="h-4 w-4" />
                        <span className="text-sm">Not Available</span>
                      </div>
                    )}
                  </div>
                </div>

                {selectedQuantity > 0 && (
                  <div className="mt-4 pt-4 border-t bg-blue-50 rounded-lg p-3">
                    <div className="flex justify-between items-center">
                      <span className="text-sm font-medium">
                        {selectedQuantity} × {ticketType.name}
                      </span>
                      <span className="font-semibold">
                        {(ticketType.price * selectedQuantity).toLocaleString()} {ticketType.currency}
                      </span>
                    </div>
                  </div>
                )}
              </CardContent>
            </Card>
          );
        })}
      </div>

      {/* Promo Code */}
      {selectedTickets.length > 0 && (
        <Card>
          <CardContent className="pt-6">
            <Label htmlFor="promo-code" className="text-sm font-medium">
              Promo Code (Optional)
            </Label>
            <div className="flex gap-2 mt-2">
              <Input
                id="promo-code"
                placeholder="Enter promo code"
                value={promoCode}
                onChange={(e) => setPromoCode(e.target.value)}
              />
              <Button variant="outline" onClick={applyPromoCode}>
                Apply
              </Button>
            </div>
          </CardContent>
        </Card>
      )}

      {/* Order Summary */}
      {selectedTickets.length > 0 && (
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Ticket className="h-5 w-5" />
              Order Summary
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-3">
            {selectedTickets.map((selected) => {
              const ticketType = event.ticketTypes.find(tt => tt.id === selected.ticketTypeId)!;
              return (
                <div key={selected.ticketTypeId} className="flex justify-between">
                  <span>{selected.quantity}× {ticketType.name}</span>
                  <span className="font-medium">
                    {(ticketType.price * selected.quantity).toLocaleString()} {ticketType.currency}
                  </span>
                </div>
              );
            })}
            
            <div className="border-t pt-3">
              <div className="flex justify-between text-lg font-bold">
                <span>Total ({getTotalTickets()} ticket{getTotalTickets() !== 1 ? 's' : ''})</span>
                <span>{calculateTotal().toLocaleString()} HRK</span>
              </div>
            </div>

            <Button 
              onClick={handleContinueToCheckout}
              className="w-full mt-4"
              size="lg"
            >
              <CheckCircle className="h-4 w-4 mr-2" />
              Continue to Checkout
            </Button>

            <div className="text-xs text-gray-500 text-center mt-2">
              <p>✓ Secure payment processing</p>
              <p>✓ Instant ticket delivery</p>
            </div>
          </CardContent>
        </Card>
      )}

      {selectedTickets.length === 0 && (
        <Card>
          <CardContent className="py-12 text-center text-gray-500">
            <Ticket className="h-12 w-12 mx-auto mb-4 text-gray-400" />
            <p>Select tickets above to see your order summary</p>
          </CardContent>
        </Card>
      )}
    </div>
  );
};

export default TicketSelection;