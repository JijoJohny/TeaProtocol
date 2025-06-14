import { useState } from 'react'
import StripePayment from '../components/StripePayment'
import CollateralVerification from '../components/CollateralVerification'
import { DEFAULT_ALGO_WALLET } from '../services/stripeService'
import type { CollateralVerification as CollateralVerificationType } from '../services/vlayerService'
import './Borrow.css'

const Borrow = () => {
  const [amount, setAmount] = useState('')
  const [isLoading, setIsLoading] = useState(false)
  const [error, setError] = useState('')
  const [showPaymentForm, setShowPaymentForm] = useState(false)
  const [showVerification, setShowVerification] = useState(false)
  const [paymentIntentId, setPaymentIntentId] = useState<string | null>(null)

  const handleBorrow = async () => {
    try {
      setIsLoading(true)
      setError('')

      // Validate amount
      const borrowAmount = parseFloat(amount)
      if (isNaN(borrowAmount)) {
        setError('Please enter a valid number')
        return
      }

      if (borrowAmount <= 0) {
        setError('Amount must be greater than 0')
        return
      }

      // If amount is valid, show payment form
      setShowPaymentForm(true)
    } catch (error) {
      setError('Failed to initiate borrowing. Please try again.')
    } finally {
      setIsLoading(false)
    }
  }

  const handlePaymentSuccess = (intentId: string) => {
    console.log('Payment successful, intent ID:', intentId);
    setPaymentIntentId(intentId);
    setShowPaymentForm(false);
    setShowVerification(true);
    setError(''); // Clear any previous errors
  }

  const handlePaymentError = (errorMessage: string) => {
    console.error('Payment error:', errorMessage);
    setError(errorMessage);
    setShowPaymentForm(false);
    setShowVerification(false);
  }

  const handleVerificationComplete = (verification: CollateralVerificationType) => {
    console.log('Verification complete:', verification);
    if (verification.status === 'verified') {
      // Handle successful verification
      setAmount('');
      setShowVerification(false);
      setShowPaymentForm(false);
      setPaymentIntentId(null);
      // Show success message
      setError(''); // Clear any previous errors
    } else {
      setError('Collateral verification failed');
    }
  }

  const handleVerificationError = (errorMessage: string) => {
    console.error('Verification error:', errorMessage);
    setError(errorMessage);
    setShowVerification(false);
    setShowPaymentForm(false);
    setPaymentIntentId(null);
  }

  return (
    <div className="borrow-page">
      <div className="container">
        <div className="borrow-content">
          <div className="borrow-header">
            <h1>Borrow VUSD</h1>
            <p>Enter the amount you want to borrow</p>
          </div>

          {!showPaymentForm && !showVerification ? (
            <div className="borrow-form">
              <div className="form-group">
                <label className="form-label">Amount (VUSD)</label>
                <input
                  type="number"
                  className="form-input"
                  value={amount}
                  onChange={(e) => setAmount(e.target.value)}
                  placeholder="Enter amount"
                  min="0"
                />
              </div>

              {error && <div className="error-message">{error}</div>}

              <button
                className="btn btn-primary"
                onClick={handleBorrow}
                disabled={isLoading}
              >
                {isLoading ? 'Processing...' : 'Borrow Now'}
              </button>
            </div>
          ) : showPaymentForm ? (
            <div className="payment-section">
              <StripePayment
                amount={parseFloat(amount)}
                onSuccess={handlePaymentSuccess}
                onError={handlePaymentError}
              />
            </div>
          ) : (
            paymentIntentId && (
              <CollateralVerification
                paymentIntentId={paymentIntentId}
                algoAddress={DEFAULT_ALGO_WALLET}
                amount={parseFloat(amount)}
                onVerificationComplete={handleVerificationComplete}
                onError={handleVerificationError}
              />
            )
          )}

          <div className="borrow-note">
            <p>
              Note: You need to have a connected wallet and sufficient collateral to borrow VUSD tokens.
              The borrowing process will be completed through Stripe payment and collateral verification.
            </p>
          </div>
        </div>
      </div>
    </div>
  )
}

export default Borrow 