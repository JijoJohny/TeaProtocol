from pyteal import *

def approval_program():
    # Global state keys
    total_supply_key = Bytes("total_supply")
    pool_address_key = Bytes("pool_address")
    pool_allocation_key = Bytes("pool_allocation")  # 75% in basis points
    
    # Local state keys
    balance_key = Bytes("balance")
    
    # Operations
    transfer = Bytes("transfer")
    mint = Bytes("mint")
    
    # Constants
    POOL_ALLOCATION = Int(7500)  # 75%
    
    def initialize():
        return Seq([
            App.globalPut(total_supply_key, Int(0)),
            App.globalPut(pool_allocation_key, POOL_ALLOCATION),
            Return(Int(1))
        ])
    
    def handle_mint():
        amount = Btoi(Txn.application_args[1])
        pool_amount = amount * App.globalGet(pool_allocation_key) / Int(10000)
        creator_amount = amount - pool_amount
        
        return Seq([
            # Update total supply
            App.globalPut(total_supply_key, App.globalGet(total_supply_key) + amount),
            
            # Allocate to pool
            App.localPut(App.globalGet(pool_address_key), balance_key,
                App.localGet(App.globalGet(pool_address_key), balance_key) + pool_amount),
            
            # Allocate to creator
            App.localPut(Txn.sender(), balance_key,
                App.localGet(Txn.sender(), balance_key) + creator_amount),
            
            Return(Int(1))
        ])
    
    def handle_transfer():
        amount = Btoi(Txn.application_args[1])
        receiver = Txn.accounts[1]
        
        return Seq([
            # Check if sender has enough balance
            Assert(App.localGet(Txn.sender(), balance_key) >= amount),
            
            # Update sender balance
            App.localPut(Txn.sender(), balance_key,
                App.localGet(Txn.sender(), balance_key) - amount),
            
            # Update receiver balance
            App.localPut(receiver, balance_key,
                App.localGet(receiver, balance_key) + amount),
            
            Return(Int(1))
        ])
    
    # Main program logic
    program = Cond(
        [Txn.application_id() == Int(0), initialize()],
        [Txn.on_completion() == OnComplete.DeleteApplication, Return(Int(0))],
        [Txn.on_completion() == OnComplete.UpdateApplication, Return(Int(0))],
        [Txn.on_completion() == OnComplete.CloseOut, Return(Int(1))],
        [Txn.on_completion() == OnComplete.OptIn, Return(Int(1))],
        
        # Handle application calls
        [Txn.application_args[0] == mint, handle_mint()],
        [Txn.application_args[0] == transfer, handle_transfer()]
    )
    
    return program

def clear_state_program():
    return Return(Int(1))

if __name__ == "__main__":
    with open("token_approval.teal", "w") as f:
        compiled = compileTeal(approval_program(), mode=Mode.Application, version=6)
        f.write(compiled)
    
    with open("token_clear.teal", "w") as f:
        compiled = compileTeal(clear_state_program(), mode=Mode.Application, version=6)
        f.write(compiled) 