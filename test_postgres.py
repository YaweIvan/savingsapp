"""
Test PostgreSQL Connection
Run this to verify your PostgreSQL setup before starting the app
"""

import os
import sys
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def test_postgres_connection():
    """Test if PostgreSQL is accessible"""
    print("=" * 60)
    print("PostgreSQL Connection Test")
    print("=" * 60)
    
    # Check environment
    database_url = os.environ.get('DATABASE_URL')
    if not database_url:
        print("❌ DATABASE_URL not found in .env file")
        return False
    
    print(f"✓ DATABASE_URL found: {database_url}")
    
    # Try to import psycopg2
    try:
        import psycopg2
        print("✓ psycopg2 is installed")
    except ImportError:
        print("❌ psycopg2 not installed")
        print("   Run: pip install psycopg2-binary")
        return False
    
    # Try to import Flask-SQLAlchemy
    try:
        from flask_sqlalchemy import SQLAlchemy
        print("✓ Flask-SQLAlchemy is installed")
    except ImportError:
        print("❌ Flask-SQLAlchemy not installed")
        print("   Run: pip install Flask-SQLAlchemy")
        return False
    
    # Try to connect to database
    try:
        import psycopg2
        # Parse connection string: postgresql://user:password@host:port/database
        parts = database_url.replace('postgresql://', '').split('@')
        user_pass = parts[0].split(':')
        host_db = parts[1].split('/')
        
        user = user_pass[0]
        password = user_pass[1] if len(user_pass) > 1 else ""
        host = host_db[0].split(':')[0]
        port = host_db[0].split(':')[1] if ':' in host_db[0] else "5432"
        database = host_db[1]
        
        print(f"\nConnecting to: {host}:{port}/{database}")
        
        conn = psycopg2.connect(
            host=host,
            port=port,
            user=user,
            password=password,
            database=database
        )
        
        print("✓ Successfully connected to PostgreSQL!")
        
        # Check tables
        cursor = conn.cursor()
        cursor.execute("""
            SELECT table_name FROM information_schema.tables 
            WHERE table_schema = 'public'
        """)
        tables = cursor.fetchall()
        
        if tables:
            print(f"✓ Found {len(tables)} tables:")
            for table in tables:
                print(f"  - {table[0]}")
        else:
            print("⚠ No tables found. Run app.py to create them.")
        
        cursor.close()
        conn.close()
        
        return True
        
    except Exception as e:
        print(f"❌ Connection failed: {e}")
        print("\nTroubleshooting:")
        print("  1. Is PostgreSQL running? (Check Services → PostgreSQL)")
        print("  2. Is the DATABASE_URL correct in .env?")
        print("  3. Are the database credentials correct?")
        return False


def main():
    success = test_postgres_connection()
    
    print("\n" + "=" * 60)
    if success:
        print("✓ Ready to run: python app.py")
    else:
        print("✗ Fix the errors above then try again")
    print("=" * 60)
    
    return 0 if success else 1


if __name__ == '__main__':
    sys.exit(main())
