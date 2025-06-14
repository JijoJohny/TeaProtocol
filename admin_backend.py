from algosdk import account, mnemonic, transaction
from algosdk.v2client import algod
import os
from dotenv import load_dotenv
import json
from algosdk.transaction import Multisig, MultisigTransaction
from typing import Dict, List, Optional, Tuple

load_dotenv()

class AdminBackend:
    def __init__(self):
        self.algod_client = algod.AlgodClient(
            algod_token=os.getenv("ALGOD_TOKEN"),
            algod_address=os.getenv("ALGOD_SERVER")
        )
        self.asset_id = int(os.getenv("VUSD_ASSET_ID"))
        self.pool_app_id = int(os.getenv("POOL_APP_ID"))
        self.pool_address = self.algod_client.application_info(self.pool_app_id)["params"]["creator"]
        
        # Initialize roles
        self.roles = {
            'manager': {
                'address': os.getenv("MANAGER"),
                'private_key': mnemonic.to_private_key(os.getenv("MANAGER_MNEMONIC"))
            },
            'freeze': {
                'address': os.getenv("FREEZE"),
                'private_key': mnemonic.to_private_key(os.getenv("FREEZE_MNEMONIC"))
            }
        }

    def create_token(self, token_data: Dict) -> Tuple[Optional[int], Optional[str]]:
        """
        Create a new token with specified parameters
        """
        try:
            # Setup creator and multisig
            creator_private_key = mnemonic.to_private_key(os.getenv("CREATOR_MNEMONIC"))
            creator_address = account.address_from_private_key(creator_private_key)
            msig = self._create_multisig_account()

            # Calculate allocations
            total_units = token_data.get('total_units', 1_000_000_000)
            pool_allocation = int(total_units * 0.75)
            creator_allocation = total_units - pool_allocation

            # Create token
            txn = transaction.AssetCreateTxn(
                sender=creator_address,
                sp=self.algod_client.suggested_params(),
                total=total_units,
                decimals=token_data.get('decimals', 2),
                asset_name=token_data.get('asset_name', 'Vlayer USD'),
                unit_name=token_data.get('unit_name', 'VUSD'),
                url=token_data.get('metadata_url', 'https://vlayer.io/vusd_metadata.json'),
                manager=msig.address(),
                reserve=msig.address(),
                freeze=msig.address(),
                clawback=msig.address(),
                default_frozen=False
            )

            # Sign and submit
            signed_txn = txn.sign(creator_private_key)
            tx_id = self.algod_client.send_transaction(signed_txn)
            confirmed_txn = transaction.wait_for_confirmation(self.algod_client, tx_id, 4)
            asset_id = confirmed_txn["asset-index"]

            # Distribute tokens
            self._distribute_tokens(asset_id, creator_address, pool_allocation, creator_allocation)

            return asset_id, msig.address()

        except Exception as e:
            print(f"Token creation failed: {str(e)}")
            return None, None

    def freeze_wallet(self, wallet_address: str) -> bool:
        """
        Freeze a specific wallet
        """
        try:
            freeze_txn = transaction.AssetFreezeTxn(
                sender=self.roles['freeze']['address'],
                sp=self.algod_client.suggested_params(),
                index=self.asset_id,
                target=wallet_address,
                new_freeze_state=True
            )
            
            signed_freeze = freeze_txn.sign(self.roles['freeze']['private_key'])
            self.algod_client.send_transaction(signed_freeze)
            return True
        except Exception as e:
            print(f"Freeze operation failed: {str(e)}")
            return False

    def unfreeze_wallet(self, wallet_address: str) -> bool:
        """
        Unfreeze a specific wallet
        """
        try:
            unfreeze_txn = transaction.AssetFreezeTxn(
                sender=self.roles['freeze']['address'],
                sp=self.algod_client.suggested_params(),
                index=self.asset_id,
                target=wallet_address,
                new_freeze_state=False
            )
            
            signed_unfreeze = unfreeze_txn.sign(self.roles['freeze']['private_key'])
            self.algod_client.send_transaction(signed_unfreeze)
            return True
        except Exception as e:
            print(f"Unfreeze operation failed: {str(e)}")
            return False

    def manage_whitelist(self, event_id: str, addresses: List[str], action: str) -> bool:
        """
        Manage whitelist for an event
        """
        try:
            # Create or update whitelist in storage
            whitelist_file = f"whitelists/{event_id}.json"
            os.makedirs("whitelists", exist_ok=True)
            
            if os.path.exists(whitelist_file):
                with open(whitelist_file, 'r') as f:
                    whitelist = json.load(f)
            else:
                whitelist = []

            if action == "add":
                whitelist.extend([addr for addr in addresses if addr not in whitelist])
            elif action == "remove":
                whitelist = [addr for addr in whitelist if addr not in addresses]
            
            with open(whitelist_file, 'w') as f:
                json.dump(whitelist, f)
            
            return True
        except Exception as e:
            print(f"Whitelist management failed: {str(e)}")
            return False

    def check_pool_status(self) -> Dict:
        """
        Check pool status and trigger regeneration if needed
        """
        try:
            # Get pool balance
            pool_info = self.algod_client.account_info(self.pool_address)
            pool_balance = 0
            for asset in pool_info.get('assets', []):
                if asset['asset-id'] == self.asset_id:
                    pool_balance = asset['amount']
                    break

            # Calculate percentage
            total_supply = self.algod_client.asset_info(self.asset_id)['params']['total']
            pool_percentage = (pool_balance / total_supply) * 100

            # Check if regeneration is needed
            needs_regeneration = pool_percentage < 5

            return {
                'pool_balance': pool_balance,
                'pool_percentage': pool_percentage,
                'needs_regeneration': needs_regeneration
            }
        except Exception as e:
            print(f"Pool status check failed: {str(e)}")
            return {}

    def _create_multisig_account(self) -> Multisig:
        """Create multisig account"""
        addresses = [
            os.getenv("MULTISIG_ADDRESS_1"),
            os.getenv("MULTISIG_ADDRESS_2"),
            os.getenv("MULTISIG_ADDRESS_3")
        ]
        threshold = int(os.getenv("MULTISIG_THRESHOLD", 2))
        
        return Multisig(
            version=1,
            threshold=threshold,
            addresses=addresses
        )

    def _distribute_tokens(self, asset_id: int, creator_address: str, 
                          pool_allocation: int, creator_allocation: int) -> None:
        """Distribute tokens to pool and creator"""
        params = self.algod_client.suggested_params()
        
        # Create transaction group
        opt_in_txn = transaction.AssetOptInTxn(
            sender=self.pool_address,
            sp=params,
            index=asset_id
        )
        
        pool_transfer_txn = transaction.AssetTransferTxn(
            sender=creator_address,
            sp=params,
            receiver=self.pool_address,
            amt=pool_allocation,
            index=asset_id
        )
        
        creator_transfer_txn = transaction.AssetTransferTxn(
            sender=creator_address,
            sp=params,
            receiver=creator_address,
            amt=creator_allocation,
            index=asset_id
        )
        
        # Group and submit transactions
        gid = transaction.calculate_group_id([opt_in_txn, pool_transfer_txn, creator_transfer_txn])
        opt_in_txn.group = gid
        pool_transfer_txn.group = gid
        creator_transfer_txn.group = gid

        signed_opt_in = opt_in_txn.sign(mnemonic.to_private_key(os.getenv("CREATOR_MNEMONIC")))
        signed_pool_transfer = pool_transfer_txn.sign(mnemonic.to_private_key(os.getenv("CREATOR_MNEMONIC")))
        signed_creator_transfer = creator_transfer_txn.sign(mnemonic.to_private_key(os.getenv("CREATOR_MNEMONIC")))

        group_tx = [signed_opt_in, signed_pool_transfer, signed_creator_transfer]
        self.algod_client.send_transactions(group_tx) 