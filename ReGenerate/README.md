# Token Regeneration System

This system enables secure re-minting of lost or recurring tokens while maintaining original metadata. It addresses the limitation of Algorand Standard Assets (ASAs) being non-mintable after creation by implementing a dynamic re-issuance mechanism.

## Features

- **On-Demand Tokenization**: Recreate tokens with identical metadata when needed
- **Threshold-Based Regeneration**: Automatically triggers when pool supply falls below 5%
- **Metadata Preservation**: Maintains original token metadata through IPFS storage
- **Ownership Verification**: Secure verification of previous token ownership
- **Creator Control**: Only authorized creator can regenerate tokens

## Components

1. **TokenRegenerator Contract** (`regenerate.py`):
   - Main contract implementation
   - Handles token regeneration logic
   - Manages ownership verification
   - Integrates with pool monitoring

2. **TEAL Programs**:
   - `regenerate_approval.teal`: Main contract logic
   - `regenerate_clear.teal`: Contract clearing logic

## Usage

1. **Deployment**:
```python
# Initialize client
algod_client = algod.AlgodClient(algod_token, algod_address)

# Create regenerator instance
regenerator = TokenRegenerator(algod_client)

# Deploy contract
app_id = regenerator.deploy_contract(creator_private_key)
```

2. **Initialization**:
```python
# Initialize with original asset details
regenerator.initialize_regenerator(
    creator_private_key,
    original_asset_id,
    metadata_ipfs_url
)
```

3. **Token Regeneration**:
```python
# Check if regeneration is needed
if regenerator.check_regeneration_threshold(pool_address):
    # Regenerate token for verified user
    new_asset_id = regenerator.regenerate_token(
        creator_private_key,
        user_identifier
    )
```

## Security Features

1. **Creator Authorization**: Only the original creator can regenerate tokens
2. **Threshold Monitoring**: Automatic checks for pool supply levels
3. **Ownership Verification**: Secure verification of previous token ownership
4. **Metadata Integrity**: Preserved through IPFS storage

## Requirements

- Python 3.7+
- Algorand SDK
- IPFS integration
- Environment variables for configuration

## Environment Variables

Create a `.env` file with:
```
ALGOD_TOKEN=your_algod_token
ALGOD_SERVER=your_algod_server
CREATOR_MNEMONIC=your_creator_mnemonic
```

## License

MIT License 