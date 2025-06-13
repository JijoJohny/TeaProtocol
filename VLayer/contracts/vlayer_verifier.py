from pyteal import *

def approval_program():
    # Global state keys
    stripe_intent_key = Bytes("stripe_intent")
    algo_address_key = Bytes("algo_address")
    amount_key = Bytes("amount")
    status_key = Bytes("status")
    
    # Local state keys
    user_collateral_key = Bytes("user_collateral")
    user_intent_key = Bytes("user_intent")

    # Operations
    verify_intent = Bytes("verify_intent")
    update_collateral = Bytes("update_collateral")
    cancel_intent = Bytes("cancel_intent")

    # Helper functions
    def is_valid_address(address):
        return Len(address) == Int(58)  # Algorand addresses are 58 characters

    def verify_stripe_intent():
        return Seq([
            # Verify the payment intent exists and is valid
            Assert(App.globalGet(stripe_intent_key) != Bytes("")),
            Assert(App.globalGet(status_key) == Bytes("preauthorized")),
            # Update the status
            App.globalPut(status_key, Bytes("verified")),
            Return(Int(1))
        ])

    def update_user_collateral():
        return Seq([
            # Verify the user has a valid intent
            Assert(App.localGet(Int(0), user_intent_key) != Bytes("")),
            # Update the user's collateral amount
            App.localPut(Int(0), user_collateral_key, App.globalGet(amount_key)),
            Return(Int(1))
        ])

    def cancel_user_intent():
        return Seq([
            # Verify the user has a valid intent
            Assert(App.localGet(Int(0), user_intent_key) != Bytes("")),
            # Clear the user's intent and collateral
            App.localPut(Int(0), user_intent_key, Bytes("")),
            App.localPut(Int(0), user_collateral_key, Int(0)),
            Return(Int(1))
        ])

    # Main program logic
    program = Cond(
        [Txn.application_id() == Int(0), Return(Int(1))],  # Allow creation
        [Txn.on_completion() == OnComplete.DeleteApplication, Return(Int(0))],
        [Txn.on_completion() == OnComplete.UpdateApplication, Return(Int(0))],
        [Txn.on_completion() == OnComplete.CloseOut, Return(Int(1))],
        [Txn.on_completion() == OnComplete.OptIn, Return(Int(1))],
        
        # Handle application calls
        [Txn.application_args[0] == verify_intent, verify_stripe_intent()],
        [Txn.application_args[0] == update_collateral, update_user_collateral()],
        [Txn.application_args[0] == cancel_intent, cancel_user_intent()],
    )

    return program

def clear_state_program():
    return Return(Int(1))

if __name__ == "__main__":
    with open("vlayer_verifier_approval.teal", "w") as f:
        compiled = compileTeal(approval_program(), mode=Mode.Application, version=6)
        f.write(compiled)

    with open("vlayer_verifier_clear.teal", "w") as f:
        compiled = compileTeal(clear_state_program(), mode=Mode.Application, version=6)
        f.write(compiled) 