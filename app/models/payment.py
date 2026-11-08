from datetime import datetime
from extensions import db


class PaymentMethod(db.Model):
    __tablename__ = "payment_methods"

    id = db.Column(db.Integer, primary_key=True)
    code = db.Column(db.String(30), unique=True, nullable=False)  # esewa, khalti, fonepay, bank, qr, cash
    name_ne = db.Column(db.String(80), nullable=False)
    name_en = db.Column(db.String(80), nullable=False)
    logo_url = db.Column(db.Text)
    external_url = db.Column(db.String(300))  # official site
    instructions_ne = db.Column(db.Text)
    instructions_en = db.Column(db.Text)
    qr_image_url = db.Column(db.Text)
    is_enabled = db.Column(db.Boolean, default=True)
    sort_order = db.Column(db.Integer, default=0)
    is_gateway = db.Column(db.Boolean, default=False)  # True only if real API integrated
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def get_name(self, lang="ne"):
        return self.name_ne if lang == "ne" else self.name_en

    def get_instructions(self, lang="ne"):
        return self.instructions_ne if lang == "ne" else self.instructions_en


class Quotation(db.Model):
    __tablename__ = "quotations"

    id = db.Column(db.Integer, primary_key=True)
    booking_id = db.Column(db.Integer, db.ForeignKey("bookings.id"), nullable=False)
    amount = db.Column(db.Numeric(12, 2), nullable=False)
    currency = db.Column(db.String(10), default="NPR")
    description_ne = db.Column(db.Text)
    description_en = db.Column(db.Text)
    valid_until = db.Column(db.DateTime)
    is_active = db.Column(db.Boolean, default=True)
    created_by_id = db.Column(db.Integer, db.ForeignKey("admins.id"))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    booking = db.relationship("Booking", back_populates="quotations")
    created_by = db.relationship("Admin")


class Payment(db.Model):
    __tablename__ = "payments"

    id = db.Column(db.Integer, primary_key=True)
    booking_id = db.Column(db.Integer, db.ForeignKey("bookings.id"), nullable=False, index=True)
    payment_method_id = db.Column(db.Integer, db.ForeignKey("payment_methods.id"))
    amount = db.Column(db.Numeric(12, 2), nullable=False)
    currency = db.Column(db.String(10), default="NPR")
    transaction_id = db.Column(db.String(120), index=True)
    status = db.Column(db.String(30), default="pending")  # pending, submitted, verified, failed, refunded
    receipt_url = db.Column(db.Text)
    notes = db.Column(db.Text)
    verified_by_id = db.Column(db.Integer, db.ForeignKey("admins.id"), nullable=True)
    verified_at = db.Column(db.DateTime)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    booking = db.relationship("Booking", back_populates="payments")
    payment_method = db.relationship("PaymentMethod")
    verified_by = db.relationship("Admin")
