from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import UserMixin
from extensions import db, login_manager


class Admin(UserMixin, db.Model):
    __tablename__ = "admins"

    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(256), nullable=False)
    full_name = db.Column(db.String(120), nullable=False)
    role = db.Column(db.String(50), default="admin")  # admin, superadmin
    is_active = db.Column(db.Boolean, default=True)
    last_login = db.Column(db.DateTime)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def get_id(self):
        return f"a:{self.id}"

    def set_password(self, password: str):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password: str) -> bool:
        return check_password_hash(self.password_hash, password)

    def __repr__(self):
        return f"<Admin {self.email}>"


@login_manager.user_loader
def load_user(user_id):
    try:
        if isinstance(user_id, str) and user_id.startswith("a:"):
            return Admin.query.get(int(user_id[2:]))
        if isinstance(user_id, str) and user_id.startswith("c:"):
            from app.models.customer import Customer
            return Customer.query.get(int(user_id[2:]))
        # legacy admin sessions without prefix
        return Admin.query.get(int(user_id))
    except Exception:
        return None
