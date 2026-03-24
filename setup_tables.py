import psycopg2
import sys
from dotenv import load_dotenv
import os

load_dotenv()

def setup():
    # Step 1: Connect to default 'postgres' db and create savings_app if needed
    try:
        conn = psycopg2.connect(
            host=os.environ.get('DB_HOST', 'localhost'),
            user=os.environ.get('DB_USER', 'postgres'),
            password=os.environ.get('DB_PASSWORD', 'postgres'),
            port=os.environ.get('DB_PORT', '5432'),
            database='postgres'
        )
        conn.autocommit = True
        cursor = conn.cursor()
        cursor.execute("SELECT 1 FROM pg_database WHERE datname = 'savings_app'")
        if cursor.fetchone():
            print("[OK] Database 'savings_app' already exists")
        else:
            cursor.execute("CREATE DATABASE savings_app")
            print("[OK] Database 'savings_app' created")
        cursor.close()
        conn.close()
    except Exception as e:
        print(f"[ERROR] Could not connect to PostgreSQL: {e}")
        sys.exit(1)

    # Step 2: Connect to savings_app and create tables
    try:
        conn = psycopg2.connect(
            host=os.environ.get('DB_HOST', 'localhost'),
            user=os.environ.get('DB_USER', 'postgres'),
            password=os.environ.get('DB_PASSWORD', 'postgres'),
            port=os.environ.get('DB_PORT', '5432'),
            database='savings_app'
        )
        cursor = conn.cursor()

        cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
                id SERIAL PRIMARY KEY,
                name VARCHAR(255) NOT NULL,
                id_number VARCHAR(50),
                phone VARCHAR(20),
                location VARCHAR(255),
                photo VARCHAR(500),
                notes TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        print("[OK] users table ready")

        cursor.execute('''
            CREATE TABLE IF NOT EXISTS transactions (
                id SERIAL PRIMARY KEY,
                user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
                type VARCHAR(50) NOT NULL,
                amount NUMERIC(10, 2) NOT NULL,
                note TEXT,
                date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        print("[OK] transactions table ready")

        cursor.execute('''
            CREATE TABLE IF NOT EXISTS admin (
                id SERIAL PRIMARY KEY,
                username VARCHAR(100) UNIQUE NOT NULL,
                password VARCHAR(255) NOT NULL
            )
        ''')
        print("[OK] admin table ready")

        cursor.execute('''
            CREATE TABLE IF NOT EXISTS messages (
                id SERIAL PRIMARY KEY,
                sender_type VARCHAR(50),
                sender_id INTEGER,
                receiver_id INTEGER,
                message TEXT,
                date_sent TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        print("[OK] messages table ready")

        cursor.execute('CREATE INDEX IF NOT EXISTS idx_transactions_user_id ON transactions(user_id)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_messages_receiver_id ON messages(receiver_id)')
        print("[OK] indexes ready")

        cursor.execute(
            "INSERT INTO admin (username, password) VALUES ('admin', 'admin123') ON CONFLICT (username) DO NOTHING"
        )
        print("[OK] default admin account ready (username: admin / password: admin123)")

        conn.commit()
        cursor.close()
        conn.close()
        print("\n[DONE] Setup complete! Run: python app.py")

    except Exception as e:
        print(f"[ERROR] Error creating tables: {e}")
        sys.exit(1)

if __name__ == '__main__':
    setup()
