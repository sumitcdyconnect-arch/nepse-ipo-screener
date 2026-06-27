from flask import Flask, render_template, request, redirect, url_for, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime
from dotenv import load_dotenv
import os

load_dotenv()

app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'nepse-secret-123')
database_url = os.environ.get('DATABASE_URL', 'sqlite:///nepse.db')
if database_url.startswith('postgres://'):
    database_url = database_url.replace('postgres://', 'postgresql://', 1)
app.config['SQLALCHEMY_DATABASE_URI'] = database_url

db = SQLAlchemy(app)
login_manager = LoginManager(app)

class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True, nullable=False)
    phone = db.Column(db.String(15), unique=True, nullable=False)
    password_hash = db.Column(db.String(256), nullable=False)
    applications = db.relationship('Application', backref='user', lazy=True)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

class IPO(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200), nullable=False)
    sector = db.Column(db.String(100))
    rating = db.Column(db.String(20))
    is_good = db.Column(db.Boolean, default=False)
    reason = db.Column(db.String(500))
    open_date = db.Column(db.String(100))
    close_date = db.Column(db.String(100))
    shares_available = db.Column(db.String(100))
    vision = db.Column(db.Text)
    promoters = db.Column(db.Text)
    past_performance = db.Column(db.Text)
    ipo_motive = db.Column(db.Text)
    liabilities = db.Column(db.Text)
    verdict = db.Column(db.Text)

class Application(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    ipo_name = db.Column(db.String(100), nullable=False)
    amount = db.Column(db.Integer, nullable=False)
    date = db.Column(db.DateTime, default=datetime.utcnow)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    status = db.Column(db.String(50), default='Applied')

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

@app.route('/')
def index():
    ipos = IPO.query.all()
    return render_template('index.html', ipos=ipos)

@app.route('/tracker', methods=['GET', 'POST'])
def tracker():
    if request.method == 'POST':
        if not current_user.is_authenticated:
            return jsonify({'error': 'login_required'}), 401
        ipo_name = request.form['ipo_name']
        amount = int(request.form['amount'])
        entry = Application(ipo_name=ipo_name, amount=amount, user_id=current_user.id)
        db.session.add(entry)
        db.session.commit()
        return redirect(url_for('tracker'))
    applications = Application.query.filter_by(user_id=current_user.id).all() if current_user.is_authenticated else []
    total_spent = sum(a.amount for a in applications)
    return render_template('tracker.html', applications=applications, total_spent=total_spent)

@app.route('/allotment')
def allotment():
    return render_template('allotment.html')

@app.route('/register', methods=['POST'])
def register():
    username = request.form['username']
    phone = request.form['phone']
    password = request.form['password']
    if User.query.filter_by(username=username).first():
        return jsonify({'error': 'Username already taken'}), 400
    if User.query.filter_by(phone=phone).first():
        return jsonify({'error': 'Phone already registered'}), 400
    user = User(username=username, phone=phone)
    user.set_password(password)
    db.session.add(user)
    db.session.commit()
    login_user(user)
    return jsonify({'success': True})

@app.route('/login', methods=['POST'])
def login():
    username = request.form['username']
    password = request.form['password']
    user = User.query.filter_by(username=username).first()
    if user and user.check_password(password):
        login_user(user)
        return jsonify({'success': True})
    return jsonify({'error': 'Wrong username or password'}), 401

@app.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('index'))

ADMIN_PASSWORD = os.environ.get('ADMIN_PASSWORD')

@app.route('/admin', methods=['GET', 'POST'])
def admin():
    if request.args.get('key') != ADMIN_PASSWORD:
        return 'Access denied', 403
    if request.method == 'POST':
        is_good = request.form['is_good'] == 'true'
        ipo = IPO(
            name=request.form['name'],
            sector=request.form['sector'],
            rating=request.form.get('rating', 'N/A'),
            reason=request.form['reason'],
            is_good=is_good,
            open_date=request.form.get('open_date'),
            close_date=request.form.get('close_date'),
            shares_available=request.form.get('shares_available'),
            vision=request.form.get('vision'),
            promoters=request.form.get('promoters'),
            past_performance=request.form.get('past_performance'),
            ipo_motive=request.form.get('ipo_motive'),
            liabilities=request.form.get('liabilities'),
            verdict=request.form.get('verdict')
        )
        db.session.add(ipo)
        db.session.commit()
        return redirect(url_for('admin', key=ADMIN_PASSWORD))
    ipos = IPO.query.all()
    return render_template('admin.html', ipos=ipos)

@app.route('/admin/delete/<int:id>')
def delete_ipo(id):
    ipo = IPO.query.get_or_404(id)
    db.session.delete(ipo)
    db.session.commit()
    return redirect(url_for('admin', key=ADMIN_PASSWORD))


@app.route('/tracker/edit/<int:id>', methods=['POST'])
def edit_application(id):
    app_entry = Application.query.get_or_404(id)
    if app_entry.user_id != current_user.id:
        return jsonify({'error': 'Unauthorized'}), 403
    app_entry.ipo_name = request.form['ipo_name']
    app_entry.amount = int(request.form['amount'])
    db.session.commit()
    return jsonify({'success': True})

@app.route('/tracker/delete/<int:id>', methods=['POST'])
def delete_application(id):
    app_entry = Application.query.get_or_404(id)
    if app_entry.user_id != current_user.id:
        return jsonify({'error': 'Unauthorized'}), 403
    db.session.delete(app_entry)
    db.session.commit()
    return jsonify({'success': True})

@app.route('/ipo/<int:id>')
def ipo_detail(id):
    ipo = IPO.query.get_or_404(id)
    return render_template('ipo_detail.html', ipo=ipo)


@app.route('/tracker/status/<int:id>', methods=['POST'])
def update_status(id):
    app_entry = Application.query.get_or_404(id)
    if app_entry.user_id != current_user.id:
        return jsonify({'error': 'Unauthorized'}), 403
    app_entry.status = request.form['status']
    db.session.commit()
    return jsonify({'success': True})


with app.app_context():
    db.drop_all()
    db.create_all()

if __name__ == '__main__':
    app.run(debug=True)