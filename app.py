from flask import Flask, render_template, request, redirect, session, url_for, flash
import psycopg2
from psycopg2.extras import RealDictCursor
import os
from datetime import datetime
from werkzeug.utils import secure_filename
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', 'savingsapp-secret-key-2024')

import traceback
from flask import Response

@app.errorhandler(500)
def internal_error(e):
    tb = traceback.format_exc()
    return Response(f'<pre style="color:red;padding:2rem;">{tb}</pre>', status=500)

# PostgreSQL Connection
# PostgreSQL Connection
DB_CONFIG = {
    'host': os.environ.get('PGHOST', 'localhost'),
    'database': os.environ.get('PGDATABASE', 'savings_app'),
    'user': os.environ.get('PGUSER', 'postgres'),
    'password': os.environ.get('PGPASSWORD', 'postgres'),
    'port': os.environ.get('PGPORT', '5432')
}

UPLOAD_FOLDER = os.path.join('static', 'uploads')
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'webp'}

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
os.makedirs(UPLOAD_FOLDER, exist_ok=True)


def get_db():
    conn = psycopg2.connect(**DB_CONFIG)
    return conn


def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


# ─────────────────────── DATABASE SETUP ───────────────────────
def init_db():
    pass  # Tables already created in pgAdmin


# ─────────────────────── HELPERS ───────────────────────
def save_photo(file_obj):
    """Save an uploaded photo and return the relative path, or None."""
    if file_obj and file_obj.filename and allowed_file(file_obj.filename):
        filename = f"{datetime.now().strftime('%Y%m%d%H%M%S%f')}_{secure_filename(file_obj.filename)}"
        path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file_obj.save(path)
        return path.replace('\\', '/')
    return None


def user_totals(user_id, conn):
    cursor = conn.cursor(cursor_factory=RealDictCursor)
    def _sum(t):
        cursor.execute(
            "SELECT COALESCE(SUM(amount),0) AS v FROM transactions WHERE user_id=%s AND type=%s",
            (user_id, t)
        )
        return cursor.fetchone()['v']
    result = {
        'deposits':    _sum('deposit'),
        'withdrawals': _sum('withdrawal'),
        'rewards':     _sum('reward'),
        'borrowed':    _sum('loan'),
    }
    cursor.close()
    return result


def get_demo_user_id():
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT id FROM users ORDER BY id LIMIT 1")
    row = cursor.fetchone()
    cursor.close()
    conn.close()
    return row[0] if row else None


# ─────────────────────── WELCOME ───────────────────────
@app.route('/')
def welcome():
    return render_template('welcome.html', demo_user_id=get_demo_user_id())


# ─────────────────────── ADMIN AUTH ───────────────────────
@app.route('/admin', methods=['GET', 'POST'])
def admin_login():
    error = None
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute(
            "SELECT * FROM admin WHERE username=%s AND password=%s", 
            (username, password)
        )
        admin = cursor.fetchone()
        cursor.close()
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
    cursor = conn.cursor(cursor_factory=RealDictCursor)
    cursor.execute("SELECT * FROM users ORDER BY created_at DESC")
    users = cursor.fetchall()

    # Compute totals per user
    user_data = []
    for u in users:
        totals = user_totals(u['id'], conn)
        net = totals['deposits'] + totals['rewards'] - totals['withdrawals'] - totals['borrowed']
        user_data.append({'user': u, 'totals': totals, 'net': net})

    # Global stats
    cursor.execute("SELECT COUNT(*) AS v FROM users")
    total_users = cursor.fetchone()['v']

    cursor.execute("SELECT COALESCE(SUM(amount),0) AS v FROM transactions WHERE type='deposit'")
    total_deposits = cursor.fetchone()['v']

    cursor.execute("SELECT COALESCE(SUM(amount),0) AS v FROM transactions WHERE type='withdrawal'")
    total_withdraw = cursor.fetchone()['v']

    cursor.execute("SELECT COALESCE(SUM(amount),0) AS v FROM transactions WHERE type='loan'")
    total_loans = cursor.fetchone()['v']

    cursor.execute("SELECT COALESCE(SUM(amount),0) AS v FROM transactions WHERE type='reward'")
    total_rewards = cursor.fetchone()['v']

    stats = {
        'total_users': total_users,
        'total_deposits': total_deposits,
        'total_withdraw': total_withdraw,
        'total_loans': total_loans,
        'total_rewards': total_rewards,
    }
    cursor.close()
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
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO users (name,id_number,phone,location,photo,notes) VALUES (%s,%s,%s,%s,%s,%s)",
            (name, id_number, phone, location, photo_path, notes)
        )
        conn.commit()
        cursor.close()
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
    cursor = conn.cursor(cursor_factory=RealDictCursor)
    cursor.execute("SELECT * FROM users WHERE id=%s", (user_id,))
    user = cursor.fetchone()
    if not user:
        cursor.close()
        conn.close()
        return 'User not found', 404
    cursor.execute(
        "SELECT * FROM transactions WHERE user_id=%s ORDER BY date DESC", (user_id,)
    )
    transactions = cursor.fetchall()
    totals = user_totals(user_id, conn)
    net = totals['deposits'] + totals['rewards'] - totals['withdrawals'] - totals['borrowed']
    cursor.execute(
        "SELECT * FROM messages WHERE receiver_id=%s ORDER BY date_sent DESC", (user_id,)
    )
    msgs = cursor.fetchall()
    cursor.close()
    conn.close()
    return render_template('user_detail.html', user=user, transactions=transactions,
                           totals=totals, net=net, messages=msgs)


# ─────────────────────── ADD TRANSACTION ───────────────────────
@app.route('/admin/transaction/<int:user_id>', methods=['GET', 'POST'])
def add_transaction(user_id):
    if 'admin' not in session:
        return redirect(url_for('admin_login'))
    conn = get_db()
    cursor = conn.cursor(cursor_factory=RealDictCursor)
    cursor.execute("SELECT * FROM users WHERE id=%s", (user_id,))
    user = cursor.fetchone()
    if request.method == 'POST':
        t_type = request.form['type']
        amount = float(request.form['amount'])
        note   = request.form.get('note', '')
        cursor.execute(
            "INSERT INTO transactions (user_id,type,amount,note) VALUES (%s,%s,%s,%s)",
            (user_id, t_type, amount, note)
        )
        conn.commit()
        cursor.close()
        conn.close()
        flash(f'Transaction ({t_type}) of {amount:,.0f} recorded.', 'success')
        return redirect(url_for('user_detail', user_id=user_id))
    cursor.close()
    conn.close()
    return render_template('add_transaction.html', user=user)


# ─────────────────────── MESSAGING ───────────────────────
@app.route('/admin/message', methods=['GET', 'POST'])
def admin_message():
    if 'admin' not in session:
        return redirect(url_for('admin_login'))
    conn = get_db()
    cursor = conn.cursor(cursor_factory=RealDictCursor)
    cursor.execute("SELECT id, name FROM users ORDER BY name")
    users = cursor.fetchall()
    if request.method == 'POST':
        message_text = request.form['message']
        receiver_id  = request.form['receiver_id']
        if receiver_id == 'all':
            cursor.execute("SELECT id FROM users")
            all_ids = cursor.fetchall()
            for row in all_ids:
                cursor.execute(
                    "INSERT INTO messages (sender_type,sender_id,receiver_id,message) VALUES (%s,%s,%s,%s)",
                    ('admin', 0, row['id'], message_text)
                )
        else:
            cursor.execute(
                "INSERT INTO messages (sender_type,sender_id,receiver_id,message) VALUES (%s,%s,%s,%s)",
                ('admin', 0, int(receiver_id), message_text)
            )
        conn.commit()
        cursor.close()
        conn.close()
        flash('Message sent!', 'success')
        return redirect(url_for('admin_dashboard'))
    cursor.close()
    conn.close()
    return render_template('admin_message.html', users=users)


# ─────────────────────── USER DASHBOARD ───────────────────────
@app.route('/user/<int:user_id>')
def user_dashboard(user_id):
    conn = get_db()
    cursor = conn.cursor(cursor_factory=RealDictCursor)
    cursor.execute("SELECT * FROM users WHERE id=%s", (user_id,))
    user = cursor.fetchone()
    if not user:
        cursor.close()
        conn.close()
        return 'User not found', 404
    cursor.execute(
        "SELECT * FROM transactions WHERE user_id=%s ORDER BY date DESC", (user_id,)
    )
    transactions = cursor.fetchall()
    totals = user_totals(user_id, conn)
    net = totals['deposits'] + totals['rewards'] - totals['withdrawals'] - totals['borrowed']
    cursor.execute(
        "SELECT * FROM messages WHERE receiver_id=%s ORDER BY date_sent DESC", (user_id,)
    )
    messages = cursor.fetchall()
    cursor.close()
    conn.close()
    return render_template('user_dashboard.html', user=user, transactions=transactions,
                           totals=totals, net=net, messages=messages)


# ─────────────────────── USER SEND MESSAGE ───────────────────────
@app.route('/user/<int:user_id>/message', methods=['POST'])
def user_send_message(user_id):
    message_text = request.form.get('message', '').strip()
    if message_text:
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO messages (sender_type,sender_id,receiver_id,message) VALUES (%s,%s,%s,%s)",
            ('user', user_id, 0, message_text)
        )
        conn.commit()
        cursor.close()
        conn.close()
        flash('Message sent to admin!', 'success')
    return redirect(url_for('user_dashboard', user_id=user_id))


# ─────────────────────── RUN ───────────────────────
if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(debug=True, host='0.0.0.0', port=port)