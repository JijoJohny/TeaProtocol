-- Create database
CREATE DATABASE vlayer_db;
\c vlayer_db;

-- Create tables
CREATE TABLE payment_intents (
    id SERIAL PRIMARY KEY,
    stripe_intent_id VARCHAR(255) NOT NULL UNIQUE,
    algo_address VARCHAR(58) NOT NULL,
    amount BIGINT NOT NULL,
    currency VARCHAR(3) NOT NULL,
    status VARCHAR(50) NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE proofs (
    id SERIAL PRIMARY KEY,
    payment_intent_id INTEGER REFERENCES payment_intents(id),
    proof_id VARCHAR(255) NOT NULL UNIQUE,
    proof_data JSONB NOT NULL,
    status VARCHAR(50) NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    verified_at TIMESTAMP WITH TIME ZONE
);

CREATE TABLE user_collateral (
    id SERIAL PRIMARY KEY,
    algo_address VARCHAR(58) NOT NULL UNIQUE,
    total_collateral BIGINT NOT NULL DEFAULT 0,
    active_intents INTEGER NOT NULL DEFAULT 0,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE transactions (
    id SERIAL PRIMARY KEY,
    algo_address VARCHAR(58) NOT NULL,
    transaction_type VARCHAR(50) NOT NULL,
    amount BIGINT NOT NULL,
    status VARCHAR(50) NOT NULL,
    proof_id VARCHAR(255) REFERENCES proofs(proof_id),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Create indexes
CREATE INDEX idx_payment_intents_algo_address ON payment_intents(algo_address);
CREATE INDEX idx_proofs_payment_intent_id ON proofs(payment_intent_id);
CREATE INDEX idx_transactions_algo_address ON transactions(algo_address);

-- Create functions
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Create triggers
CREATE TRIGGER update_payment_intents_updated_at
    BEFORE UPDATE ON payment_intents
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_user_collateral_updated_at
    BEFORE UPDATE ON user_collateral
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column(); 