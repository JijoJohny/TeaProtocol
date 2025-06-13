from algosdk import transaction
from algosdk.v2client import algod
import os
from dotenv import load_dotenv

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

    def rotate_role(self, role: str, new_address: str, current_manager_mnemonic: str):
        """Rotate control roles (requires manager privileges)"""
        if role not in self.roles:
            raise ValueError(f"Invalid role. Choose from: {list(self.roles.keys())}")
        
        private_key = mnemonic.to_private_key(current_manager_mnemonic)
        
        txn = transaction.AssetConfigTxn(
            sender=account.address_from_private_key(private_key),
            sp=self.algod_client.suggested_params(),
            index=self.asset_id,
            **{role: new_address}
        )
        
        self._submit(txn, private_key, f"Rotate {role} to {new_address}")

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