import axios from 'axios';

const API_URL = 'http://localhost:8000';

// Default Algorand wallet address
export const DEFAULT_ALGO_WALLET = 'QW5L3VD2RIFAKB33I6DCQAMZUSYSS2B5IW4GBQM7T7KSJWANU3ONHUFMTI';

export interface PaymentIntentResponse {
  client_secret: string;
  payment_intent_id: string;
  status: string;
}

export interface PaymentStatus {
  id: string;
  amount: number;
  currency: string;
  status: string;
  metadata: {
    algo_address: string;
    type: string;
  };
  amount_capturable: number;
}

export interface CaptureResponse {
  success: boolean;
  error?: string;
  paymentIntent?: {
    id: string;
    status: string;
    amount: number;
    currency: string;
  };
}

// Step 1: Create a payment intent
export const createPaymentIntent = async (
  amount: number,
  walletAddress: string = DEFAULT_ALGO_WALLET,
  paymentMethodId: string = ''
): Promise<PaymentIntentResponse> => {
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
    
    // Convert to cents for Stripe (multiply by 100)
    const amountInCents = Math.round(numericAmount * 100);
    
    const requestData = {
      amount: amountInCents, // Send amount in cents
      algo_address: walletAddress,
      payment_method_id: paymentMethodId,
      currency: 'usd'
    };

    console.log('Creating payment intent:', requestData);

    const response = await axios.post(`${API_URL}/create-payment-intent`, requestData, {
      headers: {
        'Content-Type': 'application/json'
      }
    });

    console.log('Payment intent created:', response.data);
    return response.data;
  } catch (error) {
    console.error('Error creating payment intent:', error);
    if (axios.isAxiosError(error)) {
      console.error('Response data:', error.response?.data);
    }
    throw error;
  }
};

// Step 2: Get payment status
export const getPaymentStatus = async (paymentIntentId: string): Promise<PaymentStatus> => {
  try {
    const response = await axios.get(`${API_URL}/payment-intent/${paymentIntentId}`);
    return response.data;
  } catch (error) {
    console.error('Error getting payment status:', error);
    throw error;
  }
};

// Step 3: Capture the payment
export const capturePayment = async (paymentIntentId: string): Promise<CaptureResponse> => {
  try {
    const response = await axios.post(`${API_URL}/capture-payment/${paymentIntentId}`);
    return response.data;
  } catch (error) {
    console.error('Error capturing payment:', error);
    throw error;
  }
};

// Step 4: Cancel the payment if needed
export const cancelPayment = async (paymentIntentId: string): Promise<{ id: string; status: string }> => {
  try {
    const response = await axios.post(`${API_URL}/cancel-payment/${paymentIntentId}`);
    return response.data;
  } catch (error) {
    console.error('Error canceling payment:', error);
    throw error;
  }
}; 