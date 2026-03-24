# Deployment on Coolify

## Environment Variables to Set on Coolify

Set these in your Coolify environment:

```
DB_HOST=postgres_service_name_or_hostname
DB_NAME=savings_app
DB_USER=postgres
DB_PASSWORD=your_secure_password
DB_PORT=5432
SECRET_KEY=your_secure_random_key
FLASK_DEBUG=False
PORT=5000
```

## Coolify Setup Steps

1. **Create PostgreSQL Database Service** in Coolify
   - Name: `savings-db` or similar
   - Database name: `savings_app`
   - User: `postgres`
   - Password: (generate strong password)

2. **Link to Flask App**
   - Add environment variables above
   - Make sure `DB_HOST` matches your PostgreSQL service hostname

3. **Prepare Tables** (Run Once)
   - Connect to Coolify PostgreSQL
   - Run the SQL from `init_database.sql`

4. **Deploy Flask App**
   - Upload this repository
   - Coolify will detect Flask from requirements.txt
   - Set PORT to 5000
   - Deploy!

## Quick Local Test

Before deploying, test locally:

```bash
# 1. Activate environment
.\.venv\Scripts\Activate.ps1

# 2. Run app
python app.py

# 3. Visit http://localhost:5000
```

## Production Checklist

- [ ] PostgreSQL database created on Coolify
- [ ] All environment variables set
- [ ] Tables created (run init_database.sql)
- [ ] SECRET_KEY is strong and random
- [ ] FLASK_DEBUG=False
- [ ] PORT matches Coolify settings
- [ ] Upload folder has correct permissions
