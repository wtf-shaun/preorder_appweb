# app/db.py

import os
from pymongo import MongoClient, ReturnDocument

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
counters_col = db["counters"]


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


def ensure_categories(categories):
    """Insert default categories without replacing existing values."""
    for category in categories:
        categories_col.update_one(
            {'slug': category['slug']},
            {'$setOnInsert': category},
            upsert=True
        )


def get_all_items_for_menu():
    """Get menu items with a category fallback for older records."""
    items = list(items_col.find({}, {'_id': 0}))
    for item in items:
        item.setdefault('category', 'food')
    return items


def get_all_orders_for_admin():
    """Get all orders without MongoDB's internal identifier."""
    return list(orders_col.find({}, {'_id': 0}))


def get_monthly_item_popularity():
    """Aggregate ordered quantities by month and item in MongoDB."""
    pipeline = [
        {
            '$match': {
                '$or': [
                    {'ordered_at': {'$type': 'date'}},
                    {'created_at': {'$type': 'string'}}
                ]
            }
        },
        {
            '$set': {
                'analytics_date': {
                    '$cond': [
                        {'$eq': [{'$type': '$ordered_at'}, 'date']},
                        '$ordered_at',
                        {
                            '$dateFromString': {
                                'dateString': '$created_at',
                                'format': '%Y-%m-%d %H:%M:%S',
                                'timezone': 'UTC',
                                'onError': None,
                                'onNull': None
                            }
                        }
                    ]
                }
            }
        },
        {'$match': {'analytics_date': {'$type': 'date'}}},
        {'$unwind': '$items'},
        {
            '$group': {
                '_id': {
                    'month': {
                        '$dateToString': {
                            'format': '%Y-%m',
                            'date': '$analytics_date',
                            'timezone': 'UTC'
                        }
                    },
                    'item_id': {
                        '$ifNull': ['$items.item_id', '$items.name']
                    },
                    'item_name': '$items.name'
                },
                'quantity': {'$sum': '$items.qty'}
            }
        },
        {'$sort': {'_id.month': 1, '_id.item_name': 1}},
    ]

    monthly = {}
    item_names = {}
    for row in orders_col.aggregate(pipeline):
        month = row['_id']['month']
        item_id = row['_id']['item_id']
        monthly.setdefault(month, {})[item_id] = row['quantity']
        item_names[item_id] = row['_id']['item_name']

    months = sorted(monthly)
    items = sorted(item_names, key=lambda item_id: item_names[item_id].lower())
    return {
        'months': months,
        'datasets': [
            {
                'label': item_names[item_id],
                'data': [monthly[month].get(item_id, 0) for month in months]
            }
            for item_id in items
        ]
    }


def next_order_token():
    """Atomically allocate the next order token in MongoDB."""
    counter = counters_col.find_one_and_update(
        {'_id': 'order_token'},
        {'$inc': {'value': 1}},
        upsert=True,
        return_document=ReturnDocument.AFTER,
        projection={'value': 1}
    )
    return counter['value']


def initialize_order_token_counter():
    """Seed the counter from existing orders without lowering its value."""
    last_order = orders_col.find_one(sort=[('token', -1)])
    current_value = last_order.get('token', 0) if last_order else 0
    counters_col.update_one(
        {'_id': 'order_token'},
        {'$max': {'value': current_value}},
        upsert=True
    )


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
