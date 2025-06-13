from algosdk import account, mnemonic, transaction
from algosdk.v2client import algod
import os
from dotenv import load_dotenv
import requests
import json

load_dotenv()

def create_vusd_token():
    """Create the VUSD fungible token with control roles"""
    try:
        algod_client = algod.AlgodClient(
            algod_token=os.getenv("ALGOD_TOKEN"),
            algod_address=os.getenv("ALGOD_SERVER")
        )

        creator_private_key = mnemonic.to_private_key(os.getenv("CREATOR_MNEMONIC"))
        creator_address = account.address_from_private_key(creator_private_key)
        print(f"\n🔑 Creator address: {creator_address}")

        total_units = 1_000_000_000  # 10 million with 2 decimals
        decimals = 2
        unit_name = "VUSD"
        asset_name = "Vlayer USD"

        txn = transaction.AssetCreateTxn(
            sender=creator_address,
            sp=algod_client.suggested_params(),
            total=total_units,
            decimals=decimals,
            asset_name=asset_name,
            unit_name=unit_name,
            url="https://vlayer.io/vusd_metadata.json",  # updated after IPFS
            manager=os.getenv("MANAGER"),
            reserve=os.getenv("RESERVE"),
            freeze=os.getenv("FREEZE"),
            clawback=os.getenv("CLAWBACK"),
            default_frozen=False
        )

        signed_txn = txn.sign(creator_private_key)
        tx_id = algod_client.send_transaction(signed_txn)
        print(f"📤 Submitted TX ID: {tx_id}")

        confirmed_txn = transaction.wait_for_confirmation(algod_client, tx_id, 4)
        asset_id = confirmed_txn["asset-index"]

        print(f"\n✅ VUSD Token Created!")
        print(f"Asset ID: {asset_id}")
        return asset_id

    except Exception as e:
        print(f"\n❌ Token creation failed: {str(e)}")
        return None

def upload_metadata_to_pinata(asset_id):
    """Upload asset metadata to IPFS via Pinata using JWT"""
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
    asset_id = create_vusd_token()
    if asset_id:
        ipfs_url = upload_metadata_to_pinata(asset_id)
        with open(".env", "a") as f:
            f.write(f"\nVUSD_ASSET_ID={asset_id}")
            if ipfs_url:
                f.write(f"\nVUSD_METADATA_URL={ipfs_url}")
