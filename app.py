from flask import Flask, render_template, request, redirect, url_for
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
from dotenv import load_dotenv
import os

load_dotenv()

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///nepse.db'
app.config['SECRET_KEY'] = 'nepse-secret-123'
db = SQLAlchemy(app)


class IPO(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    sector = db.Column(db.String(50))
    rating = db.Column(db.String(10))
    is_good = db.Column(db.Boolean, default=False)
    reason = db.Column(db.String(200))

class Application(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    ipo_name = db.Column(db.String(100), nullable=False)
    amount = db.Column(db.Integer, nullable=False)
    date = db.Column(db.DateTime, default=datetime.utcnow)

@app.route('/')
def index():
    ipos = IPO.query.all()
    return render_template('index.html', ipos=ipos)

@app.route('/tracker', methods=['GET', 'POST'])
def tracker():
    if request.method == 'POST':
        ipo_name = request.form['ipo_name']
        amount = int(request.form['amount'])
        app_entry = Application(ipo_name=ipo_name, amount=amount)
        db.session.add(app_entry)
        db.session.commit()
        return redirect(url_for('tracker'))
    applications = Application.query.all()
    total_spent = sum(a.amount for a in applications)
    return render_template('tracker.html', applications=applications, total_spent=total_spent)

@app.route('/allotment')
def allotment():
    return render_template('allotment.html')


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
            rating=request.form['rating'],
            reason=request.form['reason'],
            is_good=is_good
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

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True)