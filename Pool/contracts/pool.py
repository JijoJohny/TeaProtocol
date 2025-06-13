from pyteal import *

def approval_program():
    # Global state keys
    total_supply_key = Bytes("total_supply")
    pool_balance_key = Bytes("pool_balance")
    collateral_factor_key = Bytes("collateral_factor")  # 75% in basis points
    liquidation_bonus_key = Bytes("liquidation_bonus")  # 5% bonus
    liquidation_threshold_key = Bytes("liquidation_threshold")  # 80% in basis points
    
    # Local state keys
    user_balance_key = Bytes("user_balance")
    user_borrows_key = Bytes("user_borrows")
    user_collateral_key = Bytes("user_collateral")

    # Operations
    deposit = Bytes("deposit")
    borrow = Bytes("borrow")
    repay = Bytes("repay")
    withdraw = Bytes("withdraw")
    liquidate = Bytes("liquidate")

    # Constants
    COLLATERAL_FACTOR = Int(7500)  # 75%
    LIQUIDATION_BONUS = Int(10500)  # 5% bonus
    LIQUIDATION_THRESHOLD = Int(8000)  # 80%

    def initialize():
        return Seq([
            App.globalPut(total_supply_key, Int(0)),
            App.globalPut(pool_balance_key, Int(0)),
            App.globalPut(collateral_factor_key, COLLATERAL_FACTOR),
            App.globalPut(liquidation_bonus_key, LIQUIDATION_BONUS),
            App.globalPut(liquidation_threshold_key, LIQUIDATION_THRESHOLD),
            Return(Int(1))
        ])

    def handle_deposit():
        amount = Btoi(Txn.application_args[1])
        return Seq([
            # Update pool balance
            App.globalPut(pool_balance_key, App.globalGet(pool_balance_key) + amount),
            # Update user balance
            App.localPut(Txn.sender(), user_balance_key, 
                App.localGet(Txn.sender(), user_balance_key) + amount),
            Return(Int(1))
        ])

    def handle_borrow():
        amount = Btoi(Txn.application_args[1])
        return Seq([
            # Check if pool has enough balance
            Assert(App.globalGet(pool_balance_key) >= amount),
            # Check collateral factor
            Assert(App.localGet(Txn.sender(), user_collateral_key) * 
                App.globalGet(collateral_factor_key) / Int(10000) >= amount),
            # Update pool balance
            App.globalPut(pool_balance_key, App.globalGet(pool_balance_key) - amount),
            # Update user borrows
            App.localPut(Txn.sender(), user_borrows_key, 
                App.localGet(Txn.sender(), user_borrows_key) + amount),
            Return(Int(1))
        ])

    def handle_repay():
        amount = Btoi(Txn.application_args[1])
        return Seq([
            # Check if user has enough borrows
            Assert(App.localGet(Txn.sender(), user_borrows_key) >= amount),
            # Update pool balance
            App.globalPut(pool_balance_key, App.globalGet(pool_balance_key) + amount),
            # Update user borrows
            App.localPut(Txn.sender(), user_borrows_key, 
                App.localGet(Txn.sender(), user_borrows_key) - amount),
            Return(Int(1))
        ])

    def handle_withdraw():
        amount = Btoi(Txn.application_args[1])
        return Seq([
            # Check if user has enough balance
            Assert(App.localGet(Txn.sender(), user_balance_key) >= amount),
            # Check collateral factor after withdrawal
            Assert((App.localGet(Txn.sender(), user_balance_key) - amount) * 
                App.globalGet(collateral_factor_key) / Int(10000) >= 
                App.localGet(Txn.sender(), user_borrows_key)),
            # Update pool balance
            App.globalPut(pool_balance_key, App.globalGet(pool_balance_key) - amount),
            # Update user balance
            App.localPut(Txn.sender(), user_balance_key, 
                App.localGet(Txn.sender(), user_balance_key) - amount),
            Return(Int(1))
        ])

    def handle_liquidate():
        liquidatee = Txn.accounts[1]
        amount = Btoi(Txn.application_args[1])
        return Seq([
            # Check if liquidatee is undercollateralized
            Assert(App.localGet(liquidatee, user_balance_key) * 
                App.globalGet(collateral_factor_key) / Int(10000) < 
                App.localGet(liquidatee, user_borrows_key)),
            # Check if liquidator has enough balance
            Assert(App.localGet(Txn.sender(), user_balance_key) >= amount),
            # Calculate liquidation bonus
            bonus = amount * App.globalGet(liquidation_bonus_key) / Int(10000),
            # Update balances
            App.localPut(Txn.sender(), user_balance_key, 
                App.localGet(Txn.sender(), user_balance_key) - amount),
            App.localPut(liquidatee, user_borrows_key, 
                App.localGet(liquidatee, user_borrows_key) - amount),
            App.localPut(liquidatee, user_balance_key, 
                App.localGet(liquidatee, user_balance_key) - bonus),
            App.localPut(Txn.sender(), user_balance_key, 
                App.localGet(Txn.sender(), user_balance_key) + bonus),
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
        [Txn.application_args[0] == deposit, handle_deposit()],
        [Txn.application_args[0] == borrow, handle_borrow()],
        [Txn.application_args[0] == repay, handle_repay()],
        [Txn.application_args[0] == withdraw, handle_withdraw()],
        [Txn.application_args[0] == liquidate, handle_liquidate()]
    )

    return program

def clear_state_program():
    return Return(Int(1))

if __name__ == "__main__":
    with open("pool_approval.teal", "w") as f:
        compiled = compileTeal(approval_program(), mode=Mode.Application, version=6)
        f.write(compiled)

    with open("pool_clear.teal", "w") as f:
        compiled = compileTeal(clear_state_program(), mode=Mode.Application, version=6)
        f.write(compiled) 