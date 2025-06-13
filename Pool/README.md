# Algorand Pool System

This system implements a lending pool on Algorand with automatic token allocation to the pool. When new tokens are minted, 75% of them are automatically allocated to the pool for lending purposes.

## Features

- **Token Contract**: Handles token minting and transfers, automatically allocating 75% of minted tokens to the pool
- **Pool Contract**: Manages deposits, borrows, repayments, and liquidations
- **Collateral System**: Users can borrow against their collateral with a 75% collateral factor
- **Liquidation**: Under-collateralized positions can be liquidated with a 5% bonus for liquidators

## Prerequisites

- Python 3.8 or higher
- Algorand Node (or use Algorand TestNet)
- PyTeal
- Algorand SDK

## Setup

1. Install dependencies:
```bash
pip install pyteal algosdk python-dotenv
```

2. Create a `.env` file with the following variables:
```
ALGOD_ADDRESS=http://localhost:4001
ALGOD_TOKEN=aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa
ADMIN_MNEMONIC=your 25-word mnemonic phrase
```

3. Compile the contracts:
```bash
python contracts/pool.py
python contracts/token.py
```

4. Deploy the contracts:
```bash
python deploy.py
```

5. Update your `.env` file with the deployed application IDs:
```
POOL_APP_ID=<deployed_pool_app_id>
TOKEN_APP_ID=<deployed_token_app_id>
```

## Contract Interaction

### Token Contract

1. **Mint Tokens**
```python
# 75% will automatically go to the pool
app_args = ["mint", amount]
```

2. **Transfer Tokens**
```python
app_args = ["transfer", amount]
accounts = [receiver_address]
```

### Pool Contract

1. **Deposit**
```python
app_args = ["deposit", amount]
```

2. **Borrow**
```python
app_args = ["borrow", amount]
```

3. **Repay**
```python
app_args = ["repay", amount]
```

4. **Withdraw**
```python
app_args = ["withdraw", amount]
```

5. **Liquidate**
```python
app_args = ["liquidate", amount]
accounts = [liquidatee_address]
```

## Security Considerations

1. **Collateral Factor**: The system uses a 75% collateral factor, meaning users can borrow up to 75% of their collateral value.

2. **Liquidation Threshold**: Positions become liquidatable when the collateral value falls below 80% of the borrowed amount.

3. **Liquidation Bonus**: Liquidators receive a 5% bonus on liquidated positions.

## Development

To modify the contracts:

1. Edit the PyTeal code in `contracts/pool.py` and `contracts/token.py`
2. Recompile the contracts
3. Redeploy using `deploy.py`

## Testing

1. Create test accounts on Algorand TestNet
2. Fund the accounts with test ALGOs
3. Deploy contracts to TestNet
4. Test all operations:
   - Token minting and transfers
   - Pool deposits and withdrawals
   - Borrowing and repaying
   - Liquidation scenarios

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Submit a pull request

## License

MIT License 