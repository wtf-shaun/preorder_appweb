from flask import Blueprint, render_template, request, redirect, url_for, flash, session, send_file
from .db import (
    users_col, items_col, carts_col, orders_col, categories_col,
    get_user_by_id, get_all_items_for_menu, get_cart_by_user,
    get_all_categories, ensure_categories, get_item_by_id,
    get_orders_by_status,
    create_cart, update_cart, clear_cart, get_order_by_id,
    get_order_by_id_and_user, get_all_orders,
    next_order_token, create_order, record_item_order_events,
    update_order_status as save_order_status,
    archive_delivered_order, get_order_stamp_by_id_and_user
)
import uuid
from datetime import datetime, timezone
import os

bp = Blueprint('main', __name__)

# ===============================
# CAFETERIA
# ===============================
@bp.route('/cafeteria')
def cafeteria():
    user = current_user()
    if not user:
        flash('Please log in to continue.')
        return redirect(url_for('auth.login'))
    if user.get('is_admin') is not True:
        flash('You are not authorized to access the cafeteria dashboard.')
        return redirect(url_for('main.menu'))

    preparing_orders = get_orders_by_status('Preparing')
    ready_orders = get_orders_by_status('Ready for Collection')
    delivered_orders = get_orders_by_status('Delivered')
    return render_template(
        'cafeteria.html',
        preparing_orders=preparing_orders,
        ready_orders=ready_orders,
        delivered_orders=delivered_orders,
        user=user
    )

from flask import session, redirect, url_for, current_app, flash

# ===============================
# CURRENT USER
# ===============================
def current_user():
    uid = session.get('user_id')
    if not uid:
        return None
        
    # If it's a real user, look them up in the database normally
    return get_user_by_id(uid)
def get_cart_count():
    user = current_user()

    if not user:
        return 0

    cart = get_cart_by_user(user['id'])

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
    
# ===============================
# HOME
# ===============================
@bp.route('/healthz')
def healthz():
    return '', 204


@bp.route('/')
def index():
    return redirect(url_for('main.menu'))


# ===============================
# MENU
# ===============================
@bp.route('/menu')
def menu():
    items = get_all_items_for_menu()
    user = current_user()
    cart = get_cart_by_user(user['id']) if user else None
    defaults = [
        {'slug': 'food', 'name': 'Food'},
        {'slug': 'beverage', 'name': 'Beverages'}
    ]
    if not get_all_categories():
        ensure_categories(defaults)
    categories = get_all_categories()
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

    cart = get_cart_by_user(user['id'])

    if not cart or not cart.get('items'):
        return render_template('cart.html', cart_details=[], total=0, user=user)

    cart_details = []
    total = 0

    for c in cart['items']:
        item = get_item_by_id(c['item_id'])

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
    item = get_item_by_id(item_id)

    if not item:
        flash('Item not found')
        return redirect(url_for('main.menu'))

    cart = get_cart_by_user(user_id)

    if not cart:
        create_cart(user_id, [{'item_id': item_id, 'qty': quantity}])

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

        update_cart(user_id, cart['items'])

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

    cart = get_cart_by_user(user['id'])

    if not cart:
        return redirect(url_for('main.view_cart'))

    for item in cart['items']:
        if item['item_id'] == item_id:
            item['qty'] = min(20, int(item.get('qty', 1)) + 1)

    update_cart(user['id'], cart['items'])

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

    cart = get_cart_by_user(user['id'])

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

    update_cart(user['id'], new_items)

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

    cart = get_cart_by_user(user['id'])

    if not cart or not cart.get('items'):
        flash('Cart is empty')
        return redirect(url_for('main.menu'))

    checkout_details = []
    total = 0

    for c in cart['items']:
        item = get_item_by_id(c['item_id'])
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
        flash("Please login first")
        return redirect(url_for('auth.login'))

    cart = get_cart_by_user(user['id'])

    if not cart or not cart.get('items'):
        flash("Cart is empty")
        return redirect(url_for('main.menu'))

    order_items = []
    total = 0

    for c in cart['items']:
        item = get_item_by_id(c['item_id'])

        if not item:
            continue

        try:
            qty = int(c.get('qty', 0))
            price = float(item['price'])
        except (TypeError, ValueError):
            flash("Invalid item quantity or price")
            return redirect(url_for('main.view_cart'))

        if qty < 1 or qty > 20 or price < 0:
            flash("Invalid item quantity or price")
            return redirect(url_for('main.view_cart'))

        subtotal = price * qty
        total += subtotal

        order_items.append({
            "item_id": item['id'],
            "name": item['name'],
            "qty": qty,
            "price": price,
            "subtotal": subtotal
        })

    if not order_items:
        flash("No valid items found in cart")
        return redirect(url_for('main.menu'))

    order_id = str(uuid.uuid4())[:8].upper()
    token = next_order_token()
    ordered_at = datetime.now(timezone.utc)

    create_order({
        "id": order_id,
        "user_id": user['id'],
        "token": token,
        "user_name": user.get("name"),
        "items": order_items,
        "total": total,
        "status": "Preparing",
        "created_at": ordered_at.strftime("%Y-%m-%d %H:%M:%S"),
        "ordered_at": ordered_at
    })

    record_item_order_events(order_id, order_items, ordered_at)

    from .utils.pdf_invoice import generate_invoice_pdf

    pdf_path = generate_invoice_pdf(
        order_id=order_id,
        user=user,
        order_items=order_items,
        total=total,
        token=token
    )

    session['invoice_order_id'] = order_id

    clear_cart(user['id'])

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

    # Serverless instances may not retain temporary files between requests.
    # Regenerate the invoice from the persistent order record instead.
    order_id = session.get('invoice_order_id')
    if not order_id:
        flash("No recent invoice is available. Open your order progress page to access your order.")
        return redirect(url_for('main.menu'))

    order = (
        get_order_by_id_and_user(order_id, user['id'])
        or get_order_stamp_by_id_and_user(order_id, user['id'])
    )
    if not order:
        flash("Invoice order could not be found.")
        return redirect(url_for('main.menu'))

    from .utils.pdf_invoice import generate_invoice_pdf
    pdf_path = generate_invoice_pdf(
        order_id=order.get('id', order_id),
        user=user,
        order_items=order.get('items', []),
        total=order.get('total', 0),
        token=order.get('token')
    )

    return send_file(
        pdf_path,
        as_attachment=True,
        download_name=f"invoice_{order_id}.pdf",
        mimetype="application/pdf"
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
    order = (
        get_order_by_id_and_user(order_id, user['id'])
        or get_order_stamp_by_id_and_user(order_id, user['id'])
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
    user = current_user()
    if not user:
        flash('Please log in to continue.')
        return redirect(url_for('auth.login'))
    if user.get('is_admin') is not True:
        flash('You are not authorized to update order statuses.')
        return redirect(url_for('main.menu'))

    allowed_statuses = {
        "Preparing",
        "Ready for Collection",
        "Delivered"
    }

    if status not in allowed_statuses:
        flash("Invalid order status")
        return redirect(url_for('main.cafeteria'))

    order = get_order_by_id(order_id)

    if not order:
        flash("Order not found")
        return redirect(url_for('main.cafeteria'))

    if status == 'Delivered':
        delivered_at = datetime.now(timezone.utc)
        order = archive_delivered_order(order_id, delivered_at)
        if not order:
            flash("Order could not be archived")
            return redirect(url_for('main.cafeteria'))
    else:
        save_order_status(order_id, status)
    flash(f"Order status updated to: {status}")
    return redirect(url_for('main.cafeteria'))
