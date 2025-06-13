import os
from dotenv import load_dotenv
from VUSDGovernor import VUSDGovernor

load_dotenv()

def test_multisig():
    governor = VUSDGovernor()

    # Print local multisig info
    print("🔐 Multisig Address:", governor.multisig_account.address())
    print("🔐 Threshold:", governor.multisig_account.threshold)

    # ✅ Check if the ASA manager is the multisig address
    asset_info = governor.algod_client.asset_info(governor.asset_id)
    manager_on_chain = asset_info['params']['manager']

    if manager_on_chain == governor.multisig_account.address():
        print("✅ On-chain ASA manager matches multisig address")
    else:
        print("❌ Mismatch: On-chain manager =", manager_on_chain)

if __name__ == "__main__":
    test_multisig()
