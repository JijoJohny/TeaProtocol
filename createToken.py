from algosdk import account, mnemonic, transaction
from algosdk.v2client import algod
import os
from dotenv import load_dotenv
import requests
import json
from algosdk.transaction import Multisig, MultisigTransaction

load_dotenv()

def create_multisig_account():
    """Initialize a multisig account from environment variables"""
    addresses = [
        os.getenv("MULTISIG_ADDRESS_1"),
        os.getenv("MULTISIG_ADDRESS_2"),
        os.getenv("MULTISIG_ADDRESS_3")
    ]
    threshold = int(os.getenv("MULTISIG_THRESHOLD", 2))
    
    msig = Multisig(
        version=1,
        threshold=threshold,
        addresses=addresses
    )
    
    print(f"🔐 Multisig Account Created")
    print(f"Address: {msig.address()}")
    print(f"Threshold: {threshold}/{len(addresses)}")
    print(f"Signers: {addresses}")
    
    return msig

def create_vusd_token():
    """Create VUSD token with multisig-controlled roles"""
    try:
        # Initialize clients
        algod_client = algod.AlgodClient(
            algod_token=os.getenv("ALGOD_TOKEN"),
            algod_address=os.getenv("ALGOD_SERVER")
        )

        # Setup creator and multisig
        creator_private_key = mnemonic.to_private_key(os.getenv("CREATOR_MNEMONIC"))
        creator_address = account.address_from_private_key(creator_private_key)
        msig = create_multisig_account()

        # Token parameters
        total_units = 1_000_000_000  # 10 million with 2 decimals
        decimals = 2
        unit_name = "VUSD"
        asset_name = "Vlayer USD"

        # Create transaction with multisig as all privileged roles
        txn = transaction.AssetCreateTxn(
            sender=creator_address,
            sp=algod_client.suggested_params(),
            total=total_units,
            decimals=decimals,
            asset_name=asset_name,
            unit_name=unit_name,
            url="https://vlayer.io/vusd_metadata.json",
            manager=msig.address(),    # Multisig controls management
            reserve=msig.address(),    # Multisig controls reserve
            freeze=msig.address(),     # Multisig controls freezing
            clawback=msig.address(),   # Multisig controls clawback
            default_frozen=False
        )

        # Sign and submit
        signed_txn = txn.sign(creator_private_key)
        tx_id = algod_client.send_transaction(signed_txn)
        print(f"📤 Submitted TX ID: {tx_id}")

        # Wait for confirmation
        confirmed_txn = transaction.wait_for_confirmation(algod_client, tx_id, 4)
        asset_id = confirmed_txn["asset-index"]

        print(f"\n✅ VUSD Token Created with Multisig Control!")
        print(f"Asset ID: {asset_id}")
        print(f"Manager: {msig.address()}")
        print(f"Clawback: {msig.address()}")
        return asset_id, msig.address()

    except Exception as e:
        print(f"\n❌ Token creation failed: {str(e)}")
        return None, None

def send_vusd_tokens(asset_id, sender_address, sender_private_key, receiver_address, amount):
    """Send VUSD tokens to any address"""
    try:
        algod_client = algod.AlgodClient(
            algod_token=os.getenv("ALGOD_TOKEN"),
            algod_address=os.getenv("ALGOD_SERVER")
        )

        # Create transfer transaction
        txn = transaction.AssetTransferTxn(
            sender=sender_address,
            sp=algod_client.suggested_params(),
            receiver=receiver_address,
            amt=amount,
            index=asset_id
        )

        # Sign and submit
        signed_txn = txn.sign(sender_private_key)
        tx_id = algod_client.send_transaction(signed_txn)
        print(f"📤 Submitted Transfer TX ID: {tx_id}")

        # Wait for confirmation
        transaction.wait_for_confirmation(algod_client, tx_id, 4)
        print(f"\n✅ Successfully sent {amount} VUSD to {receiver_address}")
        return tx_id

    except Exception as e:
        print(f"\n❌ Token transfer failed: {str(e)}")
        return None

def send_vusd_multisig(asset_id, msig, receiver_address, amount, signers_private_keys):
    """Send VUSD tokens using multisig authorization"""
    try:
        algod_client = algod.AlgodClient(
            algod_token=os.getenv("ALGOD_TOKEN"),
            algod_address=os.getenv("ALGOD_SERVER")
        )

        # Create transfer transaction
        txn = transaction.AssetTransferTxn(
            sender=msig.address(),
            sp=algod_client.suggested_params(),
            receiver=receiver_address,
            amt=amount,
            index=asset_id
        )

        # Convert to multisig transaction
        mtx = MultisigTransaction(txn, msig)
        
        # Sign with required threshold
        for priv_key in signers_private_keys:
            mtx.sign(priv_key)

        # Submit
        tx_id = algod_client.send_transaction(mtx)
        print(f"📤 Submitted Multisig Transfer TX ID: {tx_id}")

        # Wait for confirmation
        transaction.wait_for_confirmation(algod_client, tx_id, 4)
        print(f"\n✅ Successfully sent {amount} VUSD from multisig to {receiver_address}")
        return tx_id

    except Exception as e:
        print(f"\n❌ Multisig token transfer failed: {str(e)}")
        return None

def upload_metadata_to_pinata(asset_id):
    """Upload asset metadata to IPFS"""
    metadata = {
        "name": "Vlayer USD",
        "unitName": "VUSD",
        "description": "Stablecoin issued by Tea Protocol",
        "image": "ipfs://bafkreigp3estjktgtrau2yei2w7rbtl5lj5uon6cv2hnlae4t37xbmo4ey",
        "decimals": 2,
        "assetId": asset_id,
        "properties": {
            "peg": "usd",
            "issuer": "Vlayer"
        }
    }

    try:
        headers = {
            "Authorization": os.getenv("PINATA_JWT"),
            "Content-Type": "application/json"
        }

        response = requests.post(
            "https://api.pinata.cloud/pinning/pinJSONToIPFS",
            json=metadata,
            headers=headers
        )

        if response.status_code == 200:
            ipfs_hash = response.json()["IpfsHash"]
            ipfs_url = f"https://gateway.pinata.cloud/ipfs/{ipfs_hash}"
            print(f"\n📦 Metadata uploaded to IPFS via Pinata!")
            print(f"IPFS CID: {ipfs_hash}")
            print(f"✅ View JSON: {ipfs_url}")
            return ipfs_url
        else:
            print(f"⚠️ Upload failed: {response.text}")
    except Exception as e:
        print(f"❌ Pinata upload error: {str(e)}")
    return None

if __name__ == "__main__":
    # Deploy with multisig control
    asset_id, msig_address = create_vusd_token()
    
    if asset_id:
        # Update environment file
        with open(".env", "a") as f:
            f.write(f"\nVUSD_ASSET_ID={asset_id}")
            f.write(f"\nVUSD_MULTISIG_ADDRESS={msig_address}")
        
        # Upload metadata (optional)
        ipfs_url = upload_metadata_to_pinata(asset_id)
        if ipfs_url:
            with open(".env", "a") as f:
                f.write(f"\nVUSD_METADATA_URL={ipfs_url}")
        
        # Example: Send initial tokens (using creator account)
        receiver = input("Enter receiver address for initial token distribution: ")
        amount = int(input("Enter amount of VUSD to send (in smallest units): "))
        
        creator_private_key = mnemonic.to_private_key(os.getenv("CREATOR_MNEMONIC"))
        creator_address = account.address_from_private_key(creator_private_key)
        
        send_vusd_tokens(
            asset_id=asset_id,
            sender_address=creator_address,
            sender_private_key=creator_private_key,
            receiver_address=receiver,
            amount=amount
        )
        
        # Example: Send tokens using multisig (requires multiple signers)
        if input("Send additional tokens using multisig? (y/n): ").lower() == 'y':
            receiver = input("Enter receiver address: ")
            amount = int(input("Enter amount of VUSD to send: "))
            
            # Get signers (in production, these would come from secure storage)
            signers = [
                mnemonic.to_private_key(os.getenv("MULTISIG_MNEMONIC_1")),
                mnemonic.to_private_key(os.getenv("MULTISIG_MNEMONIC_2"))
            ]
            
            send_vusd_multisig(
                asset_id=asset_id,
                msig=create_multisig_account(),
                receiver_address=receiver,
                amount=amount,
                signers_private_keys=signers
            )