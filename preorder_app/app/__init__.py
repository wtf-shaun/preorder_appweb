from flask import Flask
import os
from .db import db, initialize_order_token_counter


def create_app():

    # ===============================
    # PATH SETUP
    # ===============================
    base_dir = os.path.dirname(os.path.abspath(__file__))

    template_dir = os.path.abspath(os.path.join(base_dir, '..', 'templates'))
    static_dir = os.path.abspath(os.path.join(base_dir, '..', 'static'))

    app = Flask(
        __name__,
        template_folder=template_dir,
        static_folder=static_dir
    )

    # ===============================
    # SECRET KEY
    # ===============================
    app.config['SECRET_KEY'] = os.environ.get(
        'SECRET_KEY',
        'dev-secret'
    )

    # Attach DB to app
    app.db = db
    initialize_order_token_counter()

    # ===============================
    # CREATE DEFAULT ADMIN (ONLY ONCE)
    # ===============================
    from werkzeug.security import generate_password_hash

    if not db.users.find_one({"email": "admin@example.com"}):
        db.users.insert_one({
            "id": "admin-1",
            "name": "Admin",
            "email": "admin@example.com",
            "password_hash": generate_password_hash("admin123"),
            "is_admin": True
        })

    # ===============================
    # REGISTER BLUEPRINTS
    # ===============================
    from .routes import bp as main_bp
    from .auth import bp as auth_bp
    from .admin import bp as admin_bp

    app.register_blueprint(main_bp)
    app.register_blueprint(auth_bp, url_prefix='/auth')
    app.register_blueprint(admin_bp, url_prefix='/admin')

    return app
