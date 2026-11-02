from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import UserMixin
from extensions import db


class Customer(UserMixin, db.Model):
    __tablename__ = "customers"

    id = db.Column(db.Integer, primary_key=True)
    full_name = db.Column(db.String(150), nullable=False)
    email = db.Column(db.String(120), index=True, unique=True)
    mobile = db.Column(db.String(20), nullable=True, index=True)
    password_hash = db.Column(db.String(255))
    google_id = db.Column(db.String(120), index=True, unique=True)
    facebook_id = db.Column(db.String(120), index=True, unique=True)
    nationality = db.Column(db.String(80))
    preferred_lang = db.Column(db.String(5), default="ne")
    notes = db.Column(db.Text)
    is_active = db.Column(db.Boolean, default=True)
    email_notify = db.Column(db.Boolean, default=True)  # announcement emails
    avatar_url = db.Column(db.Text)
    reset_token = db.Column(db.String(64), index=True)
    reset_token_expires = db.Column(db.DateTime)
    push_subscription = db.Column(db.Text)  # JSON PushSubscription
    push_enabled = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    last_login = db.Column(db.DateTime)
    last_ip = db.Column(db.String(64))
    last_user_agent = db.Column(db.String(300))
    last_lat = db.Column(db.Float)
    last_lng = db.Column(db.Float)
    last_location_label = db.Column(db.String(250))  # e.g. Urlabari, Morang, NP

    bookings = db.relationship("Booking", back_populates="customer", lazy="dynamic")

    def set_password(self, password: str):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password: str) -> bool:
        if not self.password_hash:
            return False
        return check_password_hash(self.password_hash, password)

    def get_id(self):
        # Prefix so Admin and Customer share LoginManager
        return f"c:{self.id}"

    def __repr__(self):
        return f"<Customer {self.full_name} ({self.email})>"
