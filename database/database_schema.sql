-- This script defines the database schema for the Smart Wallet AI application.
-- We use UUIDs for primary keys to prevent exposing sequential user/data IDs.
-- The schema is designed to be relational, ensuring data integrity.

-- First, enable the pgcrypto extension to generate UUIDs.
CREATE EXTENSION IF NOT EXISTS "pgcrypto";

-- Table to store user account information.
CREATE TABLE app_users (
    user_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    email VARCHAR(255) UNIQUE NOT NULL,
    hashed_password TEXT NOT NULL,
    -- The unique email address for forwarding bank offers.
    unique_forwarding_email VARCHAR(255) UNIQUE NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

COMMENT ON TABLE app_users IS 'Stores user account and authentication information.';
COMMENT ON COLUMN app_users.user_id IS 'Primary key for the user.';
COMMENT ON COLUMN app_users.email IS 'User''s login email address.';
COMMENT ON COLUMN app_users.hashed_password IS 'Securely stored user password hash.';
COMMENT ON COLUMN app_users.unique_forwarding_email IS 'The unique address for this user to forward offer emails to.';


-- Table to store credit card details for each user.
CREATE TABLE credit_cards (
    card_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES app_users(user_id) ON DELETE CASCADE,
    card_name VARCHAR(100) NOT NULL,
    bank_name VARCHAR(100) NOT NULL,
    network VARCHAR(50), -- e.g., Visa, Mastercard, Amex
    reward_type VARCHAR(50), -- e.g., Cashback, Points, Miles
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

COMMENT ON TABLE credit_cards IS 'Stores the credit cards belonging to each user.';
COMMENT ON COLUMN credit_cards.user_id IS 'Foreign key linking to the app_users table.';
COMMENT ON COLUMN credit_cards.card_name IS 'User-defined name for the card (e.g., "My BofA Cash Rewards").';
COMMENT ON COLUMN credit_cards.bank_name IS 'The name of the issuing bank (e.g., "Bank of America").';


-- Define ENUM types for offer status and source to ensure data consistency.
CREATE TYPE offer_status AS ENUM ('pending_confirmation', 'active', 'used', 'expired');
CREATE TYPE offer_source AS ENUM ('email_import', 'screenshot_import', 'manual');

-- Table to store all offers associated with each credit card.
CREATE TABLE card_offers (
    offer_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    card_id UUID NOT NULL REFERENCES credit_cards(card_id) ON DELETE CASCADE,
    description TEXT NOT NULL,
    merchant_name VARCHAR(255), -- e.g., Starbucks, Amazon.com
    category VARCHAR(100), -- e.g., Restaurants, Groceries, Gas
    reward_value NUMERIC(10, 2), -- The numeric value of the reward (e.g., 10.00 for 10%, 5.00 for 5x points)
    reward_unit VARCHAR(20), -- e.g., "%", "x_points", "USD"
    expiry_date DATE,
    status offer_status NOT NULL DEFAULT 'pending_confirmation',
    source offer_source NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

COMMENT ON TABLE card_offers IS 'Stores all credit card offers, extracted via AI or entered manually.';
COMMENT ON COLUMN card_offers.card_id IS 'Foreign key linking to the credit_cards table.';
COMMENT ON COLUMN card_offers.description IS 'The full text of the offer (e.g., "Get 10% back on purchases at Starbucks").';
COMMENT ON COLUMN card_offers.status IS 'The current state of the offer. ''pending_confirmation'' is for AI-extracted offers awaiting user approval.';
COMMENT ON COLUMN card_offers.source IS 'How the offer was added to the system.';

-- Indexes to speed up common queries.
CREATE INDEX idx_credit_cards_user_id ON credit_cards(user_id);
CREATE INDEX idx_card_offers_card_id ON card_offers(card_id);
CREATE INDEX idx_card_offers_merchant_name ON card_offers(merchant_name);
CREATE INDEX idx_card_offers_category ON card_offers(category);
CREATE INDEX idx_card_offers_status ON card_offers(status);
