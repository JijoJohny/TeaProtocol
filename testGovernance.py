import os
from algosdk import account, mnemonic, transaction
from algosdk.v2client import algod
from dotenv import load_dotenv

load_dotenv()

class VUSDTester:
    def __init__(self):
        # Initialize Algod client
        self.algod_client = algod.AlgodClient(
            algod_token=os.getenv("ALGOD_TOKEN"),
            algod_address=os.getenv("ALGOD_SERVER")
        )
        
        # Load asset ID
        self.asset_id = int(os.getenv("VUSD_ASSET_ID"))
        
        # Role accounts - each with their own mnemonic
        self.roles = {
            'manager': {
                'address': os.getenv("MANAGER"),
                'private_key': mnemonic.to_private_key(os.getenv("MANAGER_MNEMONIC"))
            },
            'freeze': {
                'address': os.getenv("FREEZE"), 
                'private_key': mnemonic.to_private_key(os.getenv("FREEZE_MNEMONIC"))
            },
            'clawback': {
                'address': os.getenv("CLAWBACK"),
                'private_key': mnemonic.to_private_key(os.getenv("CLAWBACK_MNEMONIC")) 
            },
            'reserve': {
                'address': os.getenv("RESERVE")
            }
        }
        
        # Test account
        self.test_account = {
            'address': os.getenv("TEST_ACCOUNT"),
            'private_key': mnemonic.to_private_key(os.getenv("TEST_ACCOUNT_MNEMONIC"))
        }

    def get_asset_balance(self, address):
        """Get VUSD balance for an address"""
        account_info = self.algod_client.account_info(address)
        for asset in account_info.get('assets', []):
            if asset['asset-id'] == self.asset_id:
                return asset['amount']
        return 0

    def test_manager_role(self):
        """Test manager can update other roles"""
        print("\n=== Testing Manager Role ===")
        
        try:
            # 1. Create a new temporary freeze address
            new_freeze = account.generate_account()[1]
            print(f"Creating new freeze address: {new_freeze}")
            
            # 2. Update freeze address (must be signed by current manager)
            txn = transaction.AssetConfigTxn(
                sender=self.roles['manager']['address'],
                sp=self.algod_client.suggested_params(),
                index=self.asset_id,
                manager=self.roles['manager']['address'],  # Keep same manager
                freeze=new_freeze,  # Update freeze address
                clawback=self.roles['clawback']['address'],
                strict_empty_address_check=False   # Keep same clawback
            )
            
            signed = txn.sign(self.roles['manager']['private_key'])
            tx_id = self.algod_client.send_transaction(signed)
            transaction.wait_for_confirmation(self.algod_client, tx_id, 4)
            
            # 3. Verify the change
            asset_info = self.algod_client.asset_info(self.asset_id)
            assert asset_info['params']['freeze'] == new_freeze, "Freeze address update failed"
            print("✓ Successfully updated freeze address")
            
            # 4. Revert back to original freeze address
            revert_txn = transaction.AssetConfigTxn(
                sender=self.roles['manager']['address'],
                sp=self.algod_client.suggested_params(),
                index=self.asset_id,
                manager=self.roles['manager']['address'],
                freeze=self.roles['freeze']['address'],
                clawback=self.roles['clawback']['address']
            )
            
            signed_revert = revert_txn.sign(self.roles['manager']['private_key'])
            self.algod_client.send_transaction(signed_revert)
            print("✓ Reverted freeze address back to original")
            
            return True
            
        except Exception as e:
            print(f"❌ Manager test failed: {str(e)}")
            return False

    def test_freeze_role(self):
        """Test freeze account can freeze/unfreeze"""
        print("\n=== Testing Freeze Role ===")
        
        try:
            # 1. Freeze test account
            freeze_txn = transaction.AssetFreezeTxn(
                sender=self.roles['freeze']['address'],
                sp=self.algod_client.suggested_params(),
                index=self.asset_id,
                target=self.test_account['address'],
                new_freeze_state=True
            )
            
            signed_freeze = freeze_txn.sign(self.roles['freeze']['private_key'])
            self.algod_client.send_transaction(signed_freeze)
            
            # 2. Verify freeze status
            account_info = self.algod_client.account_info(self.test_account['address'])
            is_frozen = any(
                asset['is-frozen'] 
                for asset in account_info.get('assets', []) 
                if asset['asset-id'] == self.asset_id
            )
            assert is_frozen, "Freeze operation failed"
            print("✓ Successfully froze test account")
            
            # 3. Unfreeze test account
            unfreeze_txn = transaction.AssetFreezeTxn(
                sender=self.roles['freeze']['address'],
                sp=self.algod_client.suggested_params(),
                index=self.asset_id,
                target=self.test_account['address'],
                new_freeze_state=False
            )
            
            signed_unfreeze = unfreeze_txn.sign(self.roles['freeze']['private_key'])
            self.algod_client.send_transaction(signed_unfreeze)
            print("✓ Successfully unfroze test account")
            
            return True
            
        except Exception as e:
            print(f"❌ Freeze test failed: {str(e)}")
            return False

    def test_clawback_role(self):
        """Test clawback account can reclaim tokens"""
        print("\n=== Testing Clawback Role ===")
        
        try:
            # 1. Get initial balances
            initial_reserve = self.get_asset_balance(self.roles['reserve']['address'])
            initial_test = self.get_asset_balance(self.test_account['address'])
            clawback_amount = 100  # 1.00 VUSD
            
            # 2. Execute clawback
            clawback_txn = transaction.AssetTransferTxn(
                sender=self.roles['clawback']['address'],
                sp=self.algod_client.suggested_params(),
                receiver=self.roles['reserve']['address'],
                amt=clawback_amount,
                index=self.asset_id,
                revocation_target=self.test_account['address']
            )
            
            signed_clawback = clawback_txn.sign(self.roles['clawback']['private_key'])
            self.algod_client.send_transaction(signed_clawback)
            
            # 3. Verify balances
            new_reserve = self.get_asset_balance(self.roles['reserve']['address'])
            new_test = self.get_asset_balance(self.test_account['address'])
            
            assert new_test == initial_test - clawback_amount, "Clawback didn't deduct from target"
            assert new_reserve == initial_reserve + clawback_amount, "Clawback didn't add to reserve"
            print("✓ Successfully clawed back tokens")
            
            return True
            
        except Exception as e:
            print(f"❌ Clawback test failed: {str(e)}")
            return False

    def run_all_tests(self):
        """Run all governance tests"""
        print("=== Starting VUSD Governance Tests ===")
        
        # Verify role accounts are properly configured
        for role in ['manager', 'freeze', 'clawback']:
            derived_address = account.address_from_private_key(self.roles[role]['private_key'])
            assert derived_address == self.roles[role]['address'], \
                f"{role} mnemonic doesn't match {role} address"
        
        test_results = {
            'manager': self.test_manager_role(),
            'freeze': self.test_freeze_role(),
            'clawback': self.test_clawback_role()
        }
        
        if all(test_results.values()):
            print("\n✅ All governance tests passed!")
        else:
            failed = [k for k, v in test_results.items() if not v]
            print(f"\n❌ Failed tests: {', '.join(failed)}")

if __name__ == "__main__":
    # Verify required environment variables
    required_vars = [
        'ALGOD_TOKEN', 'ALGOD_SERVER', 'VUSD_ASSET_ID',
        'MANAGER', 'MANAGER_MNEMONIC',
        'FREEZE', 'FREEZE_MNEMONIC',
        'CLAWBACK', 'CLAWBACK_MNEMONIC',
        'RESERVE',
        'TEST_ACCOUNT', 'TEST_ACCOUNT_MNEMONIC'
    ]
    
    missing = [var for var in required_vars if not os.getenv(var)]
    if missing:
        print(f"Missing environment variables: {', '.join(missing)}")
        exit(1)
    
    tester = VUSDTester()
    tester.run_all_tests()