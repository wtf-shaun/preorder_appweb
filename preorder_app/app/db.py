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
