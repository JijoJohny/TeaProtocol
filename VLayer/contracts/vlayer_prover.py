from pyteal import *

def approval_program():
    # Global state keys
    proof_key = Bytes("proof")
    stripe_data_key = Bytes("stripe_data")
    algo_address_key = Bytes("algo_address")
    
    # Operations
    generate_proof = Bytes("generate_proof")
    verify_proof = Bytes("verify_proof")

    def is_valid_stripe_data():
        return Seq([
            # Verify Stripe data format
            Assert(App.globalGet(stripe_data_key) != Bytes("")),
            # Verify Algorand address format
            Assert(Len(App.globalGet(algo_address_key)) == Int(58)),
            Return(Int(1))
        ])

    def create_proof():
        return Seq([
            # Verify input data
            is_valid_stripe_data(),
            # Generate proof (simplified for example)
            App.globalPut(proof_key, Concat(
                App.globalGet(stripe_data_key),
                Bytes("_verified_"),
                App.globalGet(algo_address_key)
            )),
            Return(Int(1))
        ])

    def validate_proof():
        proof = App.globalGet(proof_key)
        verified_marker = Bytes("_verified_")
        return Seq([
            # Verify proof exists
            Assert(proof != Bytes("")),
            # Verify proof contains the marker
            Assert(Substring(proof, Int(0), Len(verified_marker)) == verified_marker),
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
        [Txn.application_args[0] == generate_proof, create_proof()],
        [Txn.application_args[0] == verify_proof, validate_proof()],
    )

    return program

def clear_state_program():
    return Return(Int(1))

if __name__ == "__main__":
    with open("vlayer_prover_approval.teal", "w") as f:
        compiled = compileTeal(approval_program(), mode=Mode.Application, version=6)
        f.write(compiled)

    with open("vlayer_prover_clear.teal", "w") as f:
        compiled = compileTeal(clear_state_program(), mode=Mode.Application, version=6)
        f.write(compiled)