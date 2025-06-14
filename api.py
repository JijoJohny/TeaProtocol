from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional, Dict
from admin_backend import AdminBackend
from user_backend import UserBackend

app = FastAPI(title="VLayer API")

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize backends
admin_backend = AdminBackend()
user_backend = UserBackend()

# Models
class TokenData(BaseModel):
    total_units: int
    decimals: int = 2
    asset_name: str
    unit_name: str
    metadata_url: Optional[str] = None

class WhitelistData(BaseModel):
    event_id: str
    addresses: List[str]
    action: str

class BorrowData(BaseModel):
    wallet_address: str
    amount: int

# Admin endpoints
@app.post("/admin/token/create")
async def create_token(token_data: TokenData):
    asset_id, msig_address = admin_backend.create_token(token_data.dict())
    if not asset_id:
        raise HTTPException(status_code=400, detail="Token creation failed")
    return {"asset_id": asset_id, "msig_address": msig_address}

@app.post("/admin/wallet/freeze/{wallet_address}")
async def freeze_wallet(wallet_address: str):
    success = admin_backend.freeze_wallet(wallet_address)
    if not success:
        raise HTTPException(status_code=400, detail="Freeze operation failed")
    return {"status": "success"}

@app.post("/admin/wallet/unfreeze/{wallet_address}")
async def unfreeze_wallet(wallet_address: str):
    success = admin_backend.unfreeze_wallet(wallet_address)
    if not success:
        raise HTTPException(status_code=400, detail="Unfreeze operation failed")
    return {"status": "success"}

@app.post("/admin/whitelist/manage")
async def manage_whitelist(data: WhitelistData):
    success = admin_backend.manage_whitelist(
        data.event_id,
        data.addresses,
        data.action
    )
    if not success:
        raise HTTPException(status_code=400, detail="Whitelist management failed")
    return {"status": "success"}

@app.get("/admin/pool/status")
async def check_pool_status():
    status = admin_backend.check_pool_status()
    if not status:
        raise HTTPException(status_code=400, detail="Pool status check failed")
    return status

# User endpoints
@app.post("/user/wallet/connect")
async def connect_wallet(wallet_address: str):
    success = user_backend.connect_wallet(wallet_address)
    if not success:
        raise HTTPException(status_code=400, detail="Wallet connection failed")
    return {"status": "success"}

@app.get("/user/whitelist/check/{wallet_address}/{event_id}")
async def check_whitelist(wallet_address: str, event_id: str):
    is_whitelisted = user_backend.check_whitelist_status(wallet_address, event_id)
    return {"is_whitelisted": is_whitelisted}

@app.post("/user/borrow/initiate")
async def initiate_borrow(data: BorrowData):
    client_secret, error = user_backend.initiate_borrow(
        data.wallet_address,
        data.amount
    )
    if error:
        raise HTTPException(status_code=400, detail=error)
    return {"client_secret": client_secret}

@app.post("/user/borrow/verify/{payment_intent_id}")
async def verify_payment(payment_intent_id: str):
    success, error = user_backend.verify_payment_and_lend(payment_intent_id)
    if error:
        raise HTTPException(status_code=400, detail=error)
    return {"status": "success"}

@app.get("/user/borrow/history/{wallet_address}")
async def get_borrow_history(wallet_address: str):
    history = user_backend.get_borrow_history(wallet_address)
    return {"history": history}

@app.get("/user/wallet/balance/{wallet_address}")
async def get_wallet_balance(wallet_address: str):
    balance = user_backend.get_wallet_balance(wallet_address)
    return {"balance": balance}

@app.get("/user/wallet/status/{wallet_address}")
async def get_wallet_status(wallet_address: str):
    status = user_backend.check_wallet_status(wallet_address)
    return status

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000) 