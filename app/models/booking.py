from datetime import datetime
from extensions import db


BOOKING_STATUSES = [
    "Pending",
    "Under Review",
    "Quotation Sent",
    "Awaiting Payment",
    "Payment Verification",
    "Confirmed",
    "Processing",
    "Completed",
    "Rejected",
    "Cancelled",
    "Refunded",
]


class Booking(db.Model):
    __tablename__ = "bookings"

    id = db.Column(db.Integer, primary_key=True)
    reference = db.Column(db.String(20), unique=True, nullable=False, index=True)  # SR-2026-00001
    customer_id = db.Column(db.Integer, db.ForeignKey("customers.id"), nullable=True)
    service_id = db.Column(db.Integer, db.ForeignKey("services.id"), nullable=True)
    booking_type = db.Column(db.String(50), nullable=False)  # flight, visa, tour, hotel, etc.
    status = db.Column(db.String(40), default="Pending", index=True)
    preferred_lang = db.Column(db.String(5), default="ne")
    special_requests = db.Column(db.Text)
    admin_notes = db.Column(db.Text)  # never expose to customer
    submitted_at = db.Column(db.DateTime, default=datetime.utcnow, index=True)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    customer = db.relationship("Customer", back_populates="bookings")
    service = db.relationship("Service", back_populates="bookings")
    details = db.relationship("BookingDetail", back_populates="booking", uselist=False, cascade="all, delete-orphan")
    status_logs = db.relationship("BookingStatusLog", back_populates="booking", order_by="BookingStatusLog.created_at", cascade="all, delete-orphan")
    quotations = db.relationship("Quotation", back_populates="booking", cascade="all, delete-orphan")
    payments = db.relationship("Payment", back_populates="booking", cascade="all, delete-orphan")
    documents = db.relationship("Document", back_populates="booking", cascade="all, delete-orphan")

    def summary_label(self, lang="ne"):
        """Human-readable what was booked: service / package / type details."""
        parts = []
        # Service
        try:
            if self.service:
                name = self.service.get_name(lang) if hasattr(self.service, "get_name") else (
                    self.service.name_ne if lang == "ne" else self.service.name_en
                )
                parts.append(name or self.service.slug)
        except Exception:
            pass
        # Package via details
        try:
            d = self.details
            if d and d.package:
                title = d.package.title_ne if lang == "ne" else d.package.title_en
                parts.append(title or f"Package #{d.package_id}")
            elif d and d.extra_data:
                extra = d.extra_data if isinstance(d.extra_data, dict) else {}
                pname = extra.get("package_name_ne") if lang == "ne" else extra.get("package_name")
                pname = pname or extra.get("package_name") or extra.get("package_name_ne")
                if pname:
                    parts.append(str(pname))
            if d:
                route = " → ".join([x for x in [d.departure, d.destination] if x])
                if route:
                    parts.append(route)
                if d.visa_type:
                    parts.append(str(d.visa_type))
        except Exception:
            pass
        type_labels = {
            "flight": {"ne": "उडान टिकट", "en": "Flight"},
            "visa": {"ne": "भिसा", "en": "Visa"},
            "tour": {"ne": "टुर प्याकेज", "en": "Tour package"},
            "hotel": {"ne": "होटल", "en": "Hotel"},
            "inquiry": {"ne": "सेवा अनुरोध", "en": "Service request"},
        }
        type_lab = type_labels.get(self.booking_type, {}).get(lang) or (self.booking_type or "").replace("-", " ").title()
        if not parts:
            return type_lab
        return f"{type_lab}: {' · '.join(parts)}"

    def current_status_label(self, lang="ne"):
        # Simple mapping; can be extended
        labels = {
            "Pending": {"ne": "पेन्डिङ", "en": "Pending"},
            "Under Review": {"ne": "समीक्षामा", "en": "Under Review"},
            "Quotation Sent": {"ne": "कोटेशन पठाइयो", "en": "Quotation Sent"},
            "Awaiting Payment": {"ne": "भुक्तानी प्रतीक्षा", "en": "Awaiting Payment"},
            "Payment Verification": {"ne": "भुक्तानी प्रमाणीकरण", "en": "Payment Verification"},
            "Confirmed": {"ne": "पुष्टि भयो", "en": "Confirmed"},
            "Processing": {"ne": "प्रशोधन हुँदै", "en": "Processing"},
            "Completed": {"ne": "पूरा भयो", "en": "Completed"},
            "Rejected": {"ne": "अस्वीकृत", "en": "Rejected"},
            "Cancelled": {"ne": "रद्द भयो", "en": "Cancelled"},
            "Refunded": {"ne": "रिफन्ड भयो", "en": "Refunded"},
        }
        return labels.get(self.status, {}).get(lang, self.status)


class BookingDetail(db.Model):
    """Flexible key-value / JSON-like storage for service-specific form data."""
    __tablename__ = "booking_details"

    id = db.Column(db.Integer, primary_key=True)
    booking_id = db.Column(db.Integer, db.ForeignKey("bookings.id"), nullable=False, unique=True)
    # Common fields
    trip_type = db.Column(db.String(30))  # one-way, round-trip
    departure = db.Column(db.String(120))
    destination = db.Column(db.String(120))
    departure_date = db.Column(db.Date)
    return_date = db.Column(db.Date)
    passengers = db.Column(db.Integer, default=1)
    travel_class = db.Column(db.String(40))
    # Visa specific
    visa_type = db.Column(db.String(80))
    travel_purpose = db.Column(db.String(120))
    nationality = db.Column(db.String(80))
    planned_travel_date = db.Column(db.Date)
    # Tour / Hotel
    package_id = db.Column(db.Integer, db.ForeignKey("packages.id"), nullable=True)
    number_of_people = db.Column(db.Integer)
    # Extra flexible data
    extra_data = db.Column(db.JSON, default=dict)

    booking = db.relationship("Booking", back_populates="details")
    package = db.relationship("Package")


class BookingStatusLog(db.Model):
    __tablename__ = "booking_status_logs"

    id = db.Column(db.Integer, primary_key=True)
    booking_id = db.Column(db.Integer, db.ForeignKey("bookings.id"), nullable=False, index=True)
    old_status = db.Column(db.String(40))
    new_status = db.Column(db.String(40), nullable=False)
    note = db.Column(db.Text)  # customer-facing note
    changed_by_id = db.Column(db.Integer, db.ForeignKey("admins.id"), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    booking = db.relationship("Booking", back_populates="status_logs")
    changed_by = db.relationship("Admin")
