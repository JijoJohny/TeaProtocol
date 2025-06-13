# generate_keys.py
from algosdk import mnemonic
from dotenv import load_dotenv
import os

load_dotenv()  # Load existing .env variables

admin_mnemonic = "brain shy surround before biology rely alcohol symbol lion alien aware wife raccoon ceiling turkey embrace humble brush pact affair bright little giraffe abandon cheese"
admin_private_key = mnemonic.to_private_key(admin_mnemonic)

# Write to .env
with open(".env", "a") as env_file:
    env_file.write(f"\nADMIN_PRIVATE_KEY={admin_private_key}")
    env_file.write(f"\nADMIN_MNEMONIC={admin_mnemonic}")  # Optional: store mnemonic too