# Stripe Preauthorization System

This implementation provides a Stripe preauthorization system that allows users to preauthorize their credit cards for use as collateral in the 0xCollateral protocol.

## Features

- Create payment intents for preauthorization
- Handle Stripe webhooks for payment status updates
- Manage payment captures and cancellations
- Store Ethereum addresses in payment metadata
- Secure webhook handling with signature verification

## Setup

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Create a `.env` file based on `.env.example`:
```bash
cp .env.example .env
```

3. Fill in your Stripe API keys in the `.env` file:
- Get your Stripe secret key from the Stripe Dashboard
- Set up a webhook endpoint in the Stripe Dashboard and get the webhook secret

## Running the Services

1. Start the main API server:
```bash
python main.py
```

2. Start the webhook handler (in a separate terminal):
```bash
python webhook_handler.py
```

## API Endpoints

### Main API (Port 8000)

1. Create Payment Intent
```http
POST /create-payment-intent
{
    "amount": 1000,
    "currency": "usd",
    "eth_address": "0x...",
    "payment_method_id": "pm_..."
}
```

2. Get Payment Intent Status
```http
GET /payment-intent/{payment_intent_id}
```

3. Capture Payment
```http
POST /capture-payment/{payment_intent_id}
```

4. Cancel Payment
```http
POST /cancel-payment/{payment_intent_id}
```

### Webhook Handler (Port 8001)

```http
POST /webhook
```

## Integration with 0xCollateral

This implementation works with the 0xCollateral protocol by:

1. Creating preauthorized payment intents with user's Ethereum address
2. Storing the payment intent ID and status
3. Allowing the Vlayer system to verify the preauthorization
4. Enabling the lending pool to use the preauthorized amount as collateral

## Security Considerations

1. Always use HTTPS in production
2. Keep your Stripe API keys secure
3. Verify webhook signatures
4. Implement proper error handling
5. Use environment variables for sensitive data

## Development

To run tests (when implemented):
```bash
pytest
```

## Contributing

1. Fork the repository
2. Create a feature branch
3. Commit your changes
4. Push to the branch
5. Create a Pull Request 