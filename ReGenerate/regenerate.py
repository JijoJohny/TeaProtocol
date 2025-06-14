from pyteal import *
import pyteal as pt
from algosdk import account, mnemonic, transaction
from algosdk.v2client import algod
from algosdk.transaction import ApplicationCreateTxn, ApplicationCallTxn, AssetConfigTxn, OnComplete as SDKOnComplete
import base64
import json
import requests
import os
from datetime import datetime, timedelta
import time

class TokenRegenerator:
    def __init__(self, algod_client, creator_address, creator_private_key):
        self.algod_client = algod_client
        self.creator_address = creator_address
        self.creator_private_key = creator_private_key
        self.app_id = None
        self.original_asset_id = None
        self.metadata_ipfs_url = None

    # PyTeal Approval Program
    def get_approval_program(self):
        program = Cond(
            [Txn.application_id() == Int(0), self.handle_creation()],
            [Txn.on_completion() == pt.OnComplete.NoOp, self.handle_noop()],
            [Txn.on_completion() == pt.OnComplete.OptIn, Return(Int(1))],
            [Txn.on_completion() == pt.OnComplete.CloseOut, Return(Int(1))],
            [Txn.on_completion() == pt.OnComplete.UpdateApplication, Return(Int(0))],
            [Txn.on_completion() == pt.OnComplete.DeleteApplication, Return(Int(0))]
        )
        return compileTeal(program, Mode.Application, version=5)

    def handle_creation(self):
        return Return(Int(1))

    def handle_noop(self):
        method = Txn.application_args[0]
        return Cond(
            [method == Bytes("init"), self.init_contract()],
            [method == Bytes("register"), self.register_user_teal()],
            [method == Bytes("remint"), self.handle_remint()]
        )

    def init_contract(self):
        return Seq([
            Assert(Txn.sender() == Global.creator_address()),
            App.globalPut(Bytes("original_asset"), Btoi(Txn.application_args[1])),
            App.globalPut(Bytes("ipfs_url"), Txn.application_args[2]),
            App.globalPut(Bytes("max_remints"), Btoi(Txn.application_args[3])),
            App.globalPut(Bytes("cooldown"), Btoi(Txn.application_args[4])),
            Return(Int(1))
        ])

    def register_user_teal(self):
        user = Txn.accounts[1]
        return Seq([
            Assert(Txn.sender() == Global.creator_address()),
            App.localPut(user, Bytes("registered"), Int(1)),
            App.localPut(user, Bytes("remint_count"), Int(0)),
            App.localPut(user, Bytes("last_remint"), Int(0)),
            Return(Int(1))
        ])

    def handle_remint(self):
        user = Txn.accounts[1]
        current_time = Global.latest_timestamp()
        last_remint = App.localGet(user, Bytes("last_remint"))
        remint_count = App.localGet(user, Bytes("remint_count"))
        max_remints = App.globalGet(Bytes("max_remints"))
        cooldown = App.globalGet(Bytes("cooldown"))

        return Seq([
            Assert(App.localGet(user, Bytes("registered")) == Int(1)),
            Assert(remint_count < max_remints),
            Assert(current_time >= (last_remint + cooldown)),
            App.localPut(user, Bytes("last_remint"), current_time),
            App.localPut(user, Bytes("remint_count"), remint_count + Int(1)),
            Return(Int(1))
        ])

    def compile_teal(self, teal_source):
        compile_response = self.algod_client.compile(teal_source)
        return base64.b64decode(compile_response['result'])

    def get_clear_program(self):
        program = Return(Int(1))
        return compileTeal(program, Mode.Application, version=5)

    def deploy_contract(self, max_remints=3, cooldown_days=30):
        cooldown = cooldown_days * 86400  # Convert days to seconds

        approval_program = self.compile_teal(self.get_approval_program())
        clear_program = self.compile_teal(self.get_clear_program())

        txn = ApplicationCreateTxn(
            sender=self.creator_address,
            sp=self.algod_client.suggested_params(),
            on_complete=SDKOnComplete.NoOpOC,
            approval_program=approval_program,
            clear_program=clear_program,
            global_schema=transaction.StateSchema(4, 3),
            local_schema=transaction.StateSchema(3, 3)
        )

        signed_txn = txn.sign(self.creator_private_key)
        tx_id = self.algod_client.send_transaction(signed_txn)
        result = transaction.wait_for_confirmation(self.algod_client, tx_id, 4)

        self.app_id = result['application-index']
        return self.app_id

    def initialize_contract(self, original_asset_id, ipfs_url):
        # Convert values to bytes
        max_remints = 3
        cooldown = 2592000  # 30 days in seconds
        
        txn = ApplicationCallTxn(
            sender=self.creator_address,
            sp=self.algod_client.suggested_params(),
            index=self.app_id,
            on_complete=SDKOnComplete.NoOpOC,
            app_args=[
                b"init",
                original_asset_id.to_bytes(8, 'big'),
                ipfs_url.encode(),
                max_remints.to_bytes(8, 'big'),
                cooldown.to_bytes(8, 'big')
            ],
            foreign_assets=[original_asset_id]
        )

        signed_txn = txn.sign(self.creator_private_key)
        tx_id = self.algod_client.send_transaction(signed_txn)
        result = transaction.wait_for_confirmation(self.algod_client, tx_id, 4)

        self.original_asset_id = original_asset_id
        self.metadata_ipfs_url = ipfs_url
        return result

    def opt_in_to_app(self, user_address, user_private_key):
        """Opt in to the application"""
        try:
            sp = self.algod_client.suggested_params()
            sp.flat_fee = True
            sp.fee = 1000

            txn = ApplicationCallTxn(
                sender=user_address,
                sp=sp,
                index=self.app_id,
                on_complete=SDKOnComplete.OptInOC
            )

            signed_txn = txn.sign(user_private_key)
            tx_id = self.algod_client.send_transaction(signed_txn)
            result = transaction.wait_for_confirmation(self.algod_client, tx_id, 4)
            
            # Wait for state to be updated
            time.sleep(3)
            
            # Verify opt-in
            account_info = self.algod_client.account_info(user_address)
            for app in account_info.get('apps-local-state', []):
                if app['id'] == self.app_id:
                    return result
            
            raise ValueError("Opt-in verification failed")
            
        except Exception as e:
            raise ValueError(f"Opt-in failed: {str(e)}")

    def register_user_onchain(self, user_address):
        """Register a user for token regeneration"""
        try:
            # First verify the user has opted in
            account_info = self.algod_client.account_info(user_address)
            has_opted_in = any(app['id'] == self.app_id 
                            for app in account_info.get('apps-local-state', []))
            
            if not has_opted_in:
                raise ValueError("User must opt-in to the application first")

            # Get suggested params with increased fee
            sp = self.algod_client.suggested_params()
            sp.flat_fee = True
            sp.fee = 2000

            # Proceed with registration
            txn = ApplicationCallTxn(
                sender=self.creator_address,
                sp=sp,
                index=self.app_id,
                on_complete=SDKOnComplete.NoOpOC,
                app_args=[b"register"],
                accounts=[user_address]
            )

            signed_txn = txn.sign(self.creator_private_key)
            tx_id = self.algod_client.send_transaction(signed_txn)
            result = transaction.wait_for_confirmation(self.algod_client, tx_id, 4)
            
            # Wait for state to be updated
            time.sleep(5)
            
            # Verify registration
            account_info = self.algod_client.account_info(user_address)
            for app in account_info.get('apps-local-state', []):
                if app['id'] == self.app_id:
                    state = {base64.b64decode(x['key']).decode(): x['value'] 
                            for x in app.get('key-value', [])}
                    if state.get('registered', {}).get('uint', 0) == 1:
                        return result
            
            raise ValueError("Registration verification failed")
            
        except Exception as e:
            raise ValueError(f"Registration failed: {str(e)}")

    def verify_user_eligibility(self, user_address):
        try:
            account_info = self.algod_client.account_info(user_address)
            for app in account_info.get('apps-local-state', []):
                if app['id'] == self.app_id:
                    state = {base64.b64decode(x['key']).decode(): x['value'] 
                            for x in app.get('key-value', [])}
                    
                    registered = state.get('registered', {}).get('uint', 0)
                    if registered != 1:
                        return False, "User not registered"
                    
                    remint_count = state.get('remint_count', {}).get('uint', 0)
                    last_remint = state.get('last_remint', {}).get('uint', 0)
                    current_time = int(datetime.now().timestamp())

                    # Get global state
                    app_info = self.algod_client.application_info(self.app_id)
                    global_state = {base64.b64decode(x['key']).decode(): x['value']
                                 for x in app_info['params']['global-state']}
                    
                    max_remints = global_state.get('max_remints', {}).get('uint', 3)
                    cooldown = global_state.get('cooldown', {}).get('uint', 2592000)

                    if remint_count >= max_remints:
                        return False, "Max remints reached"
                    if current_time < (last_remint + cooldown):
                        return False, "Cooldown period not passed"
                    return True, "Eligible for remint"
            
            return False, "User not opted in"
        except Exception as e:
            return False, f"Verification error: {str(e)}"

    def get_metadata_from_ipfs(self):
        try:
            response = requests.get(self.metadata_ipfs_url)
            response.raise_for_status()
            metadata = response.json()
            
            # Validate metadata structure
            required_fields = ['name', 'unitName', 'decimals']
            for field in required_fields:
                if field not in metadata:
                    raise ValueError(f"Missing required field in metadata: {field}")
            
            return {
                'name': metadata['name'],
                'unit_name': metadata['unitName'],
                'decimals': int(metadata['decimals']),
                'total': 1_000_000_000,  # 1 billion with decimals
                'url': self.metadata_ipfs_url,
                'properties': metadata.get('properties', {})
            }
        except Exception as e:
            raise ValueError(f"Error processing metadata: {str(e)}")

    def regenerate_token(self, user_address):
        eligible, reason = self.verify_user_eligibility(user_address)
        if not eligible:
            raise ValueError(f"User not eligible: {reason}")

        metadata = self.get_metadata_from_ipfs()

        # Create new asset with same metadata
        txn = AssetConfigTxn(
            sender=self.creator_address,
            sp=self.algod_client.suggested_params(),
            total=metadata['total'],
            decimals=metadata['decimals'],
            asset_name=metadata['name'],
            unit_name=metadata['unit_name'],
            url=metadata['url'],
            manager=self.creator_address,
            reserve=self.creator_address,
            freeze=self.creator_address,
            clawback=self.creator_address,
            default_frozen=False,
            note=json.dumps(metadata['properties']).encode()
        )

        signed_txn = txn.sign(self.creator_private_key)
        tx_id = self.algod_client.send_transaction(signed_txn)
        result = transaction.wait_for_confirmation(self.algod_client, tx_id, 4)
        new_asset_id = result['asset-index']

        # Update remint count
        remint_txn = ApplicationCallTxn(
            sender=self.creator_address,
            sp=self.algod_client.suggested_params(),
            index=self.app_id,
            on_complete=SDKOnComplete.NoOpOC,
            app_args=[b"remint"],
            accounts=[user_address]
        )

        signed_remint_txn = remint_txn.sign(self.creator_private_key)
        self.algod_client.send_transaction(signed_remint_txn)

        print(f"\n✅ Token regenerated successfully!")
        print(f"New Asset ID: {new_asset_id}")
        print(f"Name: {metadata['name']}")
        print(f"Unit: {metadata['unit_name']}")
        print(f"Decimals: {metadata['decimals']}")
        print(f"Properties: {metadata['properties']}")
        
        return new_asset_id


# ===============================
# Example Usage (Main)
# ===============================
if __name__ == "__main__":
    algod_address = "https://testnet-api.algonode.cloud"
    algod_token = ""
    algod_client = algod.AlgodClient(algod_token, algod_address)

    # Generate or use existing accounts
    creator_private_key, creator_address = account.generate_account()
    user_private_key, user_address = account.generate_account()

    print("Fund these accounts in TestNet Dispenser:")
    print(f"Creator: {creator_address}")
    print(f"User: {user_address}")
    input("Press Enter after funding accounts...")

    regenerator = TokenRegenerator(algod_client, creator_address, creator_private_key)

    print("Deploying contract...")
    app_id = regenerator.deploy_contract()
    print(f"Contract deployed with app ID: {app_id}")

    try:
        original_asset_id = int(input("Enter original asset ID: "))
        ipfs_url = input("Enter IPFS URL for metadata: ").strip()
        
        print("Initializing contract...")
        regenerator.initialize_contract(original_asset_id, ipfs_url)
        print("Contract initialized successfully!")

        print("Opting in user to application...")
        regenerator.opt_in_to_app(user_address, user_private_key)
        print("User opted in successfully!")

        print("Registering user...")
        regenerator.register_user_onchain(user_address)
        print("User registered successfully!")

        print("Attempting token regeneration...")
        new_asset_id = regenerator.regenerate_token(user_address)
        print(f"Success! New asset ID: {new_asset_id}")
    except Exception as e:
        print(f"Error: {str(e)}")
        print("Please check your input values and try again.")