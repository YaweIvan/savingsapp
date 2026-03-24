# PostgreSQL Setup Guide for Savings App

## Overview
This guide walks you through migrating your Flask Savings App from SQLite to PostgreSQL.

---

## Step-by-Step Setup

### ✅ Step 1: Start PostgreSQL Service

**Option A: Using Windows Services (Recommended)**
1. Press `Win + R`
2. Type `services.msc`
3. Find "PostgreSQL" service
4. Right-click → Select "Start" if not running
5. Verify it says "Running"

**Option B: Check if running**
```powershell
# In PowerShell, run:
C:\Program Files\PostgreSQL\18\bin\pg_isready.exe
# Should output: accepting connections
```

---

### ✅ Step 2: Open PostgreSQL Command Line

```powershell
# Replace "postgres-user" if different during installation
$env:PGPASSWORD = "postgres"; C:\Program Files\PostgreSQL\18\bin\psql.exe -U postgres
```

### ✅ Step 3: Create Database

Once in PostgreSQL command line (`postgres=#`):

```sql
-- Create database
CREATE DATABASE savingsapp;

-- Verify it was created
\l

-- Connect to it
\c savingsapp

-- Create tables
CREATE TABLE users (
    id SERIAL PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    id_number VARCHAR(50),
    phone VARCHAR(20),
    location VARCHAR(255),
    photo VARCHAR(500),
    notes TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE transactions (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    type VARCHAR(50) NOT NULL,
    amount NUMERIC(10, 2) NOT NULL,
    note TEXT,
    date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE admin (
    id SERIAL PRIMARY KEY,
    username VARCHAR(100) UNIQUE NOT NULL,
    password VARCHAR(255) NOT NULL
);

CREATE TABLE messages (
    id SERIAL PRIMARY KEY,
    sender_type VARCHAR(50),
    sender_id INTEGER,
    receiver_id INTEGER,
    message TEXT,
    date_sent TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Insert default admin
INSERT INTO admin (username, password) VALUES ('admin', 'admin123');

-- Exit
\q
```

---

### ✅ Step 4: Update Your Flask App

#### Option A: Replace app.py (Full Migration)
```powershell
# Backup your old app
ren app.py app_sqlite.py

# Rename the new PostgreSQL version
ren app_postgres.py app.py
```

#### Option B: Keep Both Versions
- Keep `app.py` (SQLite) as backup
- Run `app_postgres.py` separately:
```powershell
python app_postgres.py
```

---

### ✅ Step 5: Run Your App

```bash
# In your project folder with virtual environment activated
python app.py
```

Your app should now use PostgreSQL! Visit: `http://localhost:5000`

---

## Troubleshooting

### ❌ "fe_sendauth: no password supplied"
**Solution:** Set the password in `.env`:
```
DATABASE_URL=postgresql://postgres:YOUR_PASSWORD@localhost:5432/savingsapp
```

### ❌ "FATAL: Ident authentication failed"
**Solution:** Use `.env` file with proper credentials or modify PostgreSQL config

### ❌ Database "already exists"
**Solution:** You can ignore this or drop it first:
```sql
-- In PostgreSQL shell
DROP DATABASE savingsapp;
CREATE DATABASE savingsapp;
```

### ❌ Connection refused on port 5432
**Solution:** PostgreSQL service isn't running. Restart it using Services (services.msc)

### ❌ "psycopg2 not found"
**Solution:** Reinstall packages:
```powershell
pip install psycopg2-binary Flask-SQLAlchemy python-dotenv
```

---

## Migrating Data from SQLite to PostgreSQL

If you have existing data in SQLite that you want to migrate:

### Easy Way: Export/Import

1. **Export from SQLite:**
```python
import sqlite3
import json

conn = sqlite3.connect('database.db')
conn.row_factory = sqlite3.Row
cursor = conn.cursor()

# Export each table
tables = ['users', 'transactions', 'admin', 'messages']
for table in tables:
    data = cursor.execute(f"SELECT * FROM {table}").fetchall()
    with open(f'{table}.json', 'w') as f:
        json.dump([dict(row) for row in data], f, default=str)

conn.close()
```

2. **Import to PostgreSQL:**
```python
from sqlalchemy import create_engine
import json

engine = create_engine('postgresql://postgres:postgres@localhost:5432/savingsapp')

tables = ['users', 'transactions', 'admin', 'messages']
for table in tables:
    with open(f'{table}.json') as f:
        data = json.load(f)
        for record in data:
            # Use SQLAlchemy to insert
            # or write SQL INSERT statements
            pass
```

---

## Environment Variables (.env)

The `.env` file has been created with:
```
DATABASE_URL=postgresql://postgres:postgres@localhost:5432/savingsapp
FLASK_ENV=development
SECRET_KEY=savingsapp-secret-key-2024
```

**Change credentials if needed** to match your PostgreSQL setup.

---

## Files Created/Modified

- ✅ `.env` - Database configuration
- ✅ `requirements.txt` - Updated with PostgreSQL packages
- ✅ `app_postgres.py` - New Flask app with SQLAlchemy
- ✅ `init_database.sql` - SQL setup script
- ✅ `setup_postgres.py` - Python setup helper

---

## Next Steps

1. **Test the connection:**
```powershell
python -c "from app import db; print('✓ Database connection successful!')"
```

2. **Check your app works:**
   - Visit http://localhost:5000
   - Login to admin: username `admin`, password `admin123`

3. **Migrate your data** (if needed) using the guide above

---

## Important Notes

- PostgreSQL must be running before starting your Flask app
- The `DATABASE_URL` in `.env` must match your PostgreSQL setup
- SQLAlchemy will auto-create tables on first run if using `app.py`
- Your photo uploads folder (`static/uploads`) still works the same way

---

**Having issues?** Check that:
1. PostgreSQL service is running (services.msc)
2. You can connect: `psql -U postgres -d savingsapp`
3. `.env` file exists in your project root
4. Virtual environment is activated
