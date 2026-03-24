"""
PostgreSQL Database Setup Script
Run this script ONCE to initialize your PostgreSQL database
"""

import subprocess
import sys
import os

# PostgreSQL path
PG_BIN = r"C:\Program Files\PostgreSQL\18\bin"
PSQL = os.path.join(PG_BIN, "psql.exe")
CREATEDB = os.path.join(PG_BIN, "createdb.exe")

def run_command(cmd, shell=False):
    """Run a shell command and return output"""
    try:
        result = subprocess.run(cmd, shell=shell, capture_output=True, text=True)
        return result.returncode, result.stdout, result.stderr
    except Exception as e:
        return 1, "", str(e)

def setup_database():
    """Create PostgreSQL database and user"""
    print("=" * 60)
    print("PostgreSQL Database Setup for Savings App")
    print("=" * 60)
    
    # Step 1: Create database
    print("\n[1/2] Creating database 'savingsapp'...")
    returncode, stdout, stderr = run_command([CREATEDB, "-U", "postgres", "savingsapp"])
    
    if returncode == 0:
        print("✓ Database 'savingsapp' created successfully!")
    else:
        if "already exists" in stderr:
            print("✓ Database 'savingsapp' already exists")
        else:
            print(f"✗ Error creating database: {stderr}")
            return False
    
    # Step 2: Create tables
    print("\n[2/2] Creating tables...")
    
    sql_file = "init_database.sql"
    if os.path.exists(sql_file):
        cmd = f'{PSQL} -U postgres -d savingsapp -f {sql_file}'
        returncode, stdout, stderr = run_command(cmd, shell=True)
        
        if returncode == 0:
            print("✓ Tables created successfully!")
            print("\n" + "=" * 60)
            print("Setup Complete!")
            print("=" * 60)
            print("\nYour database is ready. Run your Flask app with:")
            print("  python app.py")
            return True
        else:
            print(f"✗ Error creating tables: {stderr}")
            return False
    else:
        print("Note: init_database.sql not found. You can create it manually or run app.py")
        print("to auto-create tables on first run.")
        return True

if __name__ == "__main__":
    try:
        success = setup_database()
        sys.exit(0 if success else 1)
    except Exception as e:
        print(f"\n✗ Setup failed: {e}")
        sys.exit(1)
