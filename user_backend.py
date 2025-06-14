from algosdk import account, mnemonic, transaction
from algosdk.v2client import algod
import os
from dotenv import load_dotenv
import json
import stripe
from typing import Dict, Optional, Tuple

load_dotenv()

class UserBackend:
    def __init__(self):
        self.algod_client = algod.AlgodClient(
            algod_token=os.getenv("ALGOD_TOKEN"),
            algod_address=os.getenv("ALGOD_SERVER")
        )
        self.asset_id = int(os.getenv("VUSD_ASSET_ID"))
        self.pool_app_id = int(os.getenv("POOL_APP_ID"))
        self.pool_address = self.algod_client.application_info(self.pool_app_id)["params"]["creator"]
        
        # Initialize Stripe
        stripe.api_key = os.getenv("STRIPE_SECRET_KEY")

    def connect_wallet(self, wallet_address: str) -> bool:
        """
        Connect user's Pera wallet
        """
        try:
            # Verify wallet exists and is valid
            account_info = self.algod_client.account_info(wallet_address)
            return True
        except Exception as e:
            print(f"Wallet connection failed: {str(e)}")
            return False

    def check_whitelist_status(self, wallet_address: str, event_id: str) -> bool:
        """
        Check if wallet is whitelisted for an event
        """
        try:
            whitelist_file = f"whitelists/{event_id}.json"
            if not os.path.exists(whitelist_file):
                return False
            
            with open(whitelist_file, 'r') as f:
                whitelist = json.load(f)
            
            return wallet_address in whitelist
        except Exception as e:
            print(f"Whitelist check failed: {str(e)}")
            return False

    def initiate_borrow(self, wallet_address: str, amount: int) -> Tuple[Optional[str], Optional[str]]:
        """
        Initiate borrowing process
        """
        try:
            # Check pool balance
            pool_info = self.algod_client.account_info(self.pool_address)
            pool_balance = 0
            for asset in pool_info.get('assets', []):
                if asset['asset-id'] == self.asset_id:
                    pool_balance = asset['amount']
                    break

            if pool_balance < amount:
                return None, "Insufficient pool balance"

            # Create Stripe payment intent
            payment_intent = stripe.PaymentIntent.create(
                amount=amount,  # Amount in cents
                currency='usd',
                metadata={
                    'wallet_address': wallet_address,
                    'token_amount': amount
                }
            )

            return payment_intent.client_secret, None

        except Exception as e:
            print(f"Borrow initiation failed: {str(e)}")
            return None, str(e)

    def verify_payment_and_lend(self, payment_intent_id: str) -> Tuple[bool, Optional[str]]:
        """
        Verify Stripe payment and process lending
        """
        try:
            # Verify payment intent
            payment_intent = stripe.PaymentIntent.retrieve(payment_intent_id)
            
            if payment_intent.status != 'succeeded':
                return False, "Payment not successful"

            # Get wallet address and amount from metadata
            wallet_address = payment_intent.metadata.get('wallet_address')
            amount = int(payment_intent.metadata.get('token_amount'))

            # Process lending from pool
            params = self.algod_client.suggested_params()
            
            # Create lending transaction
            lend_txn = transaction.AssetTransferTxn(
                sender=self.pool_address,
                sp=params,
                receiver=wallet_address,
                amt=amount,
                index=self.asset_id
            )

            # Sign with pool's private key
            signed_txn = lend_txn.sign(mnemonic.to_private_key(os.getenv("POOL_PRIVATE_KEY")))
            tx_id = self.algod_client.send_transaction(signed_txn)
            
            # Wait for confirmation
            transaction.wait_for_confirmation(self.algod_client, tx_id, 4)

            return True, None

        except Exception as e:
            print(f"Payment verification and lending failed: {str(e)}")
            return False, str(e)

    def get_borrow_history(self, wallet_address: str) -> list:
        """
        Get borrowing history for a wallet
        """
        try:
            # Query Stripe for payment intents
            payment_intents = stripe.PaymentIntent.list(
                limit=100,
                metadata={'wallet_address': wallet_address}
            )

            history = []
            for intent in payment_intents.data:
                if intent.status == 'succeeded':
                    history.append({
                        'amount': intent.amount,
                        'token_amount': intent.metadata.get('token_amount'),
                        'date': intent.created,
                        'status': 'completed'
                    })

            return history

        except Exception as e:
            print(f"Failed to get borrow history: {str(e)}")
            return []

    def get_wallet_balance(self, wallet_address: str) -> int:
        """
        Get VUSD balance for a wallet
        """
        try:
            account_info = self.algod_client.account_info(wallet_address)
            for asset in account_info.get('assets', []):
                if asset['asset-id'] == self.asset_id:
                    return asset['amount']
            return 0
        except Exception as e:
            print(f"Failed to get wallet balance: {str(e)}")
            return 0

    def check_wallet_status(self, wallet_address: str) -> Dict:
        """
        Check if wallet is frozen or has any restrictions
        """
        try:
            account_info = self.algod_client.account_info(wallet_address)
            is_frozen = False
            
            for asset in account_info.get('assets', []):
                if asset['asset-id'] == self.asset_id:
                    is_frozen = asset.get('is-frozen', False)
                    break

            return {
                'is_frozen': is_frozen,
                'balance': self.get_wallet_balance(wallet_address)
            }
        except Exception as e:
            print(f"Failed to check wallet status: {str(e)}")
            return {'is_frozen': False, 'balance': 0} 