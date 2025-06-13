import os
import subprocess
import sys
from pathlib import Path

def create_virtual_environment():
    print("Creating virtual environment...")
    try:
        subprocess.run([sys.executable, "-m", "venv", "venv"], check=True)
        print("Virtual environment created successfully!")
    except subprocess.CalledProcessError as e:
        print(f"Error creating virtual environment: {e}")
        return False
    return True

def install_requirements():
    print("Installing requirements...")
    try:
        if os.name == 'nt':  # Windows
            pip_path = os.path.join("venv", "Scripts", "pip")
        else:  # Unix/Linux/MacOS
            pip_path = os.path.join("venv", "bin", "pip")
        
        subprocess.run([pip_path, "install", "-r", "requirements.txt"], check=True)
        print("Requirements installed successfully!")
    except subprocess.CalledProcessError as e:
        print(f"Error installing requirements: {e}")
        return False
    return True

def create_env_file():
    print("Creating .env file...")
    env_template = """# Stripe Configuration
STRIPE_SECRET_KEY=your_stripe_secret_key_here
STRIPE_WEBHOOK_SECRET=your_stripe_webhook_secret_here

# Algorand Configuration
ALGOD_ADDRESS=http://localhost:4001
ALGOD_TOKEN=aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa
ADMIN_ADDRESS=your_algorand_admin_address
ADMIN_PRIVATE_KEY=your_algorand_admin_private_key

# Vlayer Application IDs (After deployment)
VLAYER_PROVER_APP_ID=
VLAYER_VERIFIER_APP_ID=

# Server Configuration
API_HOST=0.0.0.0
API_PORT=8000

# Database Configuration
DATABASE_URL=postgresql://user:password@localhost:5432/vlayer_db
"""
    
    if not os.path.exists('.env'):
        with open('.env', 'w') as f:
            f.write(env_template)
        print(".env file created successfully!")
    else:
        print(".env file already exists. Skipping creation.")

def setup_database():
    print("Setting up database...")
    try:
        # Check if PostgreSQL is installed
        subprocess.run(["psql", "--version"], check=True, capture_output=True)
        
        # Create database and tables
        # subprocess.run(["psql", "-f", "database/schema.sql"], check=True)
        print("Database setup completed successfully!")
    except subprocess.CalledProcessError as e:
        print(f"Error setting up database: {e}")
        print("Please make sure PostgreSQL is installed and running.")
        return False
    return True

def main():
    print("Starting Vlayer setup...")
    
    # Create virtual environment
    if not create_virtual_environment():
        return
    
    # Install requirements
    if not install_requirements():
        return
    
    # Create .env file
    create_env_file()
    
    # Setup database
    #setup_database()
    
    print("\nSetup completed! Next steps:")
    print("1. Edit the .env file with your actual configuration values")
    print("2. Run 'python deployContract.py' to deploy the smart contracts")
    print("3. Update the .env file with the deployed contract IDs")
    print("4. Run 'python main.py' to start the application")

if __name__ == "__main__":
    main() 