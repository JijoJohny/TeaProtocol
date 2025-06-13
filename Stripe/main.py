from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import stripe
import os
from dotenv import load_dotenv
from typing import Optional

# Load environment variables
load_dotenv()

# Initialize Stripe
stripe.api_key = os.getenv('STRIPE_SECRET_KEY')

app = FastAPI(title="Stripe Preauthorization API")

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class PreauthorizationRequest(BaseModel):
    amount: int
    currency: str = "usd"
    eth_address: str
    payment_method_id: str

class PreauthorizationResponse(BaseModel):
    client_secret: str
    payment_intent_id: str
    status: str

@app.post("/create-payment-intent", response_model=PreauthorizationResponse)
async def create_payment_intent(request: PreauthorizationRequest):
    try:
        # Create a PaymentIntent with the specified amount and currency
        intent = stripe.PaymentIntent.create(
            amount=request.amount,
            currency=request.currency,
            payment_method=request.payment_method_id,
            confirm=True,
            metadata={
                "eth_address": request.eth_address,
                "type": "preauthorization"
            },
            capture_method="manual",  # This makes it a preauthorization
            setup_future_usage="off_session"  # Allows future charges without user interaction
        )

        return PreauthorizationResponse(
            client_secret=intent.client_secret,
            payment_intent_id=intent.id,
            status=intent.status
        )
    except stripe.error.StripeError as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.get("/payment-intent/{payment_intent_id}")
async def get_payment_intent(payment_intent_id: str):
    try:
        intent = stripe.PaymentIntent.retrieve(payment_intent_id)
        return {
            "id": intent.id,
            "amount": intent.amount,
            "currency": intent.currency,
            "status": intent.status,
            "metadata": intent.metadata,
            "amount_capturable": intent.amount_capturable
        }
    except stripe.error.StripeError as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.post("/capture-payment/{payment_intent_id}")
async def capture_payment(payment_intent_id: str):
    try:
        intent = stripe.PaymentIntent.capture(payment_intent_id)
        return {
            "id": intent.id,
            "status": intent.status,
            "amount_captured": intent.amount_captured
        }
    except stripe.error.StripeError as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.post("/cancel-payment/{payment_intent_id}")
async def cancel_payment(payment_intent_id: str):
    try:
        intent = stripe.PaymentIntent.cancel(payment_intent_id)
        return {
            "id": intent.id,
            "status": intent.status
        }
    except stripe.error.StripeError as e:
        raise HTTPException(status_code=400, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000) 