from datetime import datetime
from extensions import db


class ContactMessage(db.Model):
    __tablename__ = "contact_messages"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False)
    email = db.Column(db.String(120))
    mobile = db.Column(db.String(20))
    subject = db.Column(db.String(200))
    message = db.Column(db.Text, nullable=False)
    is_read = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)


class Notification(db.Model):
    __tablename__ = "notifications"

    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    body = db.Column(db.Text)
    link = db.Column(db.String(300))
    is_read = db.Column(db.Boolean, default=False)
    admin_id = db.Column(db.Integer, db.ForeignKey("admins.id"), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)


class EmailSetting(db.Model):
    __tablename__ = "email_settings"

    id = db.Column(db.Integer, primary_key=True)
    provider = db.Column(db.String(50), default="gmail")
    host = db.Column(db.String(120), default="smtp.gmail.com")
    port = db.Column(db.Integer, default=587)
    use_tls = db.Column(db.Boolean, default=True)
    use_ssl = db.Column(db.Boolean, default=False)
    username = db.Column(db.String(120))
    # Store encrypted in production; plain for demo with warning
    password_encrypted = db.Column(db.Text)
    sender_name = db.Column(db.String(120), default="SR All Service Hub Nepal")
    sender_email = db.Column(db.String(120))
    reply_to = db.Column(db.String(120))
    is_active = db.Column(db.Boolean, default=True)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class EmailTemplate(db.Model):
    __tablename__ = "email_templates"

    id = db.Column(db.Integer, primary_key=True)
    key = db.Column(db.String(80), unique=True, nullable=False)  # booking_received, etc.
    subject_ne = db.Column(db.String(200))
    subject_en = db.Column(db.String(200))
    body_ne = db.Column(db.Text)
    body_en = db.Column(db.Text)
    is_enabled = db.Column(db.Boolean, default=True)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class EmailLog(db.Model):
    __tablename__ = "email_logs"

    id = db.Column(db.Integer, primary_key=True)
    template_key = db.Column(db.String(80))
    to_email = db.Column(db.String(120), nullable=False)
    subject = db.Column(db.String(200))
    status = db.Column(db.String(30), default="pending")  # pending, sent, failed
    error_message = db.Column(db.Text)
    retry_count = db.Column(db.Integer, default=0)
    booking_id = db.Column(db.Integer, db.ForeignKey("bookings.id"), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    sent_at = db.Column(db.DateTime)
