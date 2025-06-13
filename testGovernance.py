import os
from algosdk import account, mnemonic, transaction
from algosdk.v2client import algod
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

class VUSDTester:
    def __init__(self):
        # Initialize Algod client
        self.algod_client = algod.AlgodClient(
            algod_token=os.getenv("ALGOD_TOKEN"),
            algod_address=os.getenv("ALGOD_SERVER")
        )
        
        # Load asset and control addresses
        self.asset_id = int(os.getenv("VUSD_ASSET_ID"))
        self.roles = {
            'manager': os.getenv("MANAGER"),
            'reserve': os.getenv("RESERVE"),
            'freeze': os.getenv("FREEZE"),
            'clawback': os.getenv("CLAWBACK")
        }
        
        # Test accounts
        self.test_account = os.getenv("TEST_ACCOUNT")
        self.test_account_pk = mnemonic.to_private_key(os.getenv("TEST_ACCOUNT_MNEMONIC"))

    def get_asset_balance(self, address):
        """Get VUSD balance for an address"""
        account_info = self.algod_client.account_info(address)
        for asset in account_info.get('assets', []):
            if asset['asset-id'] == self.asset_id:
                return asset['amount']
        return 0

    def test_manager_role(self):
        """Verify manager can update roles"""
        print("\n=== Testing Manager Role ===")
        
        # 1. Rotate freeze address to a new temporary address
        new_freeze = account.generate_account()[1]
        print(f"Rotating freeze address to: {new_freeze}")
        
        txn = transaction.AssetConfigTxn(
    sender=self.roles['manager'],
    sp=self.algod_client.suggested_params(),
    index=self.asset_id,
    manager=self.roles['manager'],
    reserve=self.roles['reserve'],
    freeze=new_freeze,
    clawback=self.roles['clawback']
    )

        signed = txn.sign(mnemonic.to_private_key(os.getenv("MANAGER_MNEMONIC")))
        tx_id = self.algod_client.send_transaction(signed)
        transaction.wait_for_confirmation(self.algod_client, tx_id, 4)
        
        # 2. Verify the change
        asset_info = self.algod_client.asset_info(self.asset_id)
        assert asset_info['params']['freeze'] == new_freeze, "Manager role failed"
        
        # 3. Revert changes (cleanup)
        revert_txn = transaction.AssetConfigTxn(
    sender=self.roles['manager'],
    sp=self.algod_client.suggested_params(),
    index=self.asset_id,
    manager=self.roles['manager'],
    reserve=self.roles['reserve'],
    freeze=self.roles['freeze'],
    clawback=self.roles['clawback']
)

        signed_revert = revert_txn.sign(mnemonic.to_private_key(os.getenv("MANAGER_MNEMONIC")))
        self.algod_client.send_transaction(signed_revert)
        
        print("✓ Manager role verified - Freeze address updated successfully")

    def test_freeze_role(self):
        """Verify freeze/unfreeze functionality"""
        print("\n=== Testing Freeze Role ===")
        
        # 1. Freeze test account
        freeze_txn = transaction.AssetFreezeTxn(
            sender=self.roles['freeze'],
            sp=self.algod_client.suggested_params(),
            index=self.asset_id,
            target=self.test_account,
            new_freeze_state=True
        )
        signed_freeze = freeze_txn.sign(mnemonic.to_private_key(os.getenv("FREEZE_MNEMONIC")))
        self.algod_client.send_transaction(signed_freeze)
        
        # 2. Verify freeze status
        account_info = self.algod_client.account_info(self.test_account)
        is_frozen = any(
            asset['is-frozen'] 
            for asset in account_info.get('assets', []) 
            if asset['asset-id'] == self.asset_id
        )
        assert is_frozen, "Freeze operation failed"
        
        # 3. Try to send from frozen account (should fail)
        try:
            send_txn = transaction.AssetTransferTxn(
                sender=self.test_account,
                sp=self.algod_client.suggested_params(),
                receiver=self.roles['reserve'],
                amt=100,  # 1.00 VUSD
                index=self.asset_id
            )
            signed_send = send_txn.sign(self.test_account_pk)
            self.algod_client.send_transaction(signed_send)
            assert False, "Transaction should have failed on frozen account"
        except Exception as e:
            assert "asset frozen" in str(e).lower(), f"Unexpected error: {e}"
        
        # 4. Unfreeze (cleanup)
        unfreeze_txn = transaction.AssetFreezeTxn(
            sender=self.roles['freeze'],
            sp=self.algod_client.suggested_params(),
            index=self.asset_id,
            target=self.test_account,
            new_freeze_state=False
        )
        signed_unfreeze = unfreeze_txn.sign(mnemonic.to_private_key(os.getenv("FREEZE_MNEMONIC")))
        self.algod_client.send_transaction(signed_unfreeze)
        
        print("✓ Freeze role verified - Account frozen and thawed successfully")

    def test_clawback_role(self):
        """Verify clawback functionality"""
        print("\n=== Testing Clawback Role ===")
        
        # 1. Get initial balances
        initial_reserve = self.get_asset_balance(self.roles['reserve'])
        initial_test = self.get_asset_balance(self.test_account)
        clawback_amount = 100  # 1.00 VUSD
        
        # 2. Execute clawback
        clawback_txn = transaction.AssetTransferTxn(
            sender=self.roles['clawback'],
            sp=self.algod_client.suggested_params(),
            receiver=self.roles['reserve'],
            amt=clawback_amount,
            index=self.asset_id,
            revocation_target=self.test_account
        )
        signed_clawback = clawback_txn.sign(mnemonic.to_private_key(os.getenv("CLAWBACK_MNEMONIC")))
        self.algod_client.send_transaction(signed_clawback)
        
        # 3. Verify balances
        new_reserve = self.get_asset_balance(self.roles['reserve'])
        new_test = self.get_asset_balance(self.test_account)
        
        assert new_test == initial_test - clawback_amount, "Clawback didn't deduct from target"
        assert new_reserve == initial_reserve + clawback_amount, "Clawback didn't add to reserve"
        
        print("✓ Clawback role verified - Tokens recovered successfully")

    def run_all_tests(self):
        """Execute all role tests"""
        try:
            self.test_manager_role()
            self.test_freeze_role()
            self.test_clawback_role()
            print("\n✅ All control role tests passed successfully!")
        except Exception as e:
            print(f"\n❌ Test failed: {str(e)}")
            raise

if __name__ == "__main__":
    # Verify environment setup
    required_vars = [
        'ALGOD_TOKEN', 'ALGOD_SERVER', 'VUSD_ASSET_ID',
        'MANAGER', 'RESERVE', 'FREEZE', 'CLAWBACK',
        'MANAGER_MNEMONIC', 'FREEZE_MNEMONIC', 'CLAWBACK_MNEMONIC',
        'TEST_ACCOUNT', 'TEST_ACCOUNT_MNEMONIC'
    ]
    
    missing = [var for var in required_vars if not os.getenv(var)]
    if missing:
        print(f"Missing environment variables: {', '.join(missing)}")
        exit(1)
    
    tester = VUSDTester()
    tester.run_all_tests()