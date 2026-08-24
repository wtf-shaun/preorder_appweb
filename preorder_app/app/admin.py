from flask import (
    Blueprint, render_template, request, redirect,
    url_for, flash, session
)
from werkzeug.utils import secure_filename
from .db import users_col, items_col, orders_col
import uuid
import os

bp = Blueprint('admin', __name__)
UPLOAD_FOLDER = os.path.join('app', 'static', 'uploads')

def is_admin():
    uid = session.get('user_id')
    if not uid:
        return False
    user = users_col.find_one({'id': uid})
    return user and user.get('is_admin') is True


# ===============================
# ADMIN DASHBOARD
# ===============================


@bp.route('/')
def index():
    if not is_admin():
        return redirect(url_for('auth.login'))

    users = list(users_col.find({}, {'_id': 0}))
    items = list(items_col.find({}, {'_id': 0}))
    orders = list(orders_col.find({}, {'_id': 0}))

    return render_template('admin.html', users=users, items=items, orders=orders)


# ===============================
# ADD ITEM
# ===============================

@bp.route('/add_item', methods=['POST'])
def add_item():
    if not is_admin():
        return redirect(url_for('auth.login'))

    name = request.form.get('name')
    price = request.form.get('price')
    category = request.form.get('category', 'food')
    image = request.files.get('image')

    image_filename = None

    if image and image.filename:
        os.makedirs(UPLOAD_FOLDER, exist_ok=True)
        filename = secure_filename(image.filename)
        image_filename = str(uuid.uuid4()) + "_" + filename
        image.save(os.path.join(UPLOAD_FOLDER, image_filename))

    items_col.insert_one({
        'id': str(uuid.uuid4())[:8],
        'name': name,
        'price': int(price),
        'category': category if category in {'food', 'beverage'} else 'food',
        'image': image_filename
    })

    flash("Item added")
    return redirect(url_for('admin.index'))


@bp.route('/delete_item/<item_id>', methods=['POST'])
def delete_item(item_id):
    if not is_admin():
        return redirect(url_for('auth.login'))

    items_col.delete_one({'id': item_id})
    flash("Item deleted")
    return redirect(url_for('admin.index'))

# ===============================
# EDIT USER
# ===============================
@bp.route('/edit_user/<user_id>', methods=['GET', 'POST'])
def edit_user(user_id):
    if not is_admin():
        return redirect(url_for('auth.login'))

    user = users_col.find_one({'id': user_id})

    if not user:
        flash('User not found')
        return redirect(url_for('admin.index'))

    if request.method == 'POST':
        update_data = {}

        name = request.form.get('name')
        email = request.form.get('email')

        if name:
            update_data['name'] = name

        if email:
            update_data['email'] = email

        # checkbox handling (important fix)
        update_data['is_admin'] = True if request.form.get('is_admin') else False

        if update_data:
            users_col.update_one(
                {'id': user_id},
                {'$set': update_data}
            )
            flash('User updated')
        else:
            flash('No changes made')

        return redirect(url_for('admin.index'))

    return render_template('edit_user.html', user=user)

# ===============================
# DELETE USER
# ===============================
@bp.route('/delete_user', methods=['POST'])
def delete_user():
    if not is_admin():
        return redirect(url_for('auth.login'))

    user_id = request.form.get('user_id')

    if not user_id:
        flash("Invalid request")
        return redirect(url_for('admin.index'))

    # Prevent self delete
    if user_id == session.get('user_id'):
        flash("You cannot delete your own account!")
        return redirect(url_for('admin.index'))

    result = users_col.delete_one({'id': user_id})

    if result.deleted_count == 0:
        flash("User not found")
    else:
        flash('User deleted')

    return redirect(url_for('admin.index'))


# ===============================
# EMAIL ALL USERS
# ===============================

@bp.route('/send_email', methods=['GET', 'POST'])
def send_email():
    if not is_admin():
        return redirect(url_for('auth.login'))

    flash("Email Module is Currently Under Work")
    return redirect(url_for('admin.index'))

