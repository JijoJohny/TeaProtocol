from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, validator
import stripe
import os
from dotenv import load_dotenv
from typing import Optional
import json

# Load environment variables
load_dotenv()

# Initialize Stripe
stripe.api_key = os.getenv('STRIPE_SECRET_KEY')

# Default Algorand wallet address
DEFAULT_ALGO_WALLET = 'QW5L3VD2RIFAKB33I6DCQAMZUSYSS2B5IW4GBQM7T7KSJWANU3ONHUFMTI'

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
    algo_address: str
    payment_method_id: Optional[str] = None

    @validator('algo_address')
    def validate_algo_address(cls, v):
        # For now, accept any Algorand address
        if not v or len(v) < 10:  # Basic validation
            raise ValueError('Invalid Algorand wallet address')
        return v

class PreauthorizationResponse(BaseModel):
    client_secret: str
    payment_intent_id: str
    status: str

@app.post("/create-payment-intent", response_model=PreauthorizationResponse)
async def create_payment_intent(request: Request):
    try:
        # Log raw request body
        body = await request.body()
        print("Raw request body:", body.decode())
        
        # Parse and validate request
        data = await request.json()
        print("Parsed request data:", data)
        
        # Create request model
        payment_request = PreauthorizationRequest(**data)
        print("Validated request:", payment_request.dict())
        
        # Create payment intent parameters
        intent_params = {
            "amount": payment_request.amount,
            "currency": payment_request.currency,
            "metadata": {
                "algo_address": payment_request.algo_address,
                "type": "preauthorization"
            },
            "capture_method": "manual",  # This makes it a preauthorization
            "setup_future_usage": "off_session"  # Allows future charges without user interaction
        }

        # Add payment method if provided
        if payment_request.payment_method_id:
            intent_params["payment_method"] = payment_request.payment_method_id
            intent_params["confirm"] = True

        # Create a PaymentIntent
        intent = stripe.PaymentIntent.create(**intent_params)

        return PreauthorizationResponse(
            client_secret=intent.client_secret,
            payment_intent_id=intent.id,
            status=intent.status
        )
    except json.JSONDecodeError as e:
        print(f"JSON decode error: {str(e)}")
        raise HTTPException(status_code=400, detail="Invalid JSON in request body")
    except ValueError as e:
        print(f"Validation error: {str(e)}")
        raise HTTPException(status_code=422, detail=str(e))
    except stripe.error.StripeError as e:
        print(f"Stripe error: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        print(f"Unexpected error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

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
        print(f"Attempting to capture payment: {payment_intent_id}")
        
        # Get the payment intent first to check its status
        try:
            payment_intent = stripe.PaymentIntent.retrieve(payment_intent_id)
            print(f"Payment intent retrieved successfully. Status: {payment_intent.status}")
            print(f"Payment method: {payment_intent.payment_method}")
        except stripe.error.StripeError as e:
            print(f"Error retrieving payment intent: {str(e)}")
            raise HTTPException(
                status_code=400,
                detail={
                    "error": "Failed to retrieve payment intent",
                    "code": "retrieve_failed",
                    "message": str(e)
                }
            )
        
        # Check if the payment intent has a payment method attached
        if not payment_intent.payment_method:
            print("No payment method attached to payment intent")
            raise HTTPException(
                status_code=400,
                detail={
                    "error": "No payment method attached",
                    "code": "no_payment_method",
                    "message": "Please provide payment details before capturing"
                }
            )
        
        if payment_intent.status == 'requires_payment_method':
            print("Payment requires payment method")
            raise HTTPException(
                status_code=400,
                detail={
                    "error": "Payment requires a payment method",
                    "code": "payment_requires_method",
                    "message": "Please provide payment details before capturing"
                }
            )
        
        if payment_intent.status != 'requires_capture':
            print(f"Invalid payment status for capture: {payment_intent.status}")
            raise HTTPException(
                status_code=400,
                detail={
                    "error": f"Cannot capture payment in status: {payment_intent.status}",
                    "code": "invalid_payment_status",
                    "message": f"Payment must be in 'requires_capture' status to be captured"
                }
            )

        # Capture the payment
        try:
            print("Attempting to capture payment...")
            captured_payment = stripe.PaymentIntent.capture(
                payment_intent_id,
                payment_method=payment_intent.payment_method
            )
            print(f"Payment captured successfully: {captured_payment.id}")
            
            return {
                "success": True,
                "paymentIntent": {
                    "id": captured_payment.id,
                    "status": captured_payment.status,
                    "amount": captured_payment.amount,
                    "currency": captured_payment.currency
                }
            }
        except stripe.error.StripeError as e:
            print(f"Stripe error during capture: {str(e)}")
            error_detail = {
                "error": str(e),
                "code": getattr(e, 'code', 'unknown_error'),
                "message": getattr(e, 'message', 'An error occurred while capturing the payment')
            }
            raise HTTPException(status_code=400, detail=error_detail)
            
    except HTTPException:
        # Re-raise HTTP exceptions as they are already properly formatted
        raise
    except Exception as e:
        print(f"Unexpected error capturing payment: {str(e)}")
        print(f"Error type: {type(e)}")
        import traceback
        print(f"Traceback: {traceback.format_exc()}")
        raise HTTPException(
            status_code=500,
            detail={
                "error": str(e),
                "code": "internal_error",
                "message": "An unexpected error occurred while processing the payment"
            }
        )

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