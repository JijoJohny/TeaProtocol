from fastapi import FastAPI, Request, HTTPException
import stripe
import os
from dotenv import load_dotenv
import json
from typing import Dict, Any

# Load environment variables
load_dotenv()

# Initialize Stripe
stripe.api_key = os.getenv('STRIPE_SECRET_KEY')
webhook_secret = os.getenv('STRIPE_WEBHOOK_SECRET')

app = FastAPI()

@app.post("/webhook")
async def stripe_webhook(request: Request):
    payload = await request.body()
    sig_header = request.headers.get('stripe-signature')

    try:
        event = stripe.Webhook.construct_event(
            payload, sig_header, webhook_secret
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail="Invalid payload")
    except stripe.error.SignatureVerificationError as e:
        raise HTTPException(status_code=400, detail="Invalid signature")

    # Handle the event
    if event['type'] == 'payment_intent.succeeded':
        payment_intent = event['data']['object']
        handle_payment_intent_succeeded(payment_intent)
    elif event['type'] == 'payment_intent.payment_failed':
        payment_intent = event['data']['object']
        handle_payment_intent_failed(payment_intent)
    elif event['type'] == 'payment_intent.canceled':
        payment_intent = event['data']['object']
        handle_payment_intent_canceled(payment_intent)

    return {"status": "success"}

def handle_payment_intent_succeeded(payment_intent: Dict[str, Any]):
    """
    Handle successful payment intent
    """
    # Extract relevant information
    intent_id = payment_intent['id']
    amount = payment_intent['amount']
    eth_address = payment_intent['metadata'].get('eth_address')
    
    # Here you would typically:
    # 1. Update your database
    # 2. Trigger any necessary blockchain interactions
    # 3. Send notifications
    print(f"Payment intent {intent_id} succeeded for {eth_address} with amount {amount}")

def handle_payment_intent_failed(payment_intent: Dict[str, Any]):
    """
    Handle failed payment intent
    """
    intent_id = payment_intent['id']
    eth_address = payment_intent['metadata'].get('eth_address')
    
    # Handle the failure (e.g., notify user, update database)
    print(f"Payment intent {intent_id} failed for {eth_address}")

def handle_payment_intent_canceled(payment_intent: Dict[str, Any]):
    """
    Handle canceled payment intent
    """
    intent_id = payment_intent['id']
    eth_address = payment_intent['metadata'].get('eth_address')
    
    # Handle the cancellation (e.g., update database, notify user)
    print(f"Payment intent {intent_id} canceled for {eth_address}")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001) 