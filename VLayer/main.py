from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import stripe
import os
from dotenv import load_dotenv
from algosdk import account, mnemonic
from algosdk.v2client import algod
from algosdk import transaction
import json

# Load environment variables
load_dotenv()

# Initialize Stripe
stripe.api_key = os.getenv('STRIPE_SECRET_KEY')

# Initialize Algorand client
algod_address = os.getenv('ALGOD_ADDRESS', 'http://localhost:4001')
algod_token = os.getenv('ALGOD_TOKEN', 'aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa')
algod_client = algod.AlgodClient(algod_token, algod_address)

app = FastAPI(title="Algorand Vlayer API")

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
    payment_method_id: str

class PreauthorizationResponse(BaseModel):
    client_secret: str
    payment_intent_id: str
    status: str
    proof_id: str

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
                "algo_address": request.algo_address,
                "type": "preauthorization"
            },
            capture_method="manual",
            setup_future_usage="off_session"
        )

        # Generate Vlayer proof
        proof_id = await generate_vlayer_proof(intent.id, request.algo_address)

        return PreauthorizationResponse(
            client_secret=intent.client_secret,
            payment_intent_id=intent.id,
            status=intent.status,
            proof_id=proof_id
        )
    except stripe.error.StripeError as e:
        raise HTTPException(status_code=400, detail=str(e))

async def generate_vlayer_proof(payment_intent_id: str, algo_address: str) -> str:
    try:
        # Get payment intent details
        intent = stripe.PaymentIntent.retrieve(payment_intent_id)
        
        # Create proof data
        proof_data = {
            "payment_intent_id": payment_intent_id,
            "amount": intent.amount,
            "algo_address": algo_address,
            "status": intent.status
        }

        # Call Vlayer prover contract
        proof_id = await call_vlayer_prover(proof_data)
        
        return proof_id
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error generating proof: {str(e)}")

async def call_vlayer_prover(proof_data: dict) -> str:
    try:
        # Get the Vlayer prover application ID
        prover_app_id = int(os.getenv('VLAYER_PROVER_APP_ID'))
        
        # Create the transaction
        params = algod_client.suggested_params()
        
        # Create the application call transaction
        txn = transaction.ApplicationCallTxn(
            sender=os.getenv('ADMIN_ADDRESS'),
            sp=params,
            index=prover_app_id,
            on_complete=transaction.OnComplete.NoOpOC,
            app_args=['generate_proof'],
            accounts=[proof_data['algo_address']],
            foreign_apps=[],
            foreign_assets=[],
            note=json.dumps(proof_data).encode()
        )
        
        # Sign and submit the transaction
        signed_txn = txn.sign(os.getenv('ADMIN_PRIVATE_KEY'))
        tx_id = algod_client.send_transaction(signed_txn)
        
        # Wait for confirmation
        transaction_response = algod_client.pending_transaction_info(tx_id)
        return transaction_response['txn']['txn']['note'].decode()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error calling Vlayer prover: {str(e)}")

@app.get("/verify-proof/{proof_id}")
async def verify_proof(proof_id: str):
    try:
        # Get the Vlayer verifier application ID
        verifier_app_id = int(os.getenv('VLAYER_VERIFIER_APP_ID'))
        
        # Create the transaction
        params = algod_client.suggested_params()
        
        # Create the application call transaction
        txn = transaction.ApplicationCallTxn(
            sender=os.getenv('ADMIN_ADDRESS'),
            sp=params,
            index=verifier_app_id,
            on_complete=transaction.OnComplete.NoOpOC,
            app_args=['verify_proof'],
            accounts=[],
            foreign_apps=[],
            foreign_assets=[],
            note=proof_id.encode()
        )
        
        # Sign and submit the transaction
        signed_txn = txn.sign(os.getenv('ADMIN_PRIVATE_KEY'))
        tx_id = algod_client.send_transaction(signed_txn)
        
        # Wait for confirmation
        transaction_response = algod_client.pending_transaction_info(tx_id)
        
        return {
            "status": "verified",
            "transaction_id": tx_id,
            "proof_id": proof_id
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error verifying proof: {str(e)}")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000) 