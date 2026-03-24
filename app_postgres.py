from flask import Flask, render_template, request, redirect, session, url_for, flash
from flask_sqlalchemy import SQLAlchemy
from werkzeug.utils import secure_filename
from datetime import datetime
from functools import wraps
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

app = Flask(__name__)

# ─────────────────────── CONFIGURATION ───────────────────────
app.secret_key = os.environ.get('SECRET_KEY', 'savingsapp-secret-key-2024')
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL', 'postgresql://postgres:postgres@localhost:5432/savingsapp')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Upload folder config
UPLOAD_FOLDER = os.path.join('static', 'uploads')
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'webp'}
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# Initialize database
db = SQLAlchemy(app)


# ─────────────────────── DATABASE MODELS ───────────────────────
class User(db.Model):
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255), nullable=False)
    id_number = db.Column(db.String(50))
    phone = db.Column(db.String(20))
    location = db.Column(db.String(255))
    photo = db.Column(db.String(500))
    notes = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    transactions = db.relationship('Transaction', backref='user', lazy=True, cascade='all, delete-orphan')
    messages = db.relationship('Message', backref='receiver', lazy=True, cascade='all, delete-orphan')
    
    def __repr__(self):
        return f'<User {self.name}>'


class Transaction(db.Model):
    __tablename__ = 'transactions'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='CASCADE'), nullable=False)
    type = db.Column(db.String(50), nullable=False)
    amount = db.Column(db.Float, nullable=False)
    note = db.Column(db.Text)
    date = db.Column(db.DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f'<Transaction {self.type} {self.amount}>'


class Admin(db.Model):
    __tablename__ = 'admin'
    
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(100), unique=True, nullable=False)
    password = db.Column(db.String(255), nullable=False)
    
    def __repr__(self):
        return f'<Admin {self.username}>'


class Message(db.Model):
    __tablename__ = 'messages'
    
    id = db.Column(db.Integer, primary_key=True)
    sender_type = db.Column(db.String(50))
    sender_id = db.Column(db.Integer)
    receiver_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='CASCADE'))
    message = db.Column(db.Text)
    date_sent = db.Column(db.DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f'<Message to user {self.receiver_id}>'


# ─────────────────────── DATABASE INITIALIZATION ───────────────────────
def init_db():
    """Initialize database tables and default data"""
    with app.app_context():
        db.create_all()
        
        # Create default admin if doesn't exist
        if not Admin.query.filter_by(username='admin').first():
            admin = Admin(username='admin', password='admin123')
            db.session.add(admin)
            db.session.commit()
            print("✓ Default admin account created")
        else:
            print("✓ Admin account already exists")


# ─────────────────────── HELPERS ───────────────────────
def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


def save_photo(file_obj):
    """Save an uploaded photo and return the relative path, or None."""
    if file_obj and file_obj.filename and allowed_file(file_obj.filename):
        filename = f"{datetime.now().strftime('%Y%m%d%H%M%S%f')}_{secure_filename(file_obj.filename)}"
        path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file_obj.save(path)
        return path.replace('\\', '/')
    return None


def user_totals(user_id):
    """Calculate totals for a user by transaction type"""
    transactions = Transaction.query.filter_by(user_id=user_id).all()
    
    totals = {
        'deposits': 0,
        'withdrawals': 0,
        'rewards': 0,
        'borrowed': 0,
    }
    
    for t in transactions:
        t_type = t.type.lower()
        if t_type == 'deposit':
            totals['deposits'] += t.amount
        elif t_type == 'withdrawal':
            totals['withdrawals'] += t.amount
        elif t_type == 'reward':
            totals['rewards'] += t.amount
        elif t_type == 'loan':
            totals['borrowed'] += t.amount
    
    return totals


def get_demo_user_id():
    """Get the first user ID (for demo purposes)"""
    user = User.query.first()
    return user.id if user else None


def admin_required(f):
    """Decorator to check if user is logged in as admin"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'admin' not in session:
            return redirect(url_for('admin_login'))
        return f(*args, **kwargs)
    return decorated_function


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
        
        admin = Admin.query.filter_by(username=username, password=password).first()
        
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
@admin_required
def admin_dashboard():
    users = User.query.order_by(User.created_at.desc()).all()
    
    # Compute totals per user
    user_data = []
    for u in users:
        totals = user_totals(u.id)
        net = totals['deposits'] + totals['rewards'] - totals['withdrawals'] - totals['borrowed']
        user_data.append({'user': u, 'totals': totals, 'net': net})
    
    # Global stats
    stats = {
        'total_users': User.query.count(),
        'total_deposits': db.func.sum(Transaction.amount).filter(
            Transaction.type == 'deposit'
        ),
        'total_withdraw': db.func.sum(Transaction.amount).filter(
            Transaction.type == 'withdrawal'
        ),
        'total_loans': db.func.sum(Transaction.amount).filter(
            Transaction.type == 'loan'
        ),
        'total_rewards': db.func.sum(Transaction.amount).filter(
            Transaction.type == 'reward'
        ),
    }
    
    # Calculate sums properly
    for key in stats:
        if key != 'total_users':
            result = db.session.query(db.func.coalesce(db.func.sum(Transaction.amount), 0)).filter(
                Transaction.type == key.replace('total_', '')
            ).scalar()
            stats[key] = result if result else 0
    
    return render_template('admin_dashboard.html', user_data=user_data, stats=stats)


# ─────────────────────── REGISTER USER ───────────────────────
@app.route('/admin/register', methods=['GET', 'POST'])
@admin_required
def register_user():
    if request.method == 'POST':
        name = request.form['name']
        id_number = request.form.get('id_number', '')
        phone = request.form.get('phone', '')
        location = request.form.get('location', '')
        notes = request.form.get('notes', '')
        photo_path = save_photo(request.files.get('photo'))
        
        user = User(
            name=name,
            id_number=id_number,
            phone=phone,
            location=location,
            photo=photo_path,
            notes=notes
        )
        
        db.session.add(user)
        db.session.commit()
        
        flash(f'User "{name}" registered successfully!', 'success')
        return redirect(url_for('admin_dashboard'))
    
    return render_template('register_user.html')


# ─────────────────────── USER DETAIL (ADMIN) ───────────────────────
@app.route('/admin/user/<int:user_id>')
@admin_required
def user_detail(user_id):
    user = User.query.get_or_404(user_id)
    transactions = Transaction.query.filter_by(user_id=user_id).order_by(Transaction.date.desc()).all()
    totals = user_totals(user_id)
    net = totals['deposits'] + totals['rewards'] - totals['withdrawals'] - totals['borrowed']
    messages = Message.query.filter_by(receiver_id=user_id).order_by(Message.date_sent.desc()).all()
    
    return render_template('user_detail.html', user=user, transactions=transactions,
                           totals=totals, net=net, messages=messages)


# ─────────────────────── ADD TRANSACTION ───────────────────────
@app.route('/admin/transaction/<int:user_id>', methods=['GET', 'POST'])
@admin_required
def add_transaction(user_id):
    user = User.query.get_or_404(user_id)
    
    if request.method == 'POST':
        t_type = request.form['type']
        amount = float(request.form['amount'])
        note = request.form.get('note', '')
        
        transaction = Transaction(
            user_id=user_id,
            type=t_type,
            amount=amount,
            note=note
        )
        
        db.session.add(transaction)
        db.session.commit()
        
        flash(f'Transaction ({t_type}) of {amount:,.0f} recorded.', 'success')
        return redirect(url_for('user_detail', user_id=user_id))
    
    return render_template('add_transaction.html', user=user)


# ─────────────────────── MESSAGING ───────────────────────
@app.route('/admin/message', methods=['GET', 'POST'])
@admin_required
def admin_message():
    users = User.query.order_by(User.name).all()
    
    if request.method == 'POST':
        message_text = request.form['message']
        receiver_id = request.form['receiver_id']
        
        if receiver_id == 'all':
            all_users = User.query.all()
            for user in all_users:
                msg = Message(
                    sender_type='admin',
                    sender_id=0,
                    receiver_id=user.id,
                    message=message_text
                )
                db.session.add(msg)
        else:
            msg = Message(
                sender_type='admin',
                sender_id=0,
                receiver_id=int(receiver_id),
                message=message_text
            )
            db.session.add(msg)
        
        db.session.commit()
        flash('Message sent!', 'success')
        return redirect(url_for('admin_dashboard'))
    
    return render_template('admin_message.html', users=users)


# ─────────────────────── USER DASHBOARD ───────────────────────
@app.route('/user/<int:user_id>')
def user_dashboard(user_id):
    user = User.query.get_or_404(user_id)
    transactions = Transaction.query.filter_by(user_id=user_id).order_by(Transaction.date.desc()).all()
    totals = user_totals(user_id)
    net = totals['deposits'] + totals['rewards'] - totals['withdrawals'] - totals['borrowed']
    messages = Message.query.filter_by(receiver_id=user_id).order_by(Message.date_sent.desc()).all()
    
    return render_template('user_dashboard.html', user=user, transactions=transactions,
                           totals=totals, net=net, messages=messages)


# ─────────────────────── ERROR HANDLERS ───────────────────────
@app.errorhandler(404)
def not_found(error):
    return 'Page not found', 404


@app.errorhandler(500)
def server_error(error):
    return 'Server error', 500


if __name__ == '__main__':
    with app.app_context():
        init_db()
        print("✓ Database initialized")
    
    app.run(debug=True, host='localhost', port=5000)
