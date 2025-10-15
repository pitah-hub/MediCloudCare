
import os
from datetime import datetime
from flask import Flask, render_template, request, redirect, url_for, session, flash
from werkzeug.security import generate_password_hash, check_password_hash
from models import db, User, Patient

app = Flask(__name__)
app.secret_key = os.getenv("FLASK_SECRET", "change-this-secret-in-prod")

# Database config: use DATABASE_URL (Render) else sqlite local fallback
DATABASE_URL = os.getenv('DATABASE_URL', 'sqlite:///patients.db')
if DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)
app.config['SQLALCHEMY_DATABASE_URI'] = DATABASE_URL
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db.init_app(app)

# Create tables
with app.app_context():
    db.create_all()


# Helpers
def login_required(fn):
    from functools import wraps
    @wraps(fn)
    def wrapper(*args, **kwargs):
        if 'user_id' not in session:
            flash("Please login first.", "warning")
            return redirect(url_for('login'))
        return fn(*args, **kwargs)
    return wrapper


@app.route('/')
def index():
    return render_template('index.html')


# ---------- AUTH ----------
@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        email = request.form.get('email', '').strip().lower()
        password = request.form.get('password', '')
        confirm = request.form.get('confirm-password', '')
        role = request.form.get('role')
        practice = request.form.get('practice-name')

        if not email or not password or password != confirm:
            flash("Please fill fields and ensure passwords match.", "danger")
            return redirect(url_for('register'))

        existing = User.query.filter_by(email=email).first()
        if existing:
            flash("Email already registered. Please login.", "warning")
            return redirect(url_for('login'))

        pw_hash = generate_password_hash(password)
        user = User(email=email, password_hash=pw_hash, role=role, practice_name=practice)
        db.session.add(user)
        db.session.commit()

        flash("Account created — please login.", "success")
        return redirect(url_for('login'))

    return render_template('register.html')


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form.get('email','').strip().lower()
        password = request.form.get('password','')
        user = User.query.filter_by(email=email).first()
        if user and check_password_hash(user.password_hash, password):
            session['user_id'] = user.id
            session['user_email'] = user.email
            flash("Login successful.", "success")
            return redirect(url_for('dashboard'))
        flash("Invalid credentials.", "danger")
        return redirect(url_for('login'))
    return render_template('login.html')


@app.route('/logout')
def logout():
    session.clear()
    flash("Logged out.", "info")
    return redirect(url_for('index'))


# ---------- DASHBOARD & PATIENT CRUD ----------
@app.route('/dashboard')
@login_required
def dashboard():
    patients = Patient.query.order_by(Patient.created_at.desc()).all()
    return render_template('database.html', patients=patients)


@app.route('/patient/add', methods=['GET', 'POST'])
@login_required
def add_patient():
    if request.method == 'POST':
        external_id = request.form.get('external_id') or None
        name = request.form.get('name')
        age = request.form.get('age') or None
        gender = request.form.get('gender')
        condition = request.form.get('condition')
        last_visit = request.form.get('last_visit')  # expect YYYY-MM-DD or empty

        if last_visit:
            try:
                last_visit = datetime.strptime(last_visit, "%Y-%m-%d").date()
            except ValueError:
                last_visit = None

        patient = Patient(
            external_id=external_id,
            name=name,
            age=int(age) if age else None,
            gender=gender,
            condition=condition,
            last_visit=last_visit
        )
        db.session.add(patient)
        db.session.commit()
        flash("Patient added.", "success")
        return redirect(url_for('dashboard'))

    return render_template('patient_add.html')


@app.route('/patient/edit/<int:pid>', methods=['GET', 'POST'])
@login_required
def edit_patient(pid):
    p = Patient.query.get_or_404(pid)
    if request.method == 'POST':
        p.external_id = request.form.get('external_id') or p.external_id
        p.name = request.form.get('name') or p.name
        age = request.form.get('age')
        p.age = int(age) if age else None
        p.gender = request.form.get('gender') or p.gender
        p.condition = request.form.get('condition') or p.condition
        lv = request.form.get('last_visit')
        if lv:
            try:
                p.last_visit = datetime.strptime(lv, "%Y-%m-%d").date()
            except ValueError:
                pass
        db.session.commit()
        flash("Patient updated.", "success")
        return redirect(url_for('dashboard'))

    return render_template('patient_edit.html', patient=p)


@app.route('/patient/delete/<int:pid>', methods=['POST'])
@login_required
def delete_patient(pid):
    p = Patient.query.get_or_404(pid)
    db.session.delete(p)
    db.session.commit()
    flash("Patient removed.", "info")
    return redirect(url_for('dashboard'))


# Run
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.getenv('PORT', 5000)), debug=True)
