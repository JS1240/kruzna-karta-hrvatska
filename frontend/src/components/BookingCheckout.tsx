import React, { useState } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Textarea } from '@/components/ui/textarea';
import { Checkbox } from '@/components/ui/checkbox';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Dialog, DialogContent, DialogHeader, DialogTitle } from '@/components/ui/dialog';
import { 
  CreditCard, 
  Lock, 
  User, 
  Mail, 
  Phone, 
  MapPin,
  Calendar,
  Ticket,
  Check,
  AlertCircle,
  ArrowLeft,
  Euro
} from 'lucide-react';
import { toast } from '@/hooks/use-toast';
import { getCurrentUser } from '@/lib/auth';
import StripePayment from '@/components/StripePayment';

interface TicketType {
  id: string;
  name: string;
  description: string;
  price: number;
  currency: string;
}

interface SelectedTicket {
  ticketType: TicketType;
  quantity: number;
}

interface Event {
  id: string;
  title: string;
  date: string;
  time: string;
  location: string;
  venue: string;
}

interface BookingCheckoutProps {
  event: Event;
  selectedTickets: SelectedTicket[];
  isOpen: boolean;
  onClose: () => void;
  onBookingComplete: (bookingReference: string) => void;
}

interface BookingForm {
  firstName: string;
  lastName: string;
  email: string;
  phone: string;
  country: string;
  specialRequests: string;
  marketingConsent: boolean;
  termsAccepted: boolean;
  paymentMethod: 'stripe' | 'paypal';
  paymentIntentId?: string;
}

const BookingCheckout: React.FC<BookingCheckoutProps> = ({
  event,
  selectedTickets,
  isOpen,
  onClose,
  onBookingComplete
}) => {
  const [currentStep, setCurrentStep] = useState(1);
  const [loading, setLoading] = useState(false);
  const [form, setForm] = useState<BookingForm>({
    firstName: '',
    lastName: '',
    email: '',
    phone: '',
    country: 'Croatia',
    specialRequests: '',
    marketingConsent: false,
    termsAccepted: false,
    paymentMethod: 'stripe',
  });

  const user = getCurrentUser();

  // Pre-fill form with user data if available
  React.useEffect(() => {
    if (user) {
      setForm(prev => ({
        ...prev,
        firstName: user.name?.split(' ')[0] || '',
        lastName: user.name?.split(' ').slice(1).join(' ') || '',
        email: user.email || '',
      }));
    }
  }, [user]);

  const updateForm = (field: keyof BookingForm, value: any) => {
    setForm(prev => ({ ...prev, [field]: value }));
  };

  const calculateSubtotal = (): number => {
    return selectedTickets.reduce((total, item) => 
      total + (item.ticketType.price * item.quantity), 0
    );
  };

  const calculateFees = (): number => {
    const subtotal = calculateSubtotal();
    return Math.round(subtotal * 0.029 + 5); // 2.9% + 5 HRK processing fee
  };

  const calculateTotal = (): number => {
    return calculateSubtotal() + calculateFees();
  };

  const getTotalTickets = (): number => {
    return selectedTickets.reduce((total, item) => total + item.quantity, 0);
  };

  const validateStep1 = (): boolean => {
    const required = ['firstName', 'lastName', 'email', 'phone'];
    return required.every(field => form[field as keyof BookingForm]);
  };

  const validateStep2 = (): boolean => {
    if (!form.termsAccepted) return false;
    
    if (form.paymentMethod === 'stripe') {
      return !!form.paymentIntentId; // Payment must be processed
    }
    
    return true; // PayPal validation happens externally
  };

  const handleNext = () => {
    if (currentStep === 1 && !validateStep1()) {
      toast({
        title: "Missing information",
        description: "Please fill in all required fields.",
        variant: "destructive",
      });
      return;
    }
    
    setCurrentStep(prev => prev + 1);
  };

  const handleBack = () => {
    setCurrentStep(prev => prev - 1);
  };

  const handleSubmitBooking = async () => {
    if (!validateStep2()) {
      toast({
        title: "Missing information",
        description: "Please complete payment information and accept terms.",
        variant: "destructive",
      });
      return;
    }

    setLoading(true);
    
    try {
      // Simulate API call to create booking
      await new Promise(resolve => setTimeout(resolve, 2000));
      
      const bookingReference = `BK${Date.now().toString().slice(-8)}`;
      
      toast({
        title: "Booking confirmed!",
        description: `Your booking reference is ${bookingReference}`,
      });
      
      onBookingComplete(bookingReference);
    } catch (error) {
      toast({
        title: "Booking failed",
        description: "Please try again or contact support.",
        variant: "destructive",
      });
    } finally {
      setLoading(false);
    }
  };


  return (
    <Dialog open={isOpen} onOpenChange={onClose}>
      <DialogContent className="max-w-4xl max-h-[90vh] overflow-y-auto">
        <DialogHeader>
          <DialogTitle className="flex items-center gap-2">
            <Ticket className="h-5 w-5" />
            Complete Your Booking
          </DialogTitle>
        </DialogHeader>

        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* Main Content */}
          <div className="lg:col-span-2 space-y-6">
            {/* Progress Steps */}
            <div className="flex items-center justify-center space-x-4">
              {[1, 2, 3].map((step) => (
                <div key={step} className="flex items-center">
                  <div className={`
                    w-8 h-8 rounded-full flex items-center justify-center text-sm font-medium
                    ${currentStep >= step 
                      ? 'bg-navy-blue text-white' 
                      : 'bg-gray-200 text-gray-600'
                    }
                  `}>
                    {currentStep > step ? <Check className="h-4 w-4" /> : step}
                  </div>
                  {step < 3 && (
                    <div className={`
                      w-12 h-0.5 mx-2
                      ${currentStep > step ? 'bg-navy-blue' : 'bg-gray-200'}
                    `} />
                  )}
                </div>
              ))}
            </div>

            {/* Step 1: Contact Information */}
            {currentStep === 1 && (
              <Card>
                <CardHeader>
                  <CardTitle className="flex items-center gap-2">
                    <User className="h-5 w-5" />
                    Contact Information
                  </CardTitle>
                </CardHeader>
                <CardContent className="space-y-4">
                  <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                    <div>
                      <Label htmlFor="firstName">First Name *</Label>
                      <Input
                        id="firstName"
                        value={form.firstName}
                        onChange={(e) => updateForm('firstName', e.target.value)}
                        placeholder="Enter first name"
                      />
                    </div>
                    <div>
                      <Label htmlFor="lastName">Last Name *</Label>
                      <Input
                        id="lastName"
                        value={form.lastName}
                        onChange={(e) => updateForm('lastName', e.target.value)}
                        placeholder="Enter last name"
                      />
                    </div>
                  </div>
                  
                  <div>
                    <Label htmlFor="email">Email Address *</Label>
                    <div className="relative">
                      <Mail className="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-gray-400" />
                      <Input
                        id="email"
                        type="email"
                        value={form.email}
                        onChange={(e) => updateForm('email', e.target.value)}
                        placeholder="Enter email address"
                        className="pl-10"
                      />
                    </div>
                  </div>
                  
                  <div>
                    <Label htmlFor="phone">Phone Number *</Label>
                    <div className="relative">
                      <Phone className="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-gray-400" />
                      <Input
                        id="phone"
                        type="tel"
                        value={form.phone}
                        onChange={(e) => updateForm('phone', e.target.value)}
                        placeholder="Enter phone number"
                        className="pl-10"
                      />
                    </div>
                  </div>
                  
                  <div>
                    <Label htmlFor="country">Country</Label>
                    <Select value={form.country} onValueChange={(value) => updateForm('country', value)}>
                      <SelectTrigger>
                        <SelectValue />
                      </SelectTrigger>
                      <SelectContent>
                        <SelectItem value="Croatia">Croatia</SelectItem>
                        <SelectItem value="Slovenia">Slovenia</SelectItem>
                        <SelectItem value="Bosnia and Herzegovina">Bosnia and Herzegovina</SelectItem>
                        <SelectItem value="Serbia">Serbia</SelectItem>
                        <SelectItem value="Other">Other</SelectItem>
                      </SelectContent>
                    </Select>
                  </div>
                  
                  <div>
                    <Label htmlFor="specialRequests">Special Requests (Optional)</Label>
                    <Textarea
                      id="specialRequests"
                      value={form.specialRequests}
                      onChange={(e) => updateForm('specialRequests', e.target.value)}
                      placeholder="Any special requirements or accessibility needs?"
                      rows={3}
                    />
                  </div>

                  <div className="flex justify-end">
                    <Button onClick={handleNext} disabled={!validateStep1()}>
                      Continue to Payment
                    </Button>
                  </div>
                </CardContent>
              </Card>
            )}

            {/* Step 2: Payment */}
            {currentStep === 2 && (
              <Card>
                <CardHeader>
                  <CardTitle className="flex items-center gap-2">
                    <CreditCard className="h-5 w-5" />
                    Payment Information
                  </CardTitle>
                </CardHeader>
                <CardContent className="space-y-4">
                  {/* Payment Method Selection */}
                  <div>
                    <Label>Payment Method</Label>
                    <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 mt-2">
                      <div 
                        className={`border rounded-lg p-3 cursor-pointer transition-colors ${
                          form.paymentMethod === 'stripe' ? 'border-navy-blue bg-blue-50' : 'border-gray-200'
                        }`}
                        onClick={() => updateForm('paymentMethod', 'stripe')}
                      >
                        <div className="flex items-center gap-2">
                          <div className={`w-4 h-4 rounded-full border-2 ${
                            form.paymentMethod === 'stripe' ? 'border-navy-blue bg-navy-blue' : 'border-gray-300'
                          }`}>
                            {form.paymentMethod === 'stripe' && (
                              <div className="w-2 h-2 bg-white rounded-full m-0.5" />
                            )}
                          </div>
                          <CreditCard className="h-4 w-4" />
                          <span className="font-medium">Credit/Debit Card</span>
                        </div>
                      </div>
                      
                      <div 
                        className={`border rounded-lg p-3 cursor-pointer transition-colors ${
                          form.paymentMethod === 'paypal' ? 'border-navy-blue bg-blue-50' : 'border-gray-200'
                        }`}
                        onClick={() => updateForm('paymentMethod', 'paypal')}
                      >
                        <div className="flex items-center gap-2">
                          <div className={`w-4 h-4 rounded-full border-2 ${
                            form.paymentMethod === 'paypal' ? 'border-navy-blue bg-navy-blue' : 'border-gray-300'
                          }`}>
                            {form.paymentMethod === 'paypal' && (
                              <div className="w-2 h-2 bg-white rounded-full m-0.5" />
                            )}
                          </div>
                          <Euro className="h-4 w-4" />
                          <span className="font-medium">PayPal</span>
                        </div>
                      </div>
                    </div>
                  </div>

                  {/* Stripe Payment */}
                  {form.paymentMethod === 'stripe' && (
                    <StripePayment
                      amount={calculateTotal()}
                      currency="HRK"
                      onSuccess={(paymentIntentId) => {
                        updateForm('paymentIntentId', paymentIntentId);
                        setCurrentStep(3);
                      }}
                      onError={(error) => {
                        toast({
                          title: "Payment failed",
                          description: error,
                          variant: "destructive",
                        });
                      }}
                    />
                  )}

                  {/* PayPal Message */}
                  {form.paymentMethod === 'paypal' && (
                    <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-4">
                      <p className="text-sm text-yellow-800">
                        You will be redirected to PayPal to complete your payment securely.
                      </p>
                    </div>
                  )}

                  {/* Terms and Conditions */}
                  <div className="space-y-3 pt-4 border-t">
                    <div className="flex items-start gap-3">
                      <Checkbox 
                        id="terms"
                        checked={form.termsAccepted}
                        onCheckedChange={(checked) => updateForm('termsAccepted', checked)}
                      />
                      <Label htmlFor="terms" className="text-sm leading-relaxed">
                        I accept the <a href="#" className="text-navy-blue underline">Terms & Conditions</a> and 
                        <a href="#" className="text-navy-blue underline ml-1">Privacy Policy</a> *
                      </Label>
                    </div>
                    
                    <div className="flex items-start gap-3">
                      <Checkbox 
                        id="marketing"
                        checked={form.marketingConsent}
                        onCheckedChange={(checked) => updateForm('marketingConsent', checked)}
                      />
                      <Label htmlFor="marketing" className="text-sm leading-relaxed">
                        I would like to receive marketing emails about future events and special offers
                      </Label>
                    </div>
                  </div>

                  <div className="flex justify-between">
                    <Button variant="outline" onClick={handleBack}>
                      <ArrowLeft className="h-4 w-4 mr-2" />
                      Back
                    </Button>
                    <Button onClick={() => setCurrentStep(3)} disabled={!validateStep2()}>
                      Review Order
                    </Button>
                  </div>
                </CardContent>
              </Card>
            )}

            {/* Step 3: Review & Confirm */}
            {currentStep === 3 && (
              <Card>
                <CardHeader>
                  <CardTitle className="flex items-center gap-2">
                    <Check className="h-5 w-5" />
                    Review & Confirm
                  </CardTitle>
                </CardHeader>
                <CardContent className="space-y-4">
                  <div className="grid grid-cols-1 sm:grid-cols-2 gap-6">
                    <div>
                      <h4 className="font-medium mb-2">Contact Information</h4>
                      <div className="text-sm text-gray-600 space-y-1">
                        <p>{form.firstName} {form.lastName}</p>
                        <p>{form.email}</p>
                        <p>{form.phone}</p>
                        <p>{form.country}</p>
                      </div>
                    </div>
                    
                    <div>
                      <h4 className="font-medium mb-2">Payment Method</h4>
                      <div className="text-sm text-gray-600">
                        {form.paymentMethod === 'stripe' ? (
                          <div>
                            <p>Credit/Debit Card</p>
                            {form.paymentIntentId && (
                              <p className="text-green-600">✓ Payment Authorized</p>
                            )}
                          </div>
                        ) : (
                          <p>PayPal</p>
                        )}
                      </div>
                    </div>
                  </div>

                  <div className="bg-red-50 border border-red-200 rounded-lg p-4">
                    <div className="flex items-start gap-2">
                      <AlertCircle className="h-5 w-5 text-red-500 mt-0.5" />
                      <div>
                        <h4 className="font-medium text-red-900">Important Notice</h4>
                        <p className="text-sm text-red-700 mt-1">
                          By confirming this booking, you agree to pay the total amount shown. 
                          Tickets are non-refundable unless the event is cancelled.
                        </p>
                      </div>
                    </div>
                  </div>

                  <div className="flex justify-between">
                    <Button variant="outline" onClick={handleBack}>
                      <ArrowLeft className="h-4 w-4 mr-2" />
                      Back
                    </Button>
                    <Button 
                      onClick={handleSubmitBooking} 
                      disabled={loading}
                      className="bg-green-600 hover:bg-green-700"
                    >
                      <Lock className="h-4 w-4 mr-2" />
                      {loading ? 'Confirming Booking...' : 'Confirm Booking'}
                    </Button>
                  </div>
                </CardContent>
              </Card>
            )}
          </div>

          {/* Order Summary Sidebar */}
          <div className="lg:col-span-1">
            <Card className="sticky top-6">
              <CardHeader>
                <CardTitle className="text-lg">Order Summary</CardTitle>
              </CardHeader>
              <CardContent className="space-y-4">
                {/* Event Info */}
                <div className="pb-4 border-b">
                  <h4 className="font-medium">{event.title}</h4>
                  <div className="text-sm text-gray-600 mt-1 space-y-1">
                    <div className="flex items-center gap-1">
                      <Calendar className="h-3 w-3" />
                      {new Date(event.date + 'T' + event.time).toLocaleDateString()}
                    </div>
                    <div className="flex items-center gap-1">
                      <MapPin className="h-3 w-3" />
                      {event.venue}
                    </div>
                  </div>
                </div>

                {/* Ticket Breakdown */}
                <div className="space-y-3">
                  {selectedTickets.map((item, index) => (
                    <div key={index} className="flex justify-between">
                      <div>
                        <span className="font-medium">{item.quantity}× {item.ticketType.name}</span>
                        <p className="text-xs text-gray-600">{item.ticketType.price} HRK each</p>
                      </div>
                      <span className="font-medium">
                        {(item.ticketType.price * item.quantity).toLocaleString()} HRK
                      </span>
                    </div>
                  ))}
                </div>

                {/* Totals */}
                <div className="space-y-2 pt-4 border-t">
                  <div className="flex justify-between">
                    <span>Subtotal</span>
                    <span>{calculateSubtotal().toLocaleString()} HRK</span>
                  </div>
                  <div className="flex justify-between text-sm text-gray-600">
                    <span>Processing Fee</span>
                    <span>{calculateFees().toLocaleString()} HRK</span>
                  </div>
                  <div className="flex justify-between font-bold text-lg pt-2 border-t">
                    <span>Total</span>
                    <span>{calculateTotal().toLocaleString()} HRK</span>
                  </div>
                </div>

                {/* Security Note */}
                <div className="bg-gray-50 rounded-lg p-3 text-center">
                  <Lock className="h-4 w-4 mx-auto text-gray-600 mb-1" />
                  <p className="text-xs text-gray-600">
                    Secure payment processing
                  </p>
                </div>
              </CardContent>
            </Card>
          </div>
        </div>
      </DialogContent>
    </Dialog>
  );
};

export default BookingCheckout;