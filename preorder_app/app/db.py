# app/db.py

import os
from pymongo import MongoClient

MONGO_URI = os.environ.get("MONGO_URI")
DB_NAME = os.environ.get("DB_NAME", "cafeteria_app")

if not MONGO_URI:
    raise RuntimeError("MONGO_URI not set in environment variables")

client = MongoClient(MONGO_URI)
db = client[DB_NAME]

# Collections
users_col = db["users"]
items_col = db["items"]
carts_col = db["carts"]
orders_col = db["orders"]
categories_col = db["categories"]


# ===============================
# USER QUERIES
# ===============================
def get_user_by_id(user_id):
    """Get a single user by ID."""
    return users_col.find_one({'id': user_id})


def get_user_by_email(email):
    """Get a single user by email."""
    return users_col.find_one({'email': email})


def get_all_users():
    """Get all users."""
    return list(users_col.find({}, {'_id': 0}))


def create_user(user_data):
    """Insert a new user."""
    return users_col.insert_one(user_data)


def update_user(user_id, update_data):
    """Update user by ID."""
    return users_col.update_one({'id': user_id}, {'$set': update_data})


def delete_user(user_id):
    """Delete user by ID."""
    return users_col.delete_one({'id': user_id})


# ===============================
# ITEM QUERIES
# ===============================
def get_item_by_id(item_id):
    """Get a single item by ID."""
    return items_col.find_one({'id': item_id})


def get_all_items():
    """Get all items."""
    return list(items_col.find({}, {'_id': 0}))


def get_items_by_category(category):
    """Get all items in a category."""
    return list(items_col.find({'category': category}, {'_id': 0}))


def create_item(item_data):
    """Insert a new item."""
    return items_col.insert_one(item_data)


def update_item(item_id, update_data):
    """Update item by ID."""
    return items_col.update_one({'id': item_id}, {'$set': update_data})


def delete_item(item_id):
    """Delete item by ID."""
    return items_col.delete_one({'id': item_id})


# ===============================
# CART QUERIES
# ===============================
def get_cart_by_user(user_id):
    """Get cart for a user."""
    return carts_col.find_one({'user_id': user_id})


def create_cart(user_id, items):
    """Create a new cart."""
    return carts_col.insert_one({
        'user_id': user_id,
        'items': items
    })


def update_cart(user_id, items):
    """Update cart items for a user."""
    return carts_col.update_one(
        {'user_id': user_id},
        {'$set': {'items': items}},
        upsert=True
    )


def clear_cart(user_id):
    """Clear all items from a user's cart."""
    return carts_col.update_one(
        {'user_id': user_id},
        {'$set': {'items': []}}
    )


# ===============================
# ORDER QUERIES
# ===============================
def get_order_by_id(order_id):
    """Get a single order by ID."""
    return orders_col.find_one({'id': order_id}, {'_id': 0})


def get_order_by_id_and_user(order_id, user_id):
    """Get an order by ID and user ID."""
    return orders_col.find_one(
        {'id': order_id, 'user_id': user_id},
        {'_id': 0}
    )


def get_all_orders():
    """Get all orders."""
    return list(orders_col.find({}, {'_id': 0}))


def get_orders_by_user(user_id):
    """Get all orders for a specific user."""
    return list(orders_col.find({'user_id': user_id}, {'_id': 0}))


def create_order(order_data):
    """Insert a new order."""
    return orders_col.insert_one(order_data)


def update_order_status(order_id, status):
    """Update order status."""
    return orders_col.update_one(
        {'id': order_id},
        {'$set': {'status': status}}
    )


def delete_order(order_id):
    """Delete order by ID."""
    return orders_col.delete_one({'id': order_id})


def get_last_order():
    """Get the last order (by token)."""
    return orders_col.find_one(sort=[("token", -1)])


# ===============================
# CATEGORY QUERIES
# ===============================
def get_category_by_slug(slug):
    """Get a category by slug."""
    return categories_col.find_one({'slug': slug})


def get_all_categories():
    """Get all categories sorted by name."""
    return list(categories_col.find({}, {'_id': 0}).sort('name', 1))


def create_category(category_data):
    """Insert a new category."""
    return categories_col.insert_one(category_data)


def upsert_category(slug, category_data):
    """Create category if it doesn't exist."""
    return categories_col.update_one(
        {'slug': slug},
        {'$setOnInsert': category_data},
        upsert=True
    )


def delete_category(slug):
    """Delete category by slug."""
    return categories_col.delete_one({'slug': slug})
