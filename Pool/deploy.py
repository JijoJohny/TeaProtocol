from algosdk.v2client import algod
from algosdk.future.transaction import ApplicationCreateTxn, OnComplete
from algosdk import account, mnemonic
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def get_algod_client():
    """Initialize and return Algorand client"""
    algod_address = os.getenv("ALGOD_ADDRESS")
    algod_token = os.getenv("ALGOD_TOKEN")
    return algod.AlgodClient(algod_token, algod_address)

def deploy_contract(client, creator_private_key, approval_program, clear_program):
    """Deploy a contract and return its application ID"""
    # Get suggested parameters
    params = client.suggested_params()
    
    # Create unsigned transaction
    txn = ApplicationCreateTxn(
        sender=account.address_from_private_key(creator_private_key),
        sp=params,
        on_complete=OnComplete.NoOpOC,
        approval_program=approval_program,
        clear_program=clear_program,
        global_schema=None,
        local_schema=None
    )
    
    # Sign transaction
    signed_txn = txn.sign(creator_private_key)
    
    # Submit transaction
    tx_id = client.send_transaction(signed_txn)
    
    # Wait for confirmation
    try:
        transaction_response = client.wait_for_confirmation(tx_id, 5)
        app_id = transaction_response['application-index']
        print(f"Created app with id: {app_id}")
        return app_id
    except Exception as e:
        print(f"Error deploying contract: {e}")
        return None

def main():
    # Initialize client
    client = get_algod_client()
    
    # Get creator's private key
    creator_private_key = mnemonic.to_private_key(os.getenv("ADMIN_MNEMONIC"))
    
    # Read contract files
    with open("contracts/pool_approval.teal", "r") as f:
        pool_approval = f.read()
    with open("contracts/pool_clear.teal", "r") as f:
        pool_clear = f.read()
    
    with open("contracts/token_approval.teal", "r") as f:
        token_approval = f.read()
    with open("contracts/token_clear.teal", "r") as f:
        token_clear = f.read()
    
    # Deploy pool contract
    print("Deploying pool contract...")
    pool_app_id = deploy_contract(client, creator_private_key, pool_approval, pool_clear)
    
    # Deploy token contract
    print("Deploying token contract...")
    token_app_id = deploy_contract(client, creator_private_key, token_approval, token_clear)
    
    if pool_app_id and token_app_id:
        print("\nDeployment successful!")
        print(f"Pool Application ID: {pool_app_id}")
        print(f"Token Application ID: {token_app_id}")
        print("\nPlease update your .env file with these values:")
        print(f"POOL_APP_ID={pool_app_id}")
        print(f"TOKEN_APP_ID={token_app_id}")
    else:
        print("\nDeployment failed. Please check the error messages above.")

if __name__ == "__main__":
    main() 