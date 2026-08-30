from flask import Blueprint, render_template, request, redirect, url_for, flash, session
from werkzeug.security import generate_password_hash, check_password_hash
from .db import users_col
import uuid

bp = Blueprint('auth', __name__)

# ===============================
# CURRENT USER
# ===============================
def get_current_user():
    uid = session.get('user_id')
    if not uid:
        return None
    return users_col.find_one({'id': uid})


# ===============================
# LOGIN
# ===============================
@bp.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form.get('email')
        pwd = request.form.get('password')

        user = users_col.find_one({'email': email})

        if user and check_password_hash(user.get('password_hash', ''), pwd):
            session.clear()
            session['user_id'] = user['id']
            session['is_admin'] = user.get('is_admin', False)

            flash(f'Welcome, {user.get("name", "User")}!')
            return redirect(url_for('main.menu'))

        flash('Invalid email or password')
        return redirect(url_for('auth.login'))

    return render_template('login.html', user=get_current_user())


# ===============================
# REGISTER
# ===============================
@bp.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        name = request.form.get('name')
        email = request.form.get('email')
        pwd = request.form.get('password')

        if users_col.find_one({'email': email}):
            flash("Email already exists")
            return redirect(url_for('auth.register'))

        users_col.insert_one({
            'id': str(uuid.uuid4()),
            'name': name,
            'email': email,
            'password_hash': generate_password_hash(pwd),
            'is_admin': False
        })

        flash("Registered successfully")
        return redirect(url_for('auth.login'))

    return render_template('register.html')


# ===============================
# LOGOUT
# ===============================
@bp.route('/logout')
def logout():
    session.clear()
    flash('Logged out successfully')
    return redirect(url_for('main.menu'))
