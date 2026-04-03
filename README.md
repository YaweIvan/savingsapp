# SavingsApp Mini

SavingsApp Mini is a small Flask application for managing members in a savings group. It supports admin login, member registration, transaction tracking, messages, and member dashboards with balance summaries.

## How It Works

The app is built around a few core ideas:

1. An admin signs in and opens the dashboard.
2. The admin registers members and stores their profile details.
3. The admin records transactions for each member, such as deposits, withdrawals, loans, and rewards.
4. The app calculates totals and net balance from the transaction history.
5. Members can view their own dashboard and see transactions and messages.

There are two Flask entry points in the repository:

- `app.py` uses direct PostgreSQL connections with `psycopg2`.
- `app_postgres.py` uses `Flask-SQLAlchemy` and defines database models.

The active app is normally started with `python app.py` unless you choose the SQLAlchemy version.

## Folder Structure

```text
savingsappmini/
├── app.py
├── app_postgres.py
├── create_db.py
├── setup_postgres.py
├── setup_tables.py
├── init_database.sql
├── requirements.txt
├── .env
├── README.md
├── CHECKLIST.md
├── POSTGRES_SETUP.md
├── COOLIFY_DEPLOYMENT.md
├── MIGRATION_COMPLETE.md
├── static/
│   ├── style.css
│   ├── logoicon.png
│   └── uploads/
├── templates/
│   ├── base.html
│   ├── welcome.html
│   ├── admin_login.html
│   ├── admin_dashboard.html
│   ├── register_user.html
│   ├── add_transaction.html
│   ├── admin_message.html
│   ├── user_detail.html
│   └── user_dashboard.html
└── database.db
```

## Main Files

- `app.py` - Main Flask app with routes for login, dashboards, registration, transactions, and messaging.
- `app_postgres.py` - ORM-based version of the app with SQLAlchemy models.
- `init_database.sql` - SQL schema for PostgreSQL tables and indexes.
- `create_db.py` - Script that creates the database and tables using raw PostgreSQL commands.
- `setup_postgres.py` - Script that initializes PostgreSQL using `psql` and `createdb`.
- `setup_tables.py` - Script that creates the tables and default admin account from environment settings.
- `templates/` - Jinja templates for the UI pages.
- `static/` - CSS, branding, and uploaded member photos.

## Database Structure

The application uses four main tables:

- `users` - member profile information.
- `transactions` - deposits, withdrawals, loans, and rewards for each user.
- `admin` - admin login credentials.
- `messages` - messages sent between admin and members.

## Key Pages

- `/` - Welcome page.
- `/admin` - Admin login page.
- `/admin/dashboard` - Admin overview of users and totals.
- `/admin/register` - Register a new member.
- `/admin/user/<id>` - View a member in the admin panel.
- `/admin/transaction/<id>` - Add a transaction for a member.
- `/admin/message` - Send a message to one member or all members.
- `/user/<id>` - Member dashboard.
- `/user/<id>/message` - Member sends a message to admin.

## Environment Setup

The app reads configuration from `.env`, including database settings and the Flask secret key. Typical values include:

- `SECRET_KEY`
- `DB_HOST`
- `DB_NAME`
- `DB_USER`
- `DB_PASSWORD`
- `DB_PORT`

## Run the App

1. Create and activate a virtual environment.
2. Install dependencies from `requirements.txt`.
3. Create the PostgreSQL database and tables.
4. Run the Flask app:

```bash
python app.py
```

Then open `http://localhost:5000` in your browser.

## Default Admin Login

- Username: `admin`
- Password: `admin123`

## Notes

- Uploaded profile photos are saved in `static/uploads/`.
- The app shows flash messages for success and error feedback.
- The dashboard calculates balances from transaction history, so the numbers are derived from stored records rather than entered manually.
