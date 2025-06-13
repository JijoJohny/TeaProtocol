from algosdk import transaction
from algosdk.v2client import algod
import os
from dotenv import load_dotenv
from algosdk.transaction import Multisig, MultisigTransaction
from algosdk import mnemonic
load_dotenv()

class VUSDGovernor:
    def __init__(self):
        self.algod_client = algod.AlgodClient(
            os.getenv("ALGOD_TOKEN"),
            os.getenv("ALGOD_SERVER")
        )
        self.asset_id = int(os.getenv("VUSD_ASSET_ID"))
        self.roles = {
            'manager': os.getenv("MANAGER"),
            'reserve': os.getenv("RESERVE"),
            'freeze': os.getenv("FREEZE"),
            'clawback': os.getenv("CLAWBACK")
        }

    # Initialize multisig
        self.multisig_account = self._setup_multisig()

    def _setup_multisig(self):
        """Create multisig account from env variables"""
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

    def rotate_role_multisig(self, role: str, new_address: str):
        """Update roles using multisig authentication"""
        if role not in self.roles:
            raise ValueError(f"Invalid role. Choose from: {list(self.roles.keys())}")
        
        # Create unsigned transaction
        txn = transaction.AssetConfigTxn(
            sender=self.multisig_account.address(),
            sp=self.algod_client.suggested_params(),
            index=self.asset_id,
            **{role: new_address}
        )
        
        # Convert to multisig transaction
        mtx = MultisigTransaction(txn, self.multisig_account)
        
        # Sign with required threshold
        mtx.sign(mnemonic.to_private_key(os.getenv("MULTISIG_MNEMONIC_1")))
        mtx.sign(mnemonic.to_private_key(os.getenv("MULTISIG_MNEMONIC_2")))
        
        # Submit
        tx_id = self.algod_client.send_transaction(mtx)
        print(f"🔏 Multisig {role} rotation to {new_address} | Tx ID: {tx_id}")
        return tx_id

    def clawback(self, from_address: str, amount: int, clawback_mnemonic: str):
        """Force transfer tokens back to reserve"""
        private_key = mnemonic.to_private_key(clawback_mnemonic)
        
        txn = transaction.AssetTransferTxn(
            sender=self.roles['clawback'],
            sp=self.algod_client.suggested_params(),
            receiver=self.roles['reserve'],
            amt=amount,
            index=self.asset_id,
            revocation_target=from_address
        )
        
        self._submit(txn, private_key, f"Clawback {amount} from {from_address}")

    def _submit(self, txn, private_key: str, description: str):
        signed = txn.sign(private_key)
        tx_id = self.algod_client.send_transaction(signed)
        print(f"{description} | Tx ID: {tx_id}")
        return tx_id

# Example Usage
if __name__ == "__main__":
    governor = VUSDGovernor()
    
    governor.rotate_role_multisig(
        role="manager",
        new_address="QEEPJYJ6ELKHP5ABAPEWFWW25XINWHSTJUJPHICMMGKY323EU7TGF65XNA"
    )

    # Rotate freeze address (requires manager mnemonic)
    governor.rotate_role(
        role="freeze",
        new_address="NEW_FREEZE_ADDRESS",
        current_manager_mnemonic=os.getenv("MANAGER_MNEMONIC")
    )
    
    # Clawback 100 VUSD (requires clawback mnemonic)
    governor.clawback(
        from_address="BORROWER_ADDRESS",
        amount=10000,  # 100.00 VUSD (decimals=2)
        clawback_mnemonic=os.getenv("CLAWBACK_MNEMONIC")
    )