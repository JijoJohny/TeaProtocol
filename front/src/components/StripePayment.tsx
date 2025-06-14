import { useEffect, useState } from 'react';
import { loadStripe } from '@stripe/stripe-js';
import {
  Elements,
  PaymentElement,
  useStripe,
  useElements,
} from '@stripe/react-stripe-js';
import {
  createPaymentIntent,
  getPaymentStatus,
  capturePayment,
  cancelPayment,
  DEFAULT_ALGO_WALLET,
  type PaymentStatus,
} from '../services/stripeService';

const stripePromise = loadStripe('pk_test_51RZcoKQeThsKjpCIzqNsIPJZIlqB3F2DilDS6Q0HlqfmYep1xex67K4eiTX7MkJ2ZqgabdpdMukQh0DAeIzZp2du00JtDErIU2');

interface PaymentFormProps {
  clientSecret: string;
  paymentIntentId: string;
  onSuccess: (paymentIntentId: string) => void;
  onError: (error: string) => void;
}

const PaymentForm = ({ clientSecret, paymentIntentId, onSuccess, onError }: PaymentFormProps) => {
  const stripe = useStripe();
  const elements = useElements();
  const [isProcessing, setIsProcessing] = useState(false);
  const [message, setMessage] = useState<string | null>(null);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!stripe || !elements) {
      console.error('Stripe or Elements not initialized');
      return;
    }
    
    setIsProcessing(true);
    setMessage(null);

    try {
      console.log('Starting payment confirmation...', {
        clientSecret,
        paymentIntentId,
        stripe: !!stripe,
        elements: !!elements
      });

      // First confirm the payment with the payment method
      const { error, paymentIntent } = await stripe.confirmPayment({
        elements,
        confirmParams: {
          return_url: `${window.location.origin}/borrow?payment_intent=${paymentIntentId}`,
        },
        redirect: 'if_required',
      });

      console.log('Payment confirmation result:', { 
        error: error ? {
          message: error.message,
          type: error.type,
          code: error.code
        } : null,
        paymentIntent: paymentIntent ? {
          id: paymentIntent.id,
          status: paymentIntent.status,
          amount: paymentIntent.amount,
          currency: paymentIntent.currency,
          payment_method: paymentIntent.payment_method
        } : null
      });

      if (error) {
        console.error('Payment error details:', {
          message: error.message,
          type: error.type,
          code: error.code,
          decline_code: error.decline_code
        });
        setMessage(error.message || 'Payment failed');
        onError(error.message || 'Payment failed');
        return;
      }

      if (!paymentIntent) {
        console.error('No payment intent returned from confirmation');
        setMessage('Payment failed: No payment intent returned');
        onError('Payment failed: No payment intent returned');
        return;
      }

      console.log('Payment intent status:', paymentIntent.status);
      
      // Handle different payment statuses
      switch (paymentIntent.status) {
        case 'succeeded':
          setMessage('Payment succeeded!');
          onSuccess(paymentIntentId);
          break;
          
        case 'processing':
          setMessage('Your payment is processing.');
          // Check status after a delay
          const checkStatus = async () => {
            try {
              console.log('Checking payment status for:', paymentIntentId);
              const status = await getPaymentStatus(paymentIntentId);
              console.log('Payment status check result:', status);
              
              if (status.status === 'succeeded') {
                setMessage('Payment succeeded!');
                onSuccess(paymentIntentId);
              } else if (status.status === 'processing') {
                // Check again after 2 seconds
                setTimeout(checkStatus, 2000);
              } else if (status.status === 'requires_capture') {
                // Try to capture the payment
                try {
                  console.log('Attempting to capture payment:', paymentIntentId);
                  const captureResult = await capturePayment(paymentIntentId);
                  console.log('Capture result:', captureResult);
                  
                  if (captureResult.error) {
                    console.error('Payment capture failed:', captureResult.error);
                    setMessage(`Payment capture failed: ${captureResult.error}`);
                    onError(`Payment capture failed: ${captureResult.error}`);
                  } else {
                    setMessage('Payment captured successfully!');
                    onSuccess(paymentIntentId);
                  }
                } catch (err) {
                  console.error('Error capturing payment:', err);
                  const errorMessage = err instanceof Error ? err.message : 'Error capturing payment';
                  setMessage(errorMessage);
                  onError(errorMessage);
                }
              } else {
                console.error('Unexpected payment status:', status.status);
                setMessage(`Payment status: ${status.status}`);
                onError(`Payment status: ${status.status}`);
              }
            } catch (err) {
              console.error('Error checking payment status:', err);
              setMessage('Error checking payment status');
              onError('Error checking payment status');
            }
          };
          setTimeout(checkStatus, 2000);
          break;
          
        case 'requires_payment_method':
          console.log('Payment requires payment method');
          setMessage('Please enter your payment details.');
          break;
          
        case 'requires_confirmation':
          console.log('Payment requires confirmation');
          setMessage('Payment requires confirmation.');
          break;
          
        case 'requires_action':
          console.log('Payment requires additional action');
          setMessage('Payment requires additional action.');
          break;
          
        case 'requires_capture':
          console.log('Payment requires capture');
          setMessage('Payment authorized successfully! Capturing payment...');
          try {
            // First check if we have a payment method
            if (!paymentIntent.payment_method) {
              console.error('No payment method attached to payment intent');
              setMessage('Payment method not attached. Please try again.');
              onError('Payment method not attached');
              return;
            }

            console.log('Attempting to capture payment:', paymentIntentId);
            const captureResult = await capturePayment(paymentIntentId);
            console.log('Capture result:', captureResult);
            
            if (captureResult.error) {
              console.error('Payment capture failed:', captureResult.error);
              setMessage(`Payment capture failed: ${captureResult.error}`);
              onError(`Payment capture failed: ${captureResult.error}`);
            } else {
              setMessage('Payment captured successfully!');
              onSuccess(paymentIntentId);
            }
          } catch (err) {
            console.error('Error capturing payment:', err);
            const errorMessage = err instanceof Error ? err.message : 'Error capturing payment';
            setMessage(errorMessage);
            onError(errorMessage);
          }
          break;
          
        default:
          console.error('Unexpected payment status:', paymentIntent.status);
          setMessage('Something went wrong.');
          onError('Payment failed');
          break;
      }
    } catch (err) {
      console.error('Payment submission error:', err);
      setMessage('An unexpected error occurred');
      onError('An unexpected error occurred');
    } finally {
      setIsProcessing(false);
    }
  };

  return (
    <form onSubmit={handleSubmit} className="payment-form">
      <PaymentElement />
      {message && (
        <div className={`payment-message ${message.includes('succeeded') ? 'success' : message.includes('processing') ? 'info' : 'error'}`}>
          {message}
        </div>
      )}
      <button
        type="submit"
        className="btn btn-primary"
        disabled={!stripe || isProcessing}
      >
        {isProcessing ? 'Processing...' : 'Pay Now'}
      </button>
    </form>
  );
};

interface StripePaymentProps {
  amount: number;
  onSuccess: (paymentIntentId?: string) => void;
  onError: (error: string) => void;
}

const StripePayment = ({ amount, onSuccess, onError }: StripePaymentProps) => {
  const [clientSecret, setClientSecret] = useState<string | null>(null);
  const [paymentIntentId, setPaymentIntentId] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [status, setStatus] = useState<PaymentStatus | null>(null);
  const [actionLoading, setActionLoading] = useState(false);

  useEffect(() => {
    const initializePayment = async () => {
      try {
        // Convert amount to a number and validate
        const numericAmount = Number(amount);
        if (isNaN(numericAmount)) {
          throw new Error('Amount must be a valid number');
        }

        // Ensure amount is positive
        if (numericAmount <= 0) {
          throw new Error('Amount must be greater than 0');
        }

        console.log('Initializing payment with amount:', numericAmount);
        const response = await createPaymentIntent(numericAmount, DEFAULT_ALGO_WALLET, '');
        console.log('Payment intent response:', response);
        
        setClientSecret(response.client_secret);
        setPaymentIntentId(response.payment_intent_id);
      } catch (err) {
        const errorMessage = err instanceof Error ? err.message : 'Failed to initialize payment';
        console.error('Payment initialization error:', errorMessage);
        setError(errorMessage);
        onError(errorMessage);
      } finally {
        setLoading(false);
      }
    };

    initializePayment();
  }, [amount, onError]);

  // Check for payment_intent in URL on mount
  useEffect(() => {
    const params = new URLSearchParams(window.location.search);
    const paymentIntentId = params.get('payment_intent');
    
    if (paymentIntentId) {
      // Clear the URL parameter
      window.history.replaceState({}, document.title, window.location.pathname);
      
      // Check payment status
      getPaymentStatus(paymentIntentId).then((status) => {
        if (status.status === 'succeeded') {
          onSuccess(paymentIntentId);
        } else {
          onError('Payment was not successful');
        }
      }).catch((err) => {
        onError('Failed to verify payment status');
      });
    }
  }, [onSuccess, onError]);

  const handlePaymentSuccess = (intentId: string) => {
    setPaymentIntentId(intentId);
    onSuccess(intentId);
    // Fetch status after payment
    getPaymentStatus(intentId).then(setStatus);
  };

  const handleCapture = async () => {
    if (!paymentIntentId) return;
    setActionLoading(true);
    try {
      await capturePayment(paymentIntentId);
      const updated = await getPaymentStatus(paymentIntentId);
      setStatus(updated);
    } catch (err) {
      setError('Failed to capture payment');
    } finally {
      setActionLoading(false);
    }
  };

  const handleCancel = async () => {
    if (!paymentIntentId) return;
    setActionLoading(true);
    try {
      await cancelPayment(paymentIntentId);
      const updated = await getPaymentStatus(paymentIntentId);
      setStatus(updated);
    } catch (err) {
      setError('Failed to cancel payment');
    } finally {
      setActionLoading(false);
    }
  };

  if (loading) {
    return <div>Loading payment form...</div>;
  }
  if (error || !clientSecret || !paymentIntentId) {
    return <div className="error-message">{error || 'Failed to load payment form'}</div>;
  }

  const options = {
    clientSecret,
    appearance: {
      theme: 'stripe' as const,
      variables: {
        colorPrimary: '#0570de',
        colorBackground: '#ffffff',
        colorText: '#30313d',
        colorDanger: '#df1b41',
        fontFamily: 'system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif',
        spacingUnit: '4px',
        borderRadius: '4px',
      },
    },
  };

  return (
    <div>
      <Elements stripe={stripePromise} options={options}>
        <PaymentForm
          clientSecret={clientSecret}
          paymentIntentId={paymentIntentId}
          onSuccess={handlePaymentSuccess}
          onError={onError}
        />
      </Elements>
      {status && (
        <div className="payment-status">
          <h4>Payment Details</h4>
          <div><b>Status:</b> {status.status}</div>
          <div><b>Amount:</b> ${(status.amount / 100).toFixed(2)} {status.currency.toUpperCase()}</div>
          <div><b>Algorand Address:</b> {status.metadata?.algo_address}</div>
          <div><b>Type:</b> {status.metadata?.type}</div>
          <div><b>Capturable:</b> ${(status.amount_capturable / 100).toFixed(2)}</div>
          {(status.status === 'requires_capture' || status.amount_capturable > 0) && (
            <button onClick={handleCapture} disabled={actionLoading} className="btn btn-success">
              {actionLoading ? 'Capturing...' : 'Capture Payment'}
            </button>
          )}
          {status.status !== 'canceled' && status.status !== 'succeeded' && (
            <button onClick={handleCancel} disabled={actionLoading} className="btn btn-danger" style={{marginLeft: 8}}>
              {actionLoading ? 'Canceling...' : 'Cancel Payment'}
            </button>
          )}
        </div>
      )}
    </div>
  );
};

export default StripePayment; 