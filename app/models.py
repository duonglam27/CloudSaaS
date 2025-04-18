from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime
import re
import ipaddress

from app import db

class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(128), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    domains = db.relationship('Domain', backref='owner', lazy='dynamic')

    def set_password(self, password):
        """Hash and store the password."""
        if not password:
            raise ValueError("Password cannot be empty.")
        self.password_hash = generate_password_hash(password, method='pbkdf2:sha256')

    def check_password(self, password):
        """Check if the provided password matches the stored hash."""
        if not password:
            return False
        return check_password_hash(self.password_hash, password)

    def get_domains(self):
        """Return all domains associated with the user."""
        return self.domains.order_by(Domain.domain_name).all()

    @staticmethod
    def validate_email(email):
        """Validate email format."""
        email_regex = r'^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$'
        return re.match(email_regex, email) is not None

    def __repr__(self):
        return f"<User {self.email}>"

class Domain(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    domain_name = db.Column(db.String(120), unique=True, nullable=False, index=True)
    backend_ip = db.Column(db.String(50), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    @staticmethod
    def validate_ip(ip_address):
        """Validate IP address format and range."""
        try:
            ipaddress.ip_address(ip_address)
            return True
        except ValueError:
            return False

    @staticmethod
    def validate_domain_name(domain_name):
        """Validate domain name format."""
        domain_regex = r'^(?!-)[A-Za-z0-9-]{1,63}(?<!-)\.(?!-)[A-Za-z0-9-]{1,63}(?<!-)$'
        return re.match(domain_regex, domain_name) is not None

    def __repr__(self):
        return f"<Domain {self.domain_name} - Backend IP: {self.backend_ip}>"