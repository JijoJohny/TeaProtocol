import { useEffect, useState } from 'react';
import {
  startCollateralVerification,
  getVerificationStatus,
  getCollateralDetails,
  type CollateralVerification
} from '../services/vlayerService';
import './CollateralVerification.css';

interface CollateralVerificationProps {
  paymentIntentId: string;
  algoAddress: string;
  amount: number;
  onVerificationComplete: (status: CollateralVerification) => void;
  onError: (error: string) => void;
}

const CollateralVerification = ({
  paymentIntentId,
  algoAddress,
  amount,
  onVerificationComplete,
  onError
}: CollateralVerificationProps) => {
  const [verification, setVerification] = useState<CollateralVerification | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [collateralDetails, setCollateralDetails] = useState<any>(null);

  useEffect(() => {
    const verifyCollateral = async () => {
      try {
        setLoading(true);
        // Start verification process
        const verificationResult = await startCollateralVerification(
          paymentIntentId,
          algoAddress,
          amount
        );
        setVerification(verificationResult);

        // Get collateral details
        const details = await getCollateralDetails(algoAddress);
        setCollateralDetails(details);

        // If verification is already complete, notify parent
        if (verificationResult.status === 'verified') {
          onVerificationComplete(verificationResult);
        }
      } catch (err) {
        const errorMessage = err instanceof Error ? err.message : 'Failed to verify collateral';
        setError(errorMessage);
        onError(errorMessage);
      } finally {
        setLoading(false);
      }
    };

    verifyCollateral();
  }, [paymentIntentId, algoAddress, amount, onVerificationComplete, onError]);

  // Poll for verification status if pending
  useEffect(() => {
    if (!verification || verification.status !== 'pending') return;

    const pollInterval = setInterval(async () => {
      try {
        const status = await getVerificationStatus(verification.verificationId);
        setVerification(status);

        if (status.status !== 'pending') {
          clearInterval(pollInterval);
          if (status.status === 'verified') {
            onVerificationComplete(status);
          }
        }
      } catch (err) {
        console.error('Error polling verification status:', err);
      }
    }, 5000); // Poll every 5 seconds

    return () => clearInterval(pollInterval);
  }, [verification, onVerificationComplete]);

  if (loading) {
    return (
      <div className="verification-container">
        <div className="verification-loading">
          <div className="spinner"></div>
          <p>Verifying collateral...</p>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="verification-container">
        <div className="verification-error">
          <p>{error}</p>
        </div>
      </div>
    );
  }

  return (
    <div className="verification-container">
      <div className="verification-status">
        <h3>Collateral Verification</h3>
        <div className="status-badge" data-status={verification?.status}>
          {verification?.status.toUpperCase()}
        </div>
      </div>

      {collateralDetails && (
        <div className="collateral-details">
          <h4>Collateral Details</h4>
          <div className="details-grid">
            <div className="detail-item">
              <span>Total Collateral:</span>
              <span>${collateralDetails.totalCollateral.toFixed(2)}</span>
            </div>
            <div className="detail-item">
              <span>Available Collateral:</span>
              <span>${collateralDetails.availableCollateral.toFixed(2)}</span>
            </div>
            <div className="detail-item">
              <span>Locked Collateral:</span>
              <span>${collateralDetails.lockedCollateral.toFixed(2)}</span>
            </div>
          </div>

          <div className="assets-list">
            <h4>Assets</h4>
            {collateralDetails.assets.map((asset: any, index: number) => (
              <div key={index} className="asset-item">
                <span>{asset.type}</span>
                <span>{asset.amount}</span>
                <span>${asset.value.toFixed(2)}</span>
              </div>
            ))}
          </div>
        </div>
      )}

      {verification?.details && (
        <div className="verification-details">
          <h4>Verification Details</h4>
          <div className="details-grid">
            <div className="detail-item">
              <span>Asset Type:</span>
              <span>{verification.details.assetType}</span>
            </div>
            <div className="detail-item">
              <span>Asset Value:</span>
              <span>${verification.details.assetValue.toFixed(2)}</span>
            </div>
            <div className="detail-item">
              <span>Risk Score:</span>
              <span>{verification.details.riskScore}</span>
            </div>
            <div className="detail-item">
              <span>Verification Method:</span>
              <span>{verification.details.verificationMethod}</span>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default CollateralVerification; 