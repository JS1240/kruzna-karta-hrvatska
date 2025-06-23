import React, { useState, useEffect } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { 
  CreditCard, 
  Lock, 
  AlertCircle, 
  CheckCircle,
  Loader2 
} from 'lucide-react';
import { toast } from '@/hooks/use-toast';

interface StripePaymentProps {
  amount: number;
  currency: string;
  onSuccess: (paymentIntentId: string) => void;
  onError: (error: string) => void;
  disabled?: boolean;
}

interface CardData {
  number: string;
  expiry: string;
  cvc: string;
  name: string;
}

interface ValidationErrors {
  number?: string;
  expiry?: string;
  cvc?: string;
  name?: string;
}

const StripePayment: React.FC<StripePaymentProps> = ({
  amount,
  currency,
  onSuccess,
  onError,
  disabled = false,
}) => {
  const [cardData, setCardData] = useState<CardData>({
    number: '',
    expiry: '',
    cvc: '',
    name: '',
  });
  
  const [errors, setErrors] = useState<ValidationErrors>({});
  const [processing, setProcessing] = useState(false);
  const [cardType, setCardType] = useState<string>('');

  // Card number formatting and validation
  const formatCardNumber = (value: string): string => {
    const digits = value.replace(/\D/g, '');
    const formatted = digits.replace(/(\d{4})(?=\d)/g, '$1 ');
    return formatted.substring(0, 19); // Max 16 digits + 3 spaces
  };

  const formatExpiry = (value: string): string => {
    const digits = value.replace(/\D/g, '');
    if (digits.length >= 2) {
      return `${digits.slice(0, 2)}/${digits.slice(2, 4)}`;
    }
    return digits;
  };

  const formatCVC = (value: string): string => {
    return value.replace(/\D/g, '').substring(0, 4);
  };

  // Detect card type based on number
  const detectCardType = (number: string): string => {
    const cleanNumber = number.replace(/\D/g, '');
    
    if (/^4/.test(cleanNumber)) return 'visa';
    if (/^5[1-5]/.test(cleanNumber)) return 'mastercard';
    if (/^3[47]/.test(cleanNumber)) return 'amex';
    if (/^6(?:011|5)/.test(cleanNumber)) return 'discover';
    
    return '';
  };

  // Validation functions
  const validateCardNumber = (number: string): boolean => {
    const cleanNumber = number.replace(/\D/g, '');
    
    // Basic length check
    if (cleanNumber.length < 13 || cleanNumber.length > 19) return false;
    
    // Luhn algorithm
    let sum = 0;
    let alternate = false;
    
    for (let i = cleanNumber.length - 1; i >= 0; i--) {
      let n = parseInt(cleanNumber.charAt(i), 10);
      
      if (alternate) {
        n *= 2;
        if (n > 9) n = (n % 10) + 1;
      }
      
      sum += n;
      alternate = !alternate;
    }
    
    return sum % 10 === 0;
  };

  const validateExpiry = (expiry: string): boolean => {
    const [month, year] = expiry.split('/');
    if (!month || !year) return false;
    
    const monthNum = parseInt(month, 10);
    const yearNum = parseInt('20' + year, 10);
    
    if (monthNum < 1 || monthNum > 12) return false;
    
    const now = new Date();
    const currentYear = now.getFullYear();
    const currentMonth = now.getMonth() + 1;
    
    if (yearNum < currentYear) return false;
    if (yearNum === currentYear && monthNum < currentMonth) return false;
    
    return true;
  };

  const validateCVC = (cvc: string): boolean => {
    return cvc.length >= 3 && cvc.length <= 4;
  };

  const validateForm = (): boolean => {
    const newErrors: ValidationErrors = {};
    
    if (!cardData.name.trim()) {
      newErrors.name = 'Cardholder name is required';
    }
    
    if (!validateCardNumber(cardData.number)) {
      newErrors.number = 'Invalid card number';
    }
    
    if (!validateExpiry(cardData.expiry)) {
      newErrors.expiry = 'Invalid expiry date';
    }
    
    if (!validateCVC(cardData.cvc)) {
      newErrors.cvc = 'Invalid security code';
    }
    
    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };

  // Handle input changes
  const handleInputChange = (field: keyof CardData, value: string) => {
    let formattedValue = value;
    
    switch (field) {
      case 'number':
        formattedValue = formatCardNumber(value);
        setCardType(detectCardType(formattedValue));
        break;
      case 'expiry':
        formattedValue = formatExpiry(value);
        break;
      case 'cvc':
        formattedValue = formatCVC(value);
        break;
    }
    
    setCardData(prev => ({ ...prev, [field]: formattedValue }));
    
    // Clear error when user starts typing
    if (errors[field]) {
      setErrors(prev => ({ ...prev, [field]: undefined }));
    }
  };

  // Simulate payment processing
  const processPayment = async (): Promise<{ success: boolean; paymentIntentId?: string; error?: string }> => {
    // Simulate API call delay
    await new Promise(resolve => setTimeout(resolve, 2000));
    
    // Simulate different outcomes based on card number
    const cardNumber = cardData.number.replace(/\D/g, '');
    
    // Test cards that should fail
    if (cardNumber.endsWith('0002')) {
      return { success: false, error: 'Your card was declined.' };
    }
    
    if (cardNumber.endsWith('0004')) {
      return { success: false, error: 'Your card has expired.' };
    }
    
    if (cardNumber.endsWith('0005')) {
      return { success: false, error: 'Your card has insufficient funds.' };
    }
    
    // Default success
    return { 
      success: true, 
      paymentIntentId: `pi_${Date.now()}_${Math.random().toString(36).substr(2, 9)}` 
    };
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    
    if (!validateForm()) {
      toast({
        title: "Please correct the errors",
        description: "Check your payment information and try again.",
        variant: "destructive",
      });
      return;
    }
    
    setProcessing(true);
    
    try {
      const result = await processPayment();
      
      if (result.success && result.paymentIntentId) {
        toast({
          title: "Payment successful!",
          description: "Your payment has been processed successfully.",
        });
        onSuccess(result.paymentIntentId);
      } else {
        throw new Error(result.error || 'Payment failed');
      }
    } catch (error) {
      const errorMessage = error instanceof Error ? error.message : 'Payment processing failed';
      toast({
        title: "Payment failed",
        description: errorMessage,
        variant: "destructive",
      });
      onError(errorMessage);
    } finally {
      setProcessing(false);
    }
  };

  const getCardIcon = () => {
    switch (cardType) {
      case 'visa':
        return '💳 Visa';
      case 'mastercard':
        return '💳 Mastercard';
      case 'amex':
        return '💳 Amex';
      case 'discover':
        return '💳 Discover';
      default:
        return '💳';
    }
  };

  return (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          <CreditCard className="h-5 w-5" />
          Payment Details
        </CardTitle>
      </CardHeader>
      <CardContent>
        <form onSubmit={handleSubmit} className="space-y-4">
          {/* Cardholder Name */}
          <div>
            <Label htmlFor="cardName">Cardholder Name *</Label>
            <Input
              id="cardName"
              value={cardData.name}
              onChange={(e) => handleInputChange('name', e.target.value)}
              placeholder="Enter name as shown on card"
              disabled={disabled || processing}
              className={errors.name ? 'border-red-500' : ''}
            />
            {errors.name && (
              <p className="text-sm text-red-500 mt-1">{errors.name}</p>
            )}
          </div>

          {/* Card Number */}
          <div>
            <Label htmlFor="cardNumber">Card Number *</Label>
            <div className="relative">
              <Input
                id="cardNumber"
                value={cardData.number}
                onChange={(e) => handleInputChange('number', e.target.value)}
                placeholder="1234 5678 9012 3456"
                disabled={disabled || processing}
                className={`pr-12 ${errors.number ? 'border-red-500' : ''}`}
                maxLength={19}
              />
              {cardType && (
                <div className="absolute right-3 top-1/2 transform -translate-y-1/2 text-sm">
                  {getCardIcon()}
                </div>
              )}
            </div>
            {errors.number && (
              <p className="text-sm text-red-500 mt-1">{errors.number}</p>
            )}
          </div>

          {/* Expiry and CVC */}
          <div className="grid grid-cols-2 gap-4">
            <div>
              <Label htmlFor="expiry">Expiry Date *</Label>
              <Input
                id="expiry"
                value={cardData.expiry}
                onChange={(e) => handleInputChange('expiry', e.target.value)}
                placeholder="MM/YY"
                disabled={disabled || processing}
                className={errors.expiry ? 'border-red-500' : ''}
                maxLength={5}
              />
              {errors.expiry && (
                <p className="text-sm text-red-500 mt-1">{errors.expiry}</p>
              )}
            </div>
            
            <div>
              <Label htmlFor="cvc">Security Code *</Label>
              <Input
                id="cvc"
                value={cardData.cvc}
                onChange={(e) => handleInputChange('cvc', e.target.value)}
                placeholder="123"
                disabled={disabled || processing}
                className={errors.cvc ? 'border-red-500' : ''}
                maxLength={4}
              />
              {errors.cvc && (
                <p className="text-sm text-red-500 mt-1">{errors.cvc}</p>
              )}
            </div>
          </div>

          {/* Security Notice */}
          <Alert>
            <Lock className="h-4 w-4" />
            <AlertDescription>
              Your payment information is encrypted and secure. We use industry-standard SSL encryption.
            </AlertDescription>
          </Alert>

          {/* Test Card Info */}
          <Alert>
            <AlertCircle className="h-4 w-4" />
            <AlertDescription>
              <strong>Test Cards:</strong> Use 4242 4242 4242 4242 (success), 4000 0000 0000 0002 (decline)
            </AlertDescription>
          </Alert>

          {/* Payment Amount */}
          <div className="bg-gray-50 rounded-lg p-4">
            <div className="flex justify-between items-center">
              <span className="font-medium">Total Amount:</span>
              <span className="text-xl font-bold">
                {amount.toLocaleString()} {currency}
              </span>
            </div>
          </div>

          {/* Submit Button */}
          <Button 
            type="submit" 
            className="w-full" 
            disabled={disabled || processing}
            size="lg"
          >
            {processing ? (
              <>
                <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                Processing Payment...
              </>
            ) : (
              <>
                <Lock className="h-4 w-4 mr-2" />
                Pay {amount.toLocaleString()} {currency}
              </>
            )}
          </Button>

          {/* Security Badges */}
          <div className="flex justify-center items-center gap-4 text-xs text-gray-500 pt-2">
            <span>🔒 SSL Encrypted</span>
            <span>💳 Stripe Secured</span>
            <span>✅ PCI Compliant</span>
          </div>
        </form>
      </CardContent>
    </Card>
  );
};

export default StripePayment;