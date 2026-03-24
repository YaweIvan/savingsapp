-- PostgreSQL initialization script for Savings App

-- Users table
CREATE TABLE IF NOT EXISTS users (
    id SERIAL PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    id_number VARCHAR(50),
    phone VARCHAR(20),
    location VARCHAR(255),
    photo VARCHAR(500),
    notes TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Transactions table
CREATE TABLE IF NOT EXISTS transactions (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    type VARCHAR(50) NOT NULL,
    amount NUMERIC(10, 2) NOT NULL,
    note TEXT,
    date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Admin table
CREATE TABLE IF NOT EXISTS admin (
    id SERIAL PRIMARY KEY,
    username VARCHAR(100) UNIQUE NOT NULL,
    password VARCHAR(255) NOT NULL
);

-- Messages table
CREATE TABLE IF NOT EXISTS messages (
    id SERIAL PRIMARY KEY,
    sender_type VARCHAR(50),
    sender_id INTEGER,
    receiver_id INTEGER,
    message TEXT,
    date_sent TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create indexes for better query performance
CREATE INDEX IF NOT EXISTS idx_transactions_user_id ON transactions(user_id);
CREATE INDEX IF NOT EXISTS idx_messages_receiver_id ON messages(receiver_id);

-- Insert default admin account
INSERT INTO admin (username, password) VALUES ('admin', 'admin123')
ON CONFLICT (username) DO NOTHING;
