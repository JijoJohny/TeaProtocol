# Vlayer Setup Guide

## Prerequisites

1. Python 3.8 or higher
2. Algorand Node (local or testnet)
3. Stripe Account
4. PostgreSQL (optional, for database storage)

## Step 1: Environment Setup

1. Create a virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Create and configure `.env` file:
```bash
cp .env.example .env
```

Fill in the following values in your `.env` file:

### Stripe Configuration
- Get your `STRIPE_SECRET_KEY` from the Stripe Dashboard
- Set up a webhook endpoint in Stripe Dashboard and get `STRIPE_WEBHOOK_SECRET`

### Algorand Configuration
- `ALGOD_ADDRESS`: Your Algorand node address
- `ALGOD_TOKEN`: Your node token
- `ADMIN_ADDRESS`: Your Algorand admin address
- `ADMIN_PRIVATE_KEY`: Your admin private key

## Step 2: Deploy Smart Contracts

1. Compile the contracts:
```bash
python contracts/vlayer_prover.py
python contracts/vlayer_verifier.py
```

2. Deploy using Algorand CLI:
```bash
# Deploy Vlayer Prover
goal app create --creator $ADMIN_ADDRESS \
    --approval-prog vlayer_prover_approval.teal \
    --clear-prog vlayer_prover_clear.teal \
    --local-ints 1 \
    --local-bytes 1 \
    --global-ints 1 \
    --global-bytes 1

# Note the Application ID and update VLAYER_PROVER_APP_ID in .env

# Deploy Vlayer Verifier
goal app create --creator $ADMIN_ADDRESS \
    --approval-prog vlayer_verifier_approval.teal \
    --clear-prog vlayer_verifier_clear.teal \
    --local-ints 1 \
    --local-bytes 1 \
    --global-ints 1 \
    --global-bytes 1

# Note the Application ID and update VLAYER_VERIFIER_APP_ID in .env
```

## Step 3: Run the Application

1. Start the API server:
```bash
python main.py
```

2. Test the endpoints:
```bash
# Create a payment intent
curl -X POST http://localhost:8000/create-payment-intent \
    -H "Content-Type: application/json" \
    -d '{
        "amount": 1000,
        "currency": "usd",
        "algo_address": "YOUR_ALGO_ADDRESS",
        "payment_method_id": "pm_..."
    }'

# Verify a proof
curl http://localhost:8000/verify-proof/{proof_id}
```

## Next Steps for Implementation

### 1. Database Integration
- [ ] Set up PostgreSQL database
- [ ] Create database models for:
  - [ ] Payment intents
  - [ ] Proofs
  - [ ] User collateral
  - [ ] Transaction history

### 2. Frontend Development
- [ ] Create React/Next.js frontend
- [ ] Implement:
  - [ ] Payment form
  - [ ] Algorand wallet connection
  - [ ] Proof verification UI
  - [ ] Transaction history

### 3. Security Enhancements
- [ ] Implement JWT authentication
- [ ] Add rate limiting
- [ ] Set up HTTPS
- [ ] Add input validation
- [ ] Implement audit logging

### 4. Testing
- [ ] Unit tests for smart contracts
- [ ] Integration tests for API
- [ ] End-to-end tests
- [ ] Security testing

### 5. Monitoring and Logging
- [ ] Set up logging system
- [ ] Implement monitoring
- [ ] Add error tracking
- [ ] Set up alerts

### 6. Documentation
- [ ] API documentation
- [ ] Smart contract documentation
- [ ] Deployment guide
- [ ] User guide

### 7. Additional Features
- [ ] Support for multiple currencies
- [ ] Batch processing
- [ ] Admin dashboard
- [ ] Analytics

## Troubleshooting

### Common Issues

1. Algorand Node Connection
```bash
# Check node status
goal node status
```

2. Stripe Webhook Testing
```bash
# Install Stripe CLI
stripe listen --forward-to localhost:8000/webhook
```

3. Contract Deployment Issues
```bash
# Check contract state
goal app info --app-id $VLAYER_PROVER_APP_ID
goal app info --app-id $VLAYER_VERIFIER_APP_ID
```

## Support

For issues and questions:
1. Check the documentation
2. Open an issue on GitHub
3. Contact the development team 