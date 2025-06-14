import axios from 'axios';

const API_URL = 'http://localhost:8000';

export interface CollateralVerification {
  status: 'verified' | 'pending' | 'failed';
  collateralAmount: number;
  verificationId: string;
  timestamp: string;
  details: {
    assetType: string;
    assetValue: number;
    riskScore: number;
    verificationMethod: string;
  };
}

export interface VerificationRequest {
  paymentIntentId: string;
  algoAddress: string;
  amount: number;
}

// Start collateral verification process
export const startCollateralVerification = async (
  paymentIntentId: string,
  algoAddress: string,
  amount: number
): Promise<CollateralVerification> => {
  try {
    const response = await axios.post(`${API_URL}/verify-collateral`, {
      payment_intent_id: paymentIntentId,
      algo_address: algoAddress,
      amount: amount
    });

    return response.data;
  } catch (error) {
    console.error('Error starting collateral verification:', error);
    throw error;
  }
};

// Get verification status
export const getVerificationStatus = async (
  verificationId: string
): Promise<CollateralVerification> => {
  try {
    const response = await axios.get(`${API_URL}/verification-status/${verificationId}`);
    return response.data;
  } catch (error) {
    console.error('Error getting verification status:', error);
    throw error;
  }
};

// Get collateral details
export const getCollateralDetails = async (
  algoAddress: string
): Promise<{
  totalCollateral: number;
  availableCollateral: number;
  lockedCollateral: number;
  assets: Array<{
    type: string;
    amount: number;
    value: number;
  }>;
}> => {
  try {
    const response = await axios.get(`${API_URL}/collateral-details/${algoAddress}`);
    return response.data;
  } catch (error) {
    console.error('Error getting collateral details:', error);
    throw error;
  }
}; 