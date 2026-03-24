# PostgreSQL Migration Checklist

## Pre-Setup Checklist
- [ ] PostgreSQL 18 is installed at `C:\Program Files\PostgreSQL\18`
- [ ] PostgreSQL service is running (check Services → PostgreSQL)
- [ ] Virtual environment is created and activated
- [ ] Packages installed: `psycopg2-binary`, `Flask-SQLAlchemy`, `python-dotenv`

## Files Created
- [ ] `.env` - Contains database connection string
- [ ] `app_postgres.py` - New Flask app using PostgreSQL
- [ ] `init_database.sql` - SQL schema and setup
- [ ] `setup_postgres.py` - Setup helper script
- [ ] `POSTGRES_SETUP.md` - This detailed guide

## Setup Steps
- [ ] Start PostgreSQL service (services.msc)
- [ ] Create database in PostgreSQL:
  ```sql
  CREATE DATABASE savingsapp;
  ```
- [ ] Create tables using init_database.sql
- [ ] Verify `.env` has correct DATABASE_URL
- [ ] Backup old `app.py` as `app_sqlite.py`
- [ ] Rename `app_postgres.py` to `app.py`

## Testing
- [ ] Run: `python app.py`
- [ ] Check for errors in terminal
- [ ] Visit: http://localhost:5000
- [ ] Login with admin/admin123
- [ ] Test user registration
- [ ] Test adding transactions

## Troubleshooting
- [ ] PostgreSQL service running? → Check services.msc
- [ ] Database created? → Check with: `psql -U postgres -l`
- [ ] Connection string correct? → Check `.env` file
- [ ] Packages installed? → Run: `pip list | grep -i postgres`
- [ ] Port 5432 available? → Run: `netstat -an | find "5432"`

## Success Indicators
- ✓ App starts without errors
- ✓ Can login to admin panel
- ✓ Can view users list
- ✓ Can add new users
- ✓ Can add transactions
- ✓ Data persists after restart
