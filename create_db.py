"""
Create Database and Tables
Run this script to set up PostgreSQL database
"""

import psycopg2
import sys

def create_database():
    """Create the savingsapp database"""
    print("=" * 60)
    print("Creating PostgreSQL Database")
    print("=" * 60)
    
    try:
        # Connect to default postgres database
        conn = psycopg2.connect(
            host='localhost',
            user='postgres',
            password='postgres',
            port='5432',
            database='postgres'  # Connect to default db first
        )
        conn.autocommit = True
        cursor = conn.cursor()
        
        # Check if database already exists
        cursor.execute("""
            SELECT 1 FROM pg_database WHERE datname = 'savingsapp'
        """)
        db_exists = cursor.fetchone()
        
        if db_exists:
            print("✓ Database 'savingsapp' already exists")
        else:
            print("Creating database 'savingsapp'...")
            cursor.execute("CREATE DATABASE savingsapp")
            print("✓ Database 'savingsapp' created")
        
        cursor.close()
        conn.close()
        
        # Now connect to saveingsapp database and create tables
        print("\nCreating tables...")
        conn = psycopg2.connect(
            host='localhost',
            user='postgres',
            password='postgres',
            port='5432',
            database='savingsapp'
        )
        cursor = conn.cursor()
        
        # Create users table
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
        print("✓ Created 'users' table")
        
        # Create transactions table
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
        print("✓ Created 'transactions' table")
        
        # Create admin table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS admin (
                id SERIAL PRIMARY KEY,
                username VARCHAR(100) UNIQUE NOT NULL,
                password VARCHAR(255) NOT NULL
            )
        ''')
        print("✓ Created 'admin' table")
        
        # Create messages table
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
        print("✓ Created 'messages' table")
        
        # Create indexes
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_transactions_user_id ON transactions(user_id)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_messages_receiver_id ON messages(receiver_id)')
        print("✓ Created indexes")
        
        # Insert default admin
        cursor.execute("""
            INSERT INTO admin (username, password) VALUES ('admin', 'admin123')
            ON CONFLICT (username) DO NOTHING
        """)
        print("✓ Inserted default admin account")
        
        conn.commit()
        cursor.close()
        conn.close()
        
        print("\n" + "=" * 60)
        print("✓ Database setup complete!")
        print("=" * 60)
        print("\nNext step: Run your Flask app")
        print("  python app.py")
        print("\nAdmin credentials:")
        print("  Username: admin")
        print("  Password: admin123")
        return True
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        print("\nTroubleshooting:")
        print("  - Make sure PostgreSQL is running (check Services)")
        print("  - Default postgres user password might be different")
        print("  - Try: psql -U postgres -W (to test password)")
        return False


if __name__ == '__main__':
    success = create_database()
    sys.exit(0 if success else 1)
