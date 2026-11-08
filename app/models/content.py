from datetime import datetime
from extensions import db


class Page(db.Model):
    __tablename__ = "pages"

    id = db.Column(db.Integer, primary_key=True)
    slug = db.Column(db.String(120), unique=True, nullable=False, index=True)
    title_ne = db.Column(db.String(200), nullable=False)
    title_en = db.Column(db.String(200), nullable=False)
    content_ne = db.Column(db.Text)
    content_en = db.Column(db.Text)
    meta_title_ne = db.Column(db.String(200))
    meta_title_en = db.Column(db.String(200))
    meta_description_ne = db.Column(db.String(300))
    meta_description_en = db.Column(db.String(300))
    is_published = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def get_title(self, lang="ne"):
        return self.title_ne if lang == "ne" else self.title_en

    def get_content(self, lang="ne"):
        return self.content_ne if lang == "ne" else self.content_en


class HomepageSection(db.Model):
    __tablename__ = "homepage_sections"

    id = db.Column(db.Integer, primary_key=True)
    key = db.Column(db.String(80), unique=True, nullable=False)  # hero, destinations, packages, etc.
    title_ne = db.Column(db.String(200))
    title_en = db.Column(db.String(200))
    subtitle_ne = db.Column(db.Text)
    subtitle_en = db.Column(db.Text)
    content_ne = db.Column(db.Text)
    content_en = db.Column(db.Text)
    image_url = db.Column(db.Text)
    cta_text_ne = db.Column(db.String(100))
    cta_text_en = db.Column(db.String(100))
    cta_url = db.Column(db.String(300))
    is_enabled = db.Column(db.Boolean, default=True)
    sort_order = db.Column(db.Integer, default=0)
    extra_data = db.Column(db.JSON, default=dict)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class NavigationItem(db.Model):
    __tablename__ = "navigation_items"

    id = db.Column(db.Integer, primary_key=True)
    label_ne = db.Column(db.String(100), nullable=False)
    label_en = db.Column(db.String(100), nullable=False)
    url = db.Column(db.String(300), nullable=False)
    parent_id = db.Column(db.Integer, db.ForeignKey("navigation_items.id"), nullable=True)
    sort_order = db.Column(db.Integer, default=0)
    is_published = db.Column(db.Boolean, default=True)
    location = db.Column(db.String(30), default="header")  # header, footer

    children = db.relationship("NavigationItem", backref=db.backref("parent", remote_side=[id]))


class FAQ(db.Model):
    __tablename__ = "faqs"

    id = db.Column(db.Integer, primary_key=True)
    question_ne = db.Column(db.String(300), nullable=False)
    question_en = db.Column(db.String(300), nullable=False)
    answer_ne = db.Column(db.Text, nullable=False)
    answer_en = db.Column(db.Text, nullable=False)
    category = db.Column(db.String(80))
    sort_order = db.Column(db.Integer, default=0)
    is_published = db.Column(db.Boolean, default=True)
    is_featured = db.Column(db.Boolean, default=False)


class Destination(db.Model):
    __tablename__ = "destinations"

    id = db.Column(db.Integer, primary_key=True)
    slug = db.Column(db.String(120), unique=True, nullable=False)
    name_ne = db.Column(db.String(150), nullable=False)
    name_en = db.Column(db.String(150), nullable=False)
    description_ne = db.Column(db.Text)
    description_en = db.Column(db.Text)
    image_url = db.Column(db.Text)
    country = db.Column(db.String(80))
    is_featured = db.Column(db.Boolean, default=False)
    is_published = db.Column(db.Boolean, default=True)
    sort_order = db.Column(db.Integer, default=0)


class Package(db.Model):
    __tablename__ = "packages"

    id = db.Column(db.Integer, primary_key=True)
    slug = db.Column(db.String(120), unique=True, nullable=False)
    title_ne = db.Column(db.String(200), nullable=False)
    title_en = db.Column(db.String(200), nullable=False)
    short_desc_ne = db.Column(db.String(300))
    short_desc_en = db.Column(db.String(300))
    description_ne = db.Column(db.Text)
    description_en = db.Column(db.Text)
    price_from = db.Column(db.Numeric(12, 2))
    min_payment = db.Column(db.Numeric(12, 2))  # minimum advance payment
    currency = db.Column(db.String(10), default="NPR")
    duration_days = db.Column(db.Integer)
    image_url = db.Column(db.Text)
    destination_id = db.Column(db.Integer, db.ForeignKey("destinations.id"), nullable=True)
    is_featured = db.Column(db.Boolean, default=False)
    is_published = db.Column(db.Boolean, default=True)
    sort_order = db.Column(db.Integer, default=0)

    destination = db.relationship("Destination")
    itineraries = db.relationship("PackageItinerary", back_populates="package", cascade="all, delete-orphan")


class PackageItinerary(db.Model):
    __tablename__ = "package_itineraries"

    id = db.Column(db.Integer, primary_key=True)
    package_id = db.Column(db.Integer, db.ForeignKey("packages.id"), nullable=False)
    day_number = db.Column(db.Integer, nullable=False)
    title_ne = db.Column(db.String(200))
    title_en = db.Column(db.String(200))
    description_ne = db.Column(db.Text)
    description_en = db.Column(db.Text)

    package = db.relationship("Package", back_populates="itineraries")


class Offer(db.Model):
    __tablename__ = "offers"

    id = db.Column(db.Integer, primary_key=True)
    title_ne = db.Column(db.String(200), nullable=False)
    title_en = db.Column(db.String(200), nullable=False)
    description_ne = db.Column(db.Text)
    description_en = db.Column(db.Text)
    image_url = db.Column(db.Text)
    discount_label = db.Column(db.String(50))
    valid_from = db.Column(db.DateTime)
    valid_until = db.Column(db.DateTime)
    is_published = db.Column(db.Boolean, default=True)
    sort_order = db.Column(db.Integer, default=0)


class Gallery(db.Model):
    __tablename__ = "galleries"

    id = db.Column(db.Integer, primary_key=True)
    title_ne = db.Column(db.String(200))
    title_en = db.Column(db.String(200))
    image_url = db.Column(db.String(500), nullable=False)
    category = db.Column(db.String(80))
    sort_order = db.Column(db.Integer, default=0)
    is_published = db.Column(db.Boolean, default=True)


class Testimonial(db.Model):
    __tablename__ = "testimonials"

    id = db.Column(db.Integer, primary_key=True)
    customer_name = db.Column(db.String(120), nullable=False)
    content_ne = db.Column(db.Text)
    content_en = db.Column(db.Text)
    rating = db.Column(db.Integer, default=5)
    location = db.Column(db.String(100))
    image_url = db.Column(db.Text)
    mobile = db.Column(db.String(30))  # show for logged-in user reviews
    customer_id = db.Column(db.Integer, db.ForeignKey("customers.id"), nullable=True, index=True)
    is_published = db.Column(db.Boolean, default=True)
    sort_order = db.Column(db.Integer, default=0)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    customer = db.relationship("Customer", foreign_keys=[customer_id])


class NewsletterSubscriber(db.Model):
    __tablename__ = "newsletter_subscribers"

    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), unique=True, nullable=False, index=True)
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)


class Branch(db.Model):
    __tablename__ = "branches"

    id = db.Column(db.Integer, primary_key=True)
    name_ne = db.Column(db.String(150), nullable=False)
    name_en = db.Column(db.String(150), nullable=False)
    address_ne = db.Column(db.Text)
    address_en = db.Column(db.Text)
    phone = db.Column(db.String(50))
    email = db.Column(db.String(120))
    whatsapp = db.Column(db.String(30))
    latitude = db.Column(db.Float)
    longitude = db.Column(db.Float)
    hours_ne = db.Column(db.String(200))
    hours_en = db.Column(db.String(200))
    is_main = db.Column(db.Boolean, default=False)
    is_published = db.Column(db.Boolean, default=True)
    sort_order = db.Column(db.Integer, default=0)


class TeamMember(db.Model):
    __tablename__ = "team_members"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False)
    position_ne = db.Column(db.String(120))
    position_en = db.Column(db.String(120))
    phone = db.Column(db.String(40))
    bio_ne = db.Column(db.Text)
    bio_en = db.Column(db.Text)
    image_url = db.Column(db.Text)
    video_url = db.Column(db.Text)  # optional intro video for collaborators
    is_collaborator = db.Column(db.Boolean, default=False)  # True = Collaborated With section
    sort_order = db.Column(db.Integer, default=0)
    is_published = db.Column(db.Boolean, default=True)


class SiteSetting(db.Model):
    __tablename__ = "site_settings"

    id = db.Column(db.Integer, primary_key=True)
    key = db.Column(db.String(100), unique=True, nullable=False)
    value_ne = db.Column(db.Text)
    value_en = db.Column(db.Text)
    value_json = db.Column(db.JSON)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class SEOMetadata(db.Model):
    __tablename__ = "seo_metadata"

    id = db.Column(db.Integer, primary_key=True)
    page_key = db.Column(db.String(100), unique=True, nullable=False)
    title_ne = db.Column(db.String(200))
    title_en = db.Column(db.String(200))
    description_ne = db.Column(db.String(300))
    description_en = db.Column(db.String(300))
    og_image = db.Column(db.String(500))
    keywords = db.Column(db.String(300))


class ContentRevision(db.Model):
    __tablename__ = "content_revisions"

    id = db.Column(db.Integer, primary_key=True)
    content_type = db.Column(db.String(50), nullable=False)  # page, section, service...
    content_id = db.Column(db.Integer, nullable=False)
    data = db.Column(db.JSON, nullable=False)
    changed_by_id = db.Column(db.Integer, db.ForeignKey("admins.id"))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    changed_by = db.relationship("Admin")



class Advertisement(db.Model):
    """Site ads like a news portal — banners, side slots, inline."""
    __tablename__ = "advertisements"

    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    image_url = db.Column(db.Text)
    link_url = db.Column(db.String(500))
    placement = db.Column(db.String(40), default="home_mid", index=True)
    # placements: header_banner, home_top, home_mid, home_bottom, sidebar, footer, services, packages
    html_code = db.Column(db.Text)  # optional custom embed / script
    is_active = db.Column(db.Boolean, default=True)
    sort_order = db.Column(db.Integer, default=0)
    starts_at = db.Column(db.DateTime, nullable=True)
    ends_at = db.Column(db.DateTime, nullable=True)
    click_count = db.Column(db.Integer, default=0)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
