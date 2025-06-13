from algosdk.v2client import algod
from algosdk import transaction  # Changed from future import
from algosdk import account, mnemonic
import os
from dotenv import load_dotenv
import base64

# Load environment variables
load_dotenv()

def get_algod_client():
    algod_address = os.getenv('ALGOD_ADDRESS', 'https://testnet-api.algonode.cloud')
    algod_token = os.getenv('ALGOD_TOKEN', '')
    return algod.AlgodClient(algod_token, algod_address)

def compile_program(client, source_code):
    compile_response = client.compile(source_code)
    return base64.b64decode(compile_response['result'])

def deploy_contract(client, creator_private_key, approval_program, clear_program):
    # Get suggested parameters
    params = client.suggested_params()
    
    # Get creator address
    creator_address = account.address_from_private_key(creator_private_key)
    
    # Create unsigned transaction
    txn = transaction.ApplicationCreateTxn(
        sender=creator_address,
        sp=params,
        on_complete=transaction.OnComplete.NoOpOC,
        approval_program=approval_program,
        clear_program=clear_program,
        global_schema=transaction.StateSchema(num_uints=1, num_byte_slices=1),
        local_schema=transaction.StateSchema(num_uints=0, num_byte_slices=0)
    )
    
    # Sign transaction
    signed_txn = txn.sign(creator_private_key)
    
    # Submit transaction
    tx_id = client.send_transaction(signed_txn)
    
    # Wait for confirmation
    try:
        transaction.wait_for_confirmation(client, tx_id, 4)
        transaction_response = client.pending_transaction_info(tx_id)
        app_id = transaction_response['application-index']
        print(f"Successfully deployed app with id: {app_id}")
        return app_id
    except Exception as e:
        print(f"Error deploying contract: {e}")
        return None

def main():
    # Initialize client
    client = get_algod_client()
    
    # Get creator account
    creator_private_key = os.getenv('CREATOR_PRIVATE_KEY')
    if not creator_private_key:
        print("Error: CREATOR_PRIVATE_KEY not found in environment variables")
        return
    
    # Read and compile contract files
    try:
        print("Compiling contracts...")
        with open('vlayer_prover_approval.teal', 'r') as f:
            prover_approval_teal = f.read()
            prover_approval = compile_program(client, prover_approval_teal)
            
        with open('vlayer_prover_clear.teal', 'r') as f:
            prover_clear_teal = f.read()
            prover_clear = compile_program(client, prover_clear_teal)
            
        with open('vlayer_verifier_approval.teal', 'r') as f:
            verifier_approval_teal = f.read()
            verifier_approval = compile_program(client, verifier_approval_teal)
            
        with open('vlayer_verifier_clear.teal', 'r') as f:
            verifier_clear_teal = f.read()
            verifier_clear = compile_program(client, verifier_clear_teal)
            
    except FileNotFoundError as e:
        print(f"Error reading contract files: {e}")
        return
    except Exception as e:
        print(f"Error compiling TEAL: {e}")
        return
    
    # Deploy contracts
    print("\nDeploying Vlayer Prover contract...")
    prover_app_id = deploy_contract(client, creator_private_key, prover_approval, prover_clear)
    
    print("\nDeploying Vlayer Verifier contract...")
    verifier_app_id = deploy_contract(client, creator_private_key, verifier_approval, verifier_clear)
    
    if prover_app_id and verifier_app_id:
        print("\nUpdate your .env file with these application IDs:")
        print(f"VLAYER_PROVER_APP_ID={prover_app_id}")
        print(f"VLAYER_VERIFIER_APP_ID={verifier_app_id}")

if __name__ == "__main__":
    main()