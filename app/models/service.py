from datetime import datetime
from extensions import db


class ServiceCategory(db.Model):
    __tablename__ = "service_categories"

    id = db.Column(db.Integer, primary_key=True)
    slug = db.Column(db.String(80), unique=True, nullable=False, index=True)
    name_ne = db.Column(db.String(150), nullable=False)
    name_en = db.Column(db.String(150), nullable=False)
    description_ne = db.Column(db.Text)
    description_en = db.Column(db.Text)
    icon = db.Column(db.String(80))
    image_url = db.Column(db.Text)
    sort_order = db.Column(db.Integer, default=0)
    is_published = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    services = db.relationship("Service", back_populates="category", lazy="dynamic")

    def get_name(self, lang="ne"):
        return self.name_ne if lang == "ne" else self.name_en

    def get_description(self, lang="ne"):
        return self.description_ne if lang == "ne" else self.description_en


class Service(db.Model):
    __tablename__ = "services"

    id = db.Column(db.Integer, primary_key=True)
    category_id = db.Column(db.Integer, db.ForeignKey("service_categories.id"), nullable=False)
    slug = db.Column(db.String(120), unique=True, nullable=False, index=True)
    name_ne = db.Column(db.String(200), nullable=False)
    name_en = db.Column(db.String(200), nullable=False)
    short_desc_ne = db.Column(db.String(300))
    short_desc_en = db.Column(db.String(300))
    description_ne = db.Column(db.Text)
    description_en = db.Column(db.Text)
    requirements_ne = db.Column(db.Text)
    requirements_en = db.Column(db.Text)
    pricing_info_ne = db.Column(db.Text)
    pricing_info_en = db.Column(db.Text)
    price_npr = db.Column(db.Numeric(12, 2))  # optional fixed quote base price
    image_url = db.Column(db.String(500))
    is_featured = db.Column(db.Boolean, default=False)
    is_published = db.Column(db.Boolean, default=True)
    requires_documents = db.Column(db.Boolean, default=False)
    sort_order = db.Column(db.Integer, default=0)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    category = db.relationship("ServiceCategory", back_populates="services")
    bookings = db.relationship("Booking", back_populates="service", lazy="dynamic")

    def get_name(self, lang="ne"):
        return self.name_ne if lang == "ne" else self.name_en

    def get_short_desc(self, lang="ne"):
        return self.short_desc_ne if lang == "ne" else self.short_desc_en

    def get_description(self, lang="ne"):
        return self.description_ne if lang == "ne" else self.description_en

    def get_requirements(self, lang="ne"):
        return self.requirements_ne if lang == "ne" else self.requirements_en

    def get_pricing(self, lang="ne"):
        return self.pricing_info_ne if lang == "ne" else self.pricing_info_en
