from flask import Flask, render_template, request, redirect, session, url_for, flash
import sqlite3
import os
from datetime import datetime
from werkzeug.utils import secure_filename

app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', 'savingsapp-secret-key-2024')

UPLOAD_FOLDER = os.path.join('static', 'uploads')
DATABASE_PATH = os.environ.get('DATABASE_PATH', 'database.db')
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'webp'}

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
os.makedirs(UPLOAD_FOLDER, exist_ok=True)


def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


def get_db():
    conn = sqlite3.connect(DATABASE_PATH)
    conn.row_factory = sqlite3.Row
    return conn


# ─────────────────────── DATABASE SETUP ───────────────────────
def init_db():
    conn = get_db()
    c = conn.cursor()

    c.execute('''
    CREATE TABLE IF NOT EXISTS users (
        id       INTEGER PRIMARY KEY AUTOINCREMENT,
        name     TEXT NOT NULL,
        id_number TEXT,
        phone    TEXT,
        location TEXT,
        photo    TEXT,
        notes    TEXT,
        created_at TEXT DEFAULT (datetime('now','localtime'))
    )''')

    c.execute('''
    CREATE TABLE IF NOT EXISTS transactions (
        id       INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id  INTEGER NOT NULL,
        type     TEXT NOT NULL,
        amount   REAL NOT NULL,
        note     TEXT,
        date     TEXT DEFAULT (datetime('now','localtime')),
        FOREIGN KEY(user_id) REFERENCES users(id)
    )''')

    c.execute('''
    CREATE TABLE IF NOT EXISTS admin (
        id       INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE,
        password TEXT
    )''')

    c.execute('''
    CREATE TABLE IF NOT EXISTS messages (
        id          INTEGER PRIMARY KEY AUTOINCREMENT,
        sender_type TEXT,
        sender_id   INTEGER,
        receiver_id INTEGER,
        message     TEXT,
        date_sent   TEXT DEFAULT (datetime('now','localtime'))
    )''')

    # Default admin account
    c.execute("SELECT id FROM admin WHERE username='admin'")
    if not c.fetchone():
        c.execute("INSERT INTO admin (username, password) VALUES (?,?)", ('admin', 'admin123'))

    conn.commit()
    conn.close()


init_db()


# ─────────────────────── HELPERS ───────────────────────
def save_photo(file_obj):
    """Save an uploaded photo and return the relative path, or None."""
    if file_obj and file_obj.filename and allowed_file(file_obj.filename):
        filename = f"{datetime.now().strftime('%Y%m%d%H%M%S%f')}_{secure_filename(file_obj.filename)}"
        path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file_obj.save(path)
        # Return a forward-slash path for use in HTML src
        return path.replace('\\', '/')
    return None


def user_totals(user_id, conn):
    c = conn.cursor()
    def _sum(t):
        row = c.execute(
            "SELECT COALESCE(SUM(amount),0) FROM transactions WHERE user_id=? AND type=?",
            (user_id, t)
        ).fetchone()
        return row[0]
    return {
        'deposits':    _sum('deposit'),
        'withdrawals': _sum('withdrawal'),
        'rewards':     _sum('reward'),
        'borrowed':    _sum('loan'),
    }


def get_demo_user_id():
    conn = get_db()
    row = conn.execute("SELECT id FROM users ORDER BY id LIMIT 1").fetchone()
    conn.close()
    return row['id'] if row else None


# ─────────────────────── WELCOME ───────────────────────
@app.route('/')
def welcome():
    return render_template('welcome.html', demo_user_id=get_demo_user_id())


# ─────────────────────── ADMIN AUTH ───────────────────────
@app.route('/admin', methods=['GET', 'POST'])
def admin_login():
    if 'admin' in session:
        return redirect(url_for('admin_dashboard'))
    error = None
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        conn = get_db()
        admin = conn.execute(
            "SELECT * FROM admin WHERE username=? AND password=?", (username, password)
        ).fetchone()
        conn.close()
        if admin:
            session['admin'] = username
            return redirect(url_for('admin_dashboard'))
        error = 'Invalid username or password.'
    return render_template('admin_login.html', error=error, demo_user_id=get_demo_user_id())


@app.route('/admin/logout')
def admin_logout():
    session.pop('admin', None)
    return redirect(url_for('admin_login'))


# ─────────────────────── ADMIN DASHBOARD ───────────────────────
@app.route('/admin/dashboard')
def admin_dashboard():
    if 'admin' not in session:
        return redirect(url_for('admin_login'))
    conn = get_db()
    users = conn.execute("SELECT * FROM users ORDER BY created_at DESC").fetchall()

    # Compute totals per user
    user_data = []
    for u in users:
        totals = user_totals(u['id'], conn)
        net = totals['deposits'] + totals['rewards'] - totals['withdrawals'] - totals['borrowed']
        user_data.append({'user': u, 'totals': totals, 'net': net})

    # Global stats
    stats = {
        'total_users':    conn.execute("SELECT COUNT(*) FROM users").fetchone()[0],
        'total_deposits': conn.execute("SELECT COALESCE(SUM(amount),0) FROM transactions WHERE type='deposit'").fetchone()[0],
        'total_withdraw': conn.execute("SELECT COALESCE(SUM(amount),0) FROM transactions WHERE type='withdrawal'").fetchone()[0],
        'total_loans':    conn.execute("SELECT COALESCE(SUM(amount),0) FROM transactions WHERE type='loan'").fetchone()[0],
        'total_rewards':  conn.execute("SELECT COALESCE(SUM(amount),0) FROM transactions WHERE type='reward'").fetchone()[0],
    }
    conn.close()
    return render_template('admin_dashboard.html', user_data=user_data, stats=stats)


# ─────────────────────── REGISTER USER ───────────────────────
@app.route('/admin/register', methods=['GET', 'POST'])
def register_user():
    if 'admin' not in session:
        return redirect(url_for('admin_login'))
    if request.method == 'POST':
        name      = request.form['name']
        id_number = request.form.get('id_number', '')
        phone     = request.form.get('phone', '')
        location  = request.form.get('location', '')
        notes     = request.form.get('notes', '')
        photo_path = save_photo(request.files.get('photo'))

        conn = get_db()
        conn.execute(
            "INSERT INTO users (name,id_number,phone,location,photo,notes) VALUES (?,?,?,?,?,?)",
            (name, id_number, phone, location, photo_path, notes)
        )
        conn.commit()
        conn.close()
        flash(f'User "{name}" registered successfully!', 'success')
        return redirect(url_for('admin_dashboard'))
    return render_template('register_user.html')


# ─────────────────────── USER DETAIL (ADMIN) ───────────────────────
@app.route('/admin/user/<int:user_id>')
def user_detail(user_id):
    if 'admin' not in session:
        return redirect(url_for('admin_login'))
    conn = get_db()
    user = conn.execute("SELECT * FROM users WHERE id=?", (user_id,)).fetchone()
    if not user:
        conn.close()
        return 'User not found', 404
    transactions = conn.execute(
        "SELECT * FROM transactions WHERE user_id=? ORDER BY date DESC", (user_id,)
    ).fetchall()
    totals = user_totals(user_id, conn)
    net = totals['deposits'] + totals['rewards'] - totals['withdrawals'] - totals['borrowed']
    msgs = conn.execute(
        "SELECT * FROM messages WHERE receiver_id=? ORDER BY date_sent DESC", (user_id,)
    ).fetchall()
    conn.close()
    return render_template('user_detail.html', user=user, transactions=transactions,
                           totals=totals, net=net, messages=msgs)


# ─────────────────────── ADD TRANSACTION ───────────────────────
@app.route('/admin/transaction/<int:user_id>', methods=['GET', 'POST'])
def add_transaction(user_id):
    if 'admin' not in session:
        return redirect(url_for('admin_login'))
    conn = get_db()
    user = conn.execute("SELECT * FROM users WHERE id=?", (user_id,)).fetchone()
    if request.method == 'POST':
        t_type = request.form['type']
        amount = float(request.form['amount'])
        note   = request.form.get('note', '')
        date_now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        conn.execute(
            "INSERT INTO transactions (user_id,type,amount,note,date) VALUES (?,?,?,?,?)",
            (user_id, t_type, amount, note, date_now)
        )
        conn.commit()
        conn.close()
        flash(f'Transaction ({t_type}) of {amount:,.0f} recorded.', 'success')
        return redirect(url_for('user_detail', user_id=user_id))
    conn.close()
    return render_template('add_transaction.html', user=user)


# ─────────────────────── MESSAGING ───────────────────────
@app.route('/admin/message', methods=['GET', 'POST'])
def admin_message():
    if 'admin' not in session:
        return redirect(url_for('admin_login'))
    conn = get_db()
    users = conn.execute("SELECT id, name FROM users ORDER BY name").fetchall()
    if request.method == 'POST':
        message_text = request.form['message']
        receiver_id  = request.form['receiver_id']
        date_now     = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        if receiver_id == 'all':
            all_ids = conn.execute("SELECT id FROM users").fetchall()
            for row in all_ids:
                conn.execute(
                    "INSERT INTO messages (sender_type,sender_id,receiver_id,message,date_sent) VALUES (?,?,?,?,?)",
                    ('admin', 0, row['id'], message_text, date_now)
                )
        else:
            conn.execute(
                "INSERT INTO messages (sender_type,sender_id,receiver_id,message,date_sent) VALUES (?,?,?,?,?)",
                ('admin', 0, int(receiver_id), message_text, date_now)
            )
        conn.commit()
        conn.close()
        flash('Message sent!', 'success')
        return redirect(url_for('admin_dashboard'))
    conn.close()
    return render_template('admin_message.html', users=users)


# ─────────────────────── USER DASHBOARD ───────────────────────
@app.route('/user/<int:user_id>')
def user_dashboard(user_id):
    conn = get_db()
    user = conn.execute("SELECT * FROM users WHERE id=?", (user_id,)).fetchone()
    if not user:
        conn.close()
        return 'User not found', 404
    transactions = conn.execute(
        "SELECT * FROM transactions WHERE user_id=? ORDER BY date DESC", (user_id,)
    ).fetchall()
    totals = user_totals(user_id, conn)
    net = totals['deposits'] + totals['rewards'] - totals['withdrawals'] - totals['borrowed']
    messages = conn.execute(
        "SELECT * FROM messages WHERE receiver_id=? ORDER BY date_sent DESC", (user_id,)
    ).fetchall()
    conn.close()
    return render_template('user_dashboard.html', user=user, transactions=transactions,
                           totals=totals, net=net, messages=messages)


# ─────────────────────── USER SEND MESSAGE ───────────────────────
@app.route('/user/<int:user_id>/message', methods=['POST'])
def user_send_message(user_id):
    message_text = request.form.get('message', '').strip()
    if message_text:
        date_now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        conn = get_db()
        conn.execute(
            "INSERT INTO messages (sender_type,sender_id,receiver_id,message,date_sent) VALUES (?,?,?,?,?)",
            ('user', user_id, 0, message_text, date_now)
        )
        conn.commit()
        conn.close()
        flash('Message sent to admin!', 'success')
    return redirect(url_for('user_dashboard', user_id=user_id))


# ─────────────────────── RUN ───────────────────────
if __name__ == '__main__':
    port = int(os.environ.get('PORT', 8080))
    debug = os.environ.get('FLASK_DEBUG', '0') == '1'
    app.run(debug=debug, host='0.0.0.0', port=port)