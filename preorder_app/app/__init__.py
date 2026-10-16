from flask import Flask
import os
from .db import db


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
    secret_key = os.environ.get('SECRET_KEY')
    if not secret_key:
        raise RuntimeError(
            'SECRET_KEY must be set in the environment. '
            'Generate a long random value and configure it in your deployment settings.'
        )
    app.config['SECRET_KEY'] = secret_key
    app.config.update(
        SESSION_COOKIE_HTTPONLY=True,
        SESSION_COOKIE_SAMESITE='Lax',
        SESSION_COOKIE_SECURE=os.environ.get('COOKIE_SECURE', 'true').lower() == 'true'
    )

    # Attach DB to app
    app.db = db

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
