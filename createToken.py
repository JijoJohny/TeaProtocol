from algosdk import account, mnemonic
from algosdk.v2client import algod
from algosdk import transaction
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def create_vusd_token():
    """Create the VUSD token on Algorand using standard algosdk"""
    try:
        # Initialize Algod client
        algod_client = algod.AlgodClient(
            algod_token=os.getenv("ALGOD_TOKEN"),
            algod_address=os.getenv("ALGOD_SERVER")
        )

        # Get creator account
        creator_private_key = mnemonic.to_private_key(os.getenv("CREATOR_MNEMONIC"))
        creator_address = account.address_from_private_key(creator_private_key)
        print(f"Creator address: {creator_address}")

        # Get network suggested params
        params = algod_client.suggested_params()

        # Asset configuration
        txn = transaction.AssetCreateTxn(
            sender=creator_address,
            sp=params,
            total=1_000_000,  # 1 million tokens
            decimals=2,
            asset_name="Vlayer USD",
            unit_name="VUSD",
            url="https://vlayer.io",
            manager=os.getenv("MANAGER"),
            reserve=os.getenv("RESERVE"),
            freeze=os.getenv("FREEZE"),
            clawback=os.getenv("CLAWBACK"),
            default_frozen=False
        )

        print("\nCreating VUSD token with configuration:")
        print(f"Total Supply: 1,000,000")
        print(f"Decimals: 2")
        print(f"Manager: {os.getenv('MANAGER')}")
        print(f"Reserve: {os.getenv('RESERVE')}")
        print(f"Freeze: {os.getenv('FREEZE')}")
        print(f"Clawback: {os.getenv('CLAWBACK')}")

        # Sign and submit transaction
        signed_txn = txn.sign(creator_private_key)
        tx_id = algod_client.send_transaction(signed_txn)
        print(f"\nSubmitted transaction ID: {tx_id}")

        # Wait for confirmation
        confirmed_txn = transaction.wait_for_confirmation(algod_client, tx_id, 4)
        
        print("\nToken created successfully!")
        print(f"Transaction ID: {tx_id}")
        print(f"Asset ID: {confirmed_txn['asset-index']}")

        return confirmed_txn['asset-index']

    except Exception as e:
        print(f"\nError creating token: {str(e)}")
        return None

if __name__ == "__main__":
    create_vusd_token()