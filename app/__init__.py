from flask import Flask, redirect, url_for, render_template
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
import logging
from logging.handlers import RotatingFileHandler

# Initialize extensions
db = SQLAlchemy()
login_manager = LoginManager()

def create_app():
    # Create Flask app
    app = Flask(__name__)
    app.config.from_object('config.Config')

    # Initialize extensions
    db.init_app(app)
    login_manager.init_app(app)

    # Configure LoginManager
    login_manager.login_view = "auth.login"
    login_manager.login_message = "Vui lòng đăng nhập để truy cập trang này."
    login_manager.login_message_category = "info"

    # Configure logging
    handler = RotatingFileHandler('app.log', maxBytes=100000, backupCount=3)
    handler.setLevel(logging.INFO)
    app.logger.addHandler(handler)

    # Register user_loader
    @login_manager.user_loader
    def load_user(user_id):
        from app.models import User  # Avoid circular imports
        try:
            return User.query.get(int(user_id))
        except Exception as e:
            app.logger.error(f"Error loading user with ID {user_id}: {e}")
            return None

    # Register Blueprints
    from app.views.auth import auth_bp
    from app.views.dashboard import dashboard_bp
    from app.views.domains import domains_bp
    app.register_blueprint(auth_bp, url_prefix='/auth')
    app.register_blueprint(dashboard_bp, url_prefix='/dashboard')
    app.register_blueprint(domains_bp, url_prefix='/domains')

    # Default route
    @app.route('/')
    def index():
        from flask_login import current_user
        if current_user.is_authenticated:
            return redirect(url_for('dashboard.index'))
        return redirect(url_for('auth.login'))

    # Error handlers
    @app.errorhandler(404)
    def not_found_error(error):
        return render_template('404.html'), 404

    @app.errorhandler(500)
    def internal_error(error):
        db.session.rollback()
        return render_template('500.html'), 500

    return app