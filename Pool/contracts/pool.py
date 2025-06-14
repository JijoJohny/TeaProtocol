from algosdk import account, encoding
from algosdk.v2client import algod
from algosdk import transaction
from algosdk.abi import Contract
import json
import os
import base64

class LiquidityPool:
    def __init__(self, algod_client):
        self.algod_client = algod_client
        self.app_id = None
        self.contract = None
        
        # State variables
        self.total_supply = 0
        self.pool_balance = 0
        self.collateral_factor = 7500  # 75% in basis points
        self.liquidation_bonus = 10500  # 5% bonus (105%)
        self.liquidation_threshold = 8000  # 80%
        self.supported_assets = []
        
        # User state tracking (in a real implementation, this would be on-chain)
        self.user_balances = {}
        self.user_borrows = {}
        self.user_collateral = {}

    def deploy_contract(self, creator_private_key):
        """Deploy the smart contract"""
        creator_address = account.address_from_private_key(creator_private_key)
        
        # Create application transaction
        txn = transaction.ApplicationCreateTxn(
            sender=creator_address,
            sp=self.algod_client.suggested_params(),
            on_complete=transaction.OnComplete.NoOpOC,
            approval_program=self.compile_program("pool_approval.teal"),
            clear_program=self.compile_program("pool_clear.teal"),
            global_schema=transaction.StateSchema(4, 3),  # 4 byteslice, 3 uint
            local_schema=transaction.StateSchema(2, 2)    # 2 byteslice, 2 uint
        )
        
        signed_txn = txn.sign(creator_private_key)
        tx_id = self.algod_client.send_transaction(signed_txn)
        result = transaction.wait_for_confirmation(self.algod_client, tx_id, 4)
        
        self.app_id = result['application-index']
        print(f"Contract deployed with app ID: {self.app_id}")
        return self.app_id

    def compile_program(self, source_path):
        """Compile TEAL program"""
        # Get the directory of the current file
        current_dir = os.path.dirname(os.path.abspath(__file__))
        # Construct the full path to the TEAL file
        teal_path = os.path.join(current_dir, source_path)
        with open(teal_path, "r") as f:
            teal_source = f.read()
        compile_response = self.algod_client.compile(teal_source)
        return base64.b64decode(compile_response['result'])

    def initialize(self, sender_private_key):
        """Initialize contract state"""
        txn = transaction.ApplicationCallTxn(
            sender=account.address_from_private_key(sender_private_key),
            sp=self.algod_client.suggested_params(),
            index=self.app_id,
            on_complete=transaction.OnComplete.NoOpOC,
            app_args=["initialize"]
        )
        signed_txn = txn.sign(sender_private_key)
        tx_id = self.algod_client.send_transaction(signed_txn)
        return transaction.wait_for_confirmation(self.algod_client, tx_id, 4)

    def deposit(self, sender_private_key, amount):
        """Deposit assets into the pool"""
        sender_address = account.address_from_private_key(sender_private_key)
        
        # In a real implementation, you'd transfer assets first
        txn = transaction.ApplicationCallTxn(
            sender=sender_address,
            sp=self.algod_client.suggested_params(),
            index=self.app_id,
            on_complete=transaction.OnComplete.NoOpOC,
            app_args=["deposit", amount]
        )
        signed_txn = txn.sign(sender_private_key)
        tx_id = self.algod_client.send_transaction(signed_txn)
        result = transaction.wait_for_confirmation(self.algod_client, tx_id, 4)
        
        # Update local state tracking
        self.pool_balance += amount
        self.user_balances[sender_address] = self.user_balances.get(sender_address, 0) + amount
        return result

    def borrow(self, sender_private_key, amount):
        """Borrow assets from the pool"""
        sender_address = account.address_from_private_key(sender_private_key)
        
        # Check collateral (simplified)
        collateral_value = self.user_collateral.get(sender_address, 0) * self.collateral_factor / 10000
        if collateral_value < amount:
            raise ValueError("Insufficient collateral")
            
        txn = transaction.ApplicationCallTxn(
            sender=sender_address,
            sp=self.algod_client.suggested_params(),
            index=self.app_id,
            on_complete=transaction.OnComplete.NoOpOC,
            app_args=["borrow", amount]
        )
        signed_txn = txn.sign(sender_private_key)
        tx_id = self.algod_client.send_transaction(signed_txn)
        result = transaction.wait_for_confirmation(self.algod_client, tx_id, 4)
        
        # Update local state tracking
        self.pool_balance -= amount
        self.user_borrows[sender_address] = self.user_borrows.get(sender_address, 0) + amount
        return result

    def liquidate(self, liquidator_private_key, liquidatee_address, amount):
        """Liquidate undercollateralized position"""
        liquidator_address = account.address_from_private_key(liquidator_private_key)
        
        # Check if liquidatee is undercollateralized (simplified)
        collateral_value = self.user_collateral.get(liquidatee_address, 0) * self.collateral_factor / 10000
        if collateral_value >= self.user_borrows.get(liquidatee_address, 0):
            raise ValueError("Account is not undercollateralized")
            
        txn = transaction.ApplicationCallTxn(
            sender=liquidator_address,
            sp=self.algod_client.suggested_params(),
            index=self.app_id,
            on_complete=transaction.OnComplete.NoOpOC,
            app_args=["liquidate", amount],
            accounts=[liquidatee_address]
        )
        signed_txn = txn.sign(liquidator_private_key)
        tx_id = self.algod_client.send_transaction(signed_txn)
        result = transaction.wait_for_confirmation(self.algod_client, tx_id, 4)
        
        # Update local state tracking
        bonus = amount * (self.liquidation_bonus - 10000) / 10000
        self.user_balances[liquidator_address] -= amount
        self.user_borrows[liquidatee_address] -= amount
        self.user_balances[liquidator_address] += bonus
        self.user_balances[liquidatee_address] -= bonus
        
        return result

# Example usage
if __name__ == "__main__":
    # Initialize client
    algod_address = "https://testnet-api.algonode.cloud"
    algod_token = ""
    algod_client = algod.AlgodClient(algod_token, algod_address)
    
    # Create pool instance
    pool = LiquidityPool(algod_client)
    
    # Generate test accounts
    creator_private_key, creator_address = account.generate_account()
    user_private_key, user_address = account.generate_account()
    
    # Fund accounts (in testnet)
    print("Fund these accounts in TestNet Dispenser:")
    print(f"Creator: {creator_address}")
    print(f"User: {user_address}")
    input("Press Enter after funding accounts...")
    
    # Deploy contract
    app_id = pool.deploy_contract(creator_private_key)
    
    # Initialize contract
    pool.initialize(creator_private_key)
    
    # Example deposit
    pool.deposit(user_private_key, 1000000)  # 1 ALGO
    print(f"User balance: {pool.user_balances.get(user_address, 0)}")
    
    # Example borrow (would need collateral first in real implementation)
    # pool.add_collateral(user_private_key, 2000000)  # 2 ALGO collateral
    # pool.borrow(user_private_key, 1000000)  # 1 ALGO