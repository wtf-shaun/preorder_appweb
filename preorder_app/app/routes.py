from flask import Blueprint, render_template, request, redirect, url_for, flash, session, send_file
from .db import users_col, items_col, carts_col, orders_col, categories_col
import uuid
from datetime import datetime
import threading
import os

from .utils.pdf_invoice import generate_invoice_pdf

bp = Blueprint('main', __name__)

# ===============================
# CAFETERIA
# ===============================
@bp.route('/cafeteria')
def cafeteria():
    user = current_user()
    orders = list(orders_col.find({}, {'_id': 0}))

    return render_template('cafeteria.html', orders=orders, user=user)

from flask import session, redirect, url_for, current_app, flash

# ===============================
# Dev Tester
# ===============================

@bp.route('/demo-login')
def demo_login():
    # No environment or debug checks! It just works immediately.
    
    # Inject mock user data into the session
    session['user_id'] = 9999
    session['user_name'] = 'Demo Tester'
    session['user_email'] = 'tester@example.com'
    session['role'] = 'student' 

    flash("Logged in as Demo Tester!", "success")
    
    return redirect(url_for('main.menu'))

# ===============================
# CURRENT USER
# ===============================
# ===============================
# CURRENT USER
# ===============================
def current_user():
    uid = session.get('user_id')
    if not uid:
        return None
        
    # Catch the Demo Tester BEFORE asking the database
    if uid == 9999:
        return {
            'id': 9999,
            'name': session.get('user_name', 'Demo Tester'),
            'email': session.get('user_email', 'tester@example.com'),
            'role': session.get('role', 'student')
        }

    # If it's a real user, look them up in the database normally
    return users_col.find_one({'id': uid})
def get_cart_count():
    user = current_user()

    if not user:
        return 0

    cart = carts_col.find_one({'user_id': user['id']})

    if not cart or not cart.get('items'):
        return 0

    return sum(
        int(item.get('qty', 0))
        for item in cart['items']
    )


@bp.app_context_processor
def inject_cart_count():
    return {
        'cart_count': get_cart_count()
    }
    
def delete_order_after_delay(order_id, delay=60):
    import time
    time.sleep(delay)
    orders_col.delete_one({'id': order_id})
# ===============================
# HOME
# ===============================
@bp.route('/')
def index():
    return redirect(url_for('main.menu'))


# ===============================
# MENU
# ===============================
@bp.route('/menu')
def menu():
    items = list(items_col.find({}, {'_id': 0}))
    for item in items:
        item.setdefault('category', 'food')
    user = current_user()
    cart = carts_col.find_one({'user_id': user['id']}) if user else None
    defaults = [
        {'slug': 'food', 'name': 'Food'},
        {'slug': 'beverage', 'name': 'Beverages'}
    ]
    for category in defaults:
        categories_col.update_one(
            {'slug': category['slug']},
            {'$setOnInsert': category},
            upsert=True
        )
    categories = list(categories_col.find({}, {'_id': 0}).sort('name', 1))
    cart_item_ids = {
        cart_item['item_id']
        for cart_item in (cart or {}).get('items', [])
    }
    cart_quantities = {
        cart_item['item_id']: cart_item.get('qty', 0)
        for cart_item in (cart or {}).get('items', [])
    }

    return render_template(
        'menu.html',
        items=items,
        user=user,
        cart_item_ids=cart_item_ids,
        cart_quantities=cart_quantities,
        categories=categories,
    )


# ===============================
# VIEW CART
# ===============================
@bp.route('/cart')
def view_cart():
    user = current_user()

    if not user:
        flash('Login first')
        return redirect(url_for('auth.login'))

    cart = carts_col.find_one({'user_id': user['id']})

    if not cart or not cart.get('items'):
        return render_template('cart.html', cart_details=[], total=0, user=user)

    cart_details = []
    total = 0

    for c in cart['items']:
        item = items_col.find_one({'id': c['item_id']})

        if not item:
            continue

        subtotal = item['price'] * c['qty']
        total += subtotal

        cart_details.append({
            'item_id': item['id'],
            'name': item['name'],
            'qty': c['qty'],
            'price': item['price'],
            'subtotal': subtotal
        })

    return render_template('cart.html', cart_details=cart_details, total=total, user=user)


# ===============================
# ADD TO CART
# ===============================
@bp.route('/add_to_cart', methods=['POST'])
def add_to_cart():
    user = current_user()

    if not user:
        flash('Please login first')
        return redirect(url_for('auth.login'))

    item_id = request.form.get('item_id')

    try:
        quantity = int(request.form.get('quantity', 1))
    except (TypeError, ValueError):
        quantity = 1

    # Keep quantity sensible
    quantity = max(1, min(quantity, 20))

    user_id = user['id']

    # Make sure the item actually exists
    item = items_col.find_one({'id': item_id})

    if not item:
        flash('Item not found')
        return redirect(url_for('main.menu'))

    cart = carts_col.find_one({'user_id': user_id})

    if not cart:
        carts_col.insert_one({
            'user_id': user_id,
            'items': [
                {
                    'item_id': item_id,
                    'qty': quantity
                }
            ]
        })

    else:
        found = False

        for cart_item in cart['items']:
            if cart_item['item_id'] == item_id:

                cart_item['qty'] += quantity

                # Prevent an item from exceeding 20
                cart_item['qty'] = min(cart_item['qty'], 20)

                found = True
                break

        if not found:
            cart['items'].append({
                'item_id': item_id,
                'qty': quantity
            })

        carts_col.update_one(
            {'user_id': user_id},
            {'$set': {'items': cart['items']}}
        )

    if quantity == 1:
        flash(f'{item["name"]} added to cart')
    else:
        flash(f'{quantity} × {item["name"]} added to cart')
    return redirect(url_for('main.menu'))

# ===============================
# INCREASE CART
# ===============================
@bp.route('/cart/increase', methods=['POST'])
def cart_increase():
    user = current_user()
    if not user:
        return redirect(url_for('auth.login'))

    item_id = request.form.get('item_id')

    cart = carts_col.find_one({'user_id': user['id']})

    if not cart:
        return redirect(url_for('main.view_cart'))

    for item in cart['items']:
        if item['item_id'] == item_id:
            item['qty'] += 1

    carts_col.update_one(
        {'user_id': user['id']},
        {'$set': {'items': cart['items']}}
    )

    return redirect(url_for('main.view_cart'))


# ===============================
# DECREASE CART
# ===============================
@bp.route('/cart/decrease', methods=['POST'])
def cart_decrease():
    user = current_user()
    if not user:
        return redirect(url_for('auth.login'))

    item_id = request.form.get('item_id')

    cart = carts_col.find_one({'user_id': user['id']})

    if not cart:
        return redirect(url_for('main.view_cart'))

    new_items = []

    for item in cart['items']:
        if item['item_id'] == item_id:
            item['qty'] -= 1
            if item['qty'] > 0:
                new_items.append(item)
        else:
            new_items.append(item)

    carts_col.update_one(
        {'user_id': user['id']},
        {'$set': {'items': new_items}}
    )

    return redirect(url_for('main.view_cart'))


# ===============================
# CHECKOUT
# ===============================
@bp.route('/checkout')
def checkout():
    user = current_user()

    if not user:
        flash('Login required')
        return redirect(url_for('auth.login'))

    cart = carts_col.find_one({'user_id': user['id']})

    if not cart or not cart.get('items'):
        flash('Cart is empty')
        return redirect(url_for('main.menu'))

    checkout_details = []
    total = 0

    for c in cart['items']:
        item = items_col.find_one({'id': c['item_id']})
        if not item:
            continue

        subtotal = item['price'] * c['qty']
        total += subtotal

        checkout_details.append({
            'name': item['name'],
            'price': item['price'],
            'qty': c['qty'],
            'subtotal': subtotal
        })

    return render_template('checkout.html',
                           cart_details=checkout_details,
                           total=total,
                           user=user)


# ===============================
# PAY NOW
# ===============================
@bp.route('/pay_now', methods=['POST'])
def pay_now():
    user = current_user()

    if not user:
        return redirect(url_for('auth.login'))

    cart = carts_col.find_one({'user_id': user['id']})

    if not cart or not cart.get('items'):
        flash("Cart empty")
        return redirect(url_for('main.menu'))

    order_items = []
    total = 0

    for c in cart['items']:
        item = items_col.find_one({'id': c['item_id']})

        if not item:
            continue

        subtotal = item['price'] * c['qty']
        total += subtotal

        order_items.append({
            "name": item['name'],
            "qty": c['qty'],
            "price": item['price'],
            "subtotal": subtotal
        })

    order_id = str(uuid.uuid4())[:8].upper()

    last_order = orders_col.find_one(sort=[("token", -1)])
    token = (last_order['token'] + 1) if last_order else 1

    orders_col.insert_one({
        "id": order_id,
        "user_id": user['id'],
        "token": token,
        "user_name": user.get("name"),
        "items": order_items,
        "total": total,
        "status": "Preparing",
        "created_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S")


    })

    # Empty cart
    carts_col.update_one(
        {'user_id': user['id']},
        {'$set': {'items': []}}
    )

    # Generate invoice
    pdf_path = generate_invoice_pdf(
        order_id=order_id,
        user=user,
        order_items=order_items,
        total=total,
        token=token
    )

    # Store invoice path temporarily for this session
    session['invoice_path'] = pdf_path

    return render_template(
        'payment_success.html',
        order_id=order_id,
        token=token,
        total=total,
        user=user
    )
# ===============================
# DOWNLOAD INVOICE
# ===============================
@bp.route('/download_invoice')
def download_invoice():

    user = current_user()

    if not user:
        return redirect(url_for('auth.login'))

    pdf_path = session.get('invoice_path')

    if not pdf_path or not os.path.exists(pdf_path):
        flash("Invoice is no longer available")
        return redirect(url_for('main.menu'))

    return send_file(
        pdf_path,
        as_attachment=True,
        download_name=os.path.basename(pdf_path)
    )
# ===============================
# ORDER PROGRESS
# ===============================
@bp.route('/order_progress/<order_id>')
def order_progress(order_id):

    user = current_user()

    if not user:
        flash("Please login first")
        return redirect(url_for('auth.login'))

    # Find the order
    order = orders_col.find_one(
        {
            'id': order_id,
            'user_id': user['id']
        },
        {
            '_id': 0
        }
    )

    if not order:
        flash("Order not found")
        return redirect(url_for('main.menu'))

    # Make sure older orders don't break the template
    order.setdefault("items", [])
    order.setdefault("token", "N/A")
    order.setdefault("total", 0)
    order.setdefault("status", "Paid")
    order.setdefault("id", order_id)

    return render_template(
        'order_progress.html',
        order=order,
        user=user
    )
# ===============================
# UPDATE ORDER STATUS
# ===============================
@bp.route('/update_order_status/<order_id>/<status>', methods=['POST'])
def update_order_status(order_id, status):

    allowed_statuses = {
        "Preparing",
        "Ready for Collection",
        "Delivered"
    }

    if status not in allowed_statuses:
        flash("Invalid order status")
        return redirect(url_for('main.cafeteria'))

    order = orders_col.find_one({'id': order_id})

    if not order:
        flash("Order not found")
        return redirect(url_for('main.cafeteria'))

    # If the status is Delivered, delete the data instantly
    if status == "Delivered":
        orders_col.delete_one({'id': order_id})
        flash("Order marked as delivered and successfully removed from the system.")
    else:
        # Otherwise, just update the status
        orders_col.update_one(
            {'id': order_id},
            {'$set': {'status': status}}
        )
        flash(f"Order status updated to: {status}")

    return redirect(url_for('main.cafeteria'))
