# app/db.py

import os
import logging
import random
import uuid
from datetime import datetime, timedelta, timezone
from pymongo import MongoClient, ReturnDocument, UpdateOne
from pymongo.errors import PyMongoError

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
item_order_events_col = db["item_order_events"]


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


def record_item_order_events(order_id, order_items, ordered_at, demo_data=False):
    """Persist item order history independently from deletable orders."""
    events = [
        {
            'event_id': f'{order_id}:{index}',
            'order_id': order_id,
            'item_id': item.get('item_id') or item.get('name'),
            'item_name': item.get('name') or 'Unknown item',
            'quantity': item.get('qty', 0),
            'unit_price': item.get('price', 0),
            'revenue': item.get('subtotal', 0),
            'ordered_at': ordered_at,
            'demo_data': demo_data
        }
        for index, item in enumerate(order_items)
    ]
    if events:
        item_order_events_col.bulk_write([
            UpdateOne(
                {'event_id': event['event_id']},
                {'$setOnInsert': event},
                upsert=True
            )
            for event in events
        ])


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
        {'$match': {'ordered_at': {'$type': 'date'}}},
        {
            '$group': {
                '_id': {
                    'month': {
                        '$dateToString': {
                            'format': '%Y-%m',
                            'date': '$ordered_at',
                            'timezone': 'UTC'
                        }
                    },
                    'item_id': '$item_id',
                    'item_name': '$item_name'
                },
                'quantity': {'$sum': '$quantity'}
            }
        },
        {'$sort': {'_id.month': 1, '_id.item_name': 1}},
    ]

    monthly = {}
    item_names = {}
    try:
        rows = item_order_events_col.aggregate(pipeline)
        for row in rows:
            month = row['_id']['month']
            item_name = row['_id'].get('item_name') or 'Unknown item'
            item_id = row['_id'].get('item_id') or item_name
            monthly.setdefault(month, {})[item_id] = row['quantity']
            item_names[item_id] = item_name
    except PyMongoError:
        logging.getLogger(__name__).exception(
            'Monthly item popularity aggregation failed'
        )
        return {'months': [], 'datasets': []}

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


def get_monthly_revenue():
    """Aggregate revenue and order count by month in MongoDB."""
    pipeline = [
        {'$match': {'ordered_at': {'$type': 'date'}}},
        {
            '$group': {
                '_id': {
                    '$dateToString': {
                        'format': '%Y-%m',
                        'date': '$ordered_at',
                        'timezone': 'UTC'
                    }
                },
                'revenue': {'$sum': '$revenue'},
                'orders': {'$addToSet': '$order_id'}
            }
        },
        {'$sort': {'_id': 1}}
    ]

    try:
        rows = item_order_events_col.aggregate(pipeline)
        return [
            {
                'month': row['_id'],
                'revenue': row['revenue'],
                'orders': len(row['orders'])
            }
            for row in rows
        ]
    except PyMongoError:
        logging.getLogger(__name__).exception(
            'Monthly revenue aggregation failed'
        )
        return []


def get_item_revenue_rankings():
    """Rank every menu item by its contribution to total order revenue."""
    pipeline = [
        {'$match': {'ordered_at': {'$type': 'date'}}},
        {
            '$group': {
                '_id': {
                    'item_id': '$item_id',
                    'item_name': '$item_name'
                },
                'revenue': {'$sum': '$revenue'},
                'quantity': {'$sum': '$quantity'},
                'orders': {'$addToSet': '$order_id'}
            }
        },
        {'$sort': {'revenue': -1, '_id.item_name': 1}}
    ]

    try:
        totals = list(item_order_events_col.aggregate(pipeline))
        menu_items = list(items_col.find({}, {'_id': 0, 'id': 1, 'name': 1}))
    except PyMongoError:
        logging.getLogger(__name__).exception('Item revenue ranking failed')
        return []

    ranked = {}
    for row in totals:
        item_id = row['_id'].get('item_id') or row['_id'].get('item_name')
        ranked[item_id] = {
            'name': row['_id'].get('item_name') or 'Unknown item',
            'revenue': row['revenue'],
            'quantity': row['quantity'],
            'orders': len(row['orders'])
        }

    for item in menu_items:
        ranked.setdefault(item['id'], {
            'name': item['name'],
            'revenue': 0,
            'quantity': 0,
            'orders': 0
        })

    total_revenue = sum(item['revenue'] for item in ranked.values())
    result = sorted(
        ranked.values(),
        key=lambda item: (-item['revenue'], item['name'].lower())
    )
    return [
        {
            'rank': index,
            'name': item['name'],
            'quantity': item['quantity'],
            'orders': item['orders'],
            'revenue': item['revenue'],
            'percentage': (
                item['revenue'] / total_revenue * 100
                if total_revenue else 0
            )
        }
        for index, item in enumerate(result, start=1)
    ]


def seed_demo_statistics(order_count=300):
    """Create clearly marked demo orders for testing the statistics charts."""
    menu_items = list(items_col.find({}, {'_id': 0}))
    if not menu_items:
        menu_items = [
            {'id': 'demo-sandwich', 'name': 'Demo Sandwich', 'price': 80},
            {'id': 'demo-coffee', 'name': 'Demo Coffee', 'price': 50},
            {'id': 'demo-wrap', 'name': 'Demo Wrap', 'price': 100},
        ]

    now = datetime.now(timezone.utc)
    demo_orders = []
    for index in range(order_count):
        ordered_at = now - timedelta(days=random.randint(0, 364))
        order_items = []
        total = 0
        for item in random.sample(menu_items, min(random.randint(1, 3), len(menu_items))):
            quantity = random.randint(1, 5)
            price = item.get('price', 0)
            subtotal = price * quantity
            total += subtotal
            order_items.append({
                'item_id': item.get('id', item['name']),
                'name': item['name'],
                'qty': quantity,
                'price': price,
                'subtotal': subtotal
            })

        demo_orders.append({
            'id': f'demo-{uuid.uuid4().hex[:10]}',
            'user_id': 'demo-analytics',
            'user_name': 'Demo Analytics',
            'token': 900000 + index,
            'items': order_items,
            'total': total,
            'status': 'Delivered',
            'demo_data': True,
            'created_at': ordered_at.strftime('%Y-%m-%d %H:%M:%S'),
            'ordered_at': ordered_at
        })

    if demo_orders:
        orders_col.insert_many(demo_orders)
        for order in demo_orders:
            record_item_order_events(
                order['id'],
                order['items'],
                order['ordered_at'],
                demo_data=True
            )
    return len(demo_orders)


def clear_demo_statistics():
    """Delete only orders created by the demo statistics action."""
    item_order_events_col.delete_many({'demo_data': True})
    return orders_col.delete_many({'demo_data': True})


def backfill_item_order_events():
    """Copy existing orders into the ledger without creating duplicates."""
    for order in orders_col.find({}):
        ordered_at = order.get('ordered_at')
        if not ordered_at and order.get('created_at'):
            try:
                ordered_at = datetime.strptime(
                    order['created_at'], '%Y-%m-%d %H:%M:%S'
                ).replace(tzinfo=timezone.utc)
            except (TypeError, ValueError):
                continue
        if ordered_at:
            record_item_order_events(
                order['id'],
                order.get('items', []),
                ordered_at,
                demo_data=order.get('demo_data', False)
            )


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


def update_category(slug, update_data):
    """Update a category by slug."""
    return categories_col.update_one({'slug': slug}, {'$set': update_data})


def delete_category(slug):
    """Delete category by slug."""
    return categories_col.delete_one({'slug': slug})
