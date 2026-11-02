from datetime import datetime
from extensions import db
from app.models import Booking, BookingDetail, BookingStatusLog, Customer


def generate_booking_reference() -> str:
    """Generate unique reference: SR-2026-00001"""
    year = datetime.utcnow().year
    prefix = f"SR-{year}-"
    last = (
        Booking.query.filter(Booking.reference.like(f"{prefix}%"))
        .order_by(Booking.id.desc())
        .first()
    )
    if last:
        try:
            num = int(last.reference.split("-")[-1]) + 1
        except (ValueError, IndexError):
            num = 1
    else:
        num = 1
    return f"{prefix}{num:05d}"


def create_booking(
    *,
    full_name: str,
    mobile: str | None,
    email: str | None,
    booking_type: str,
    service_id: int | None = None,
    preferred_lang: str = "ne",
    special_requests: str | None = None,
    detail_data: dict | None = None,
    customer_id: int | None = None,
) -> Booking:
    """Create/link customer + booking + detail + initial status log."""
    customer = None

    # Prefer explicit logged-in customer
    if customer_id:
        customer = Customer.query.get(customer_id)

    # Match by mobile or email to avoid unique-email conflicts
    if not customer and mobile:
        customer = Customer.query.filter_by(mobile=mobile).first()
    if not customer and email:
        customer = Customer.query.filter_by(email=email.lower()).first()

    if not customer:
        customer = Customer(
            full_name=full_name,
            mobile=mobile or None,
            email=(email.lower() if email else None),
            preferred_lang=preferred_lang,
        )
        db.session.add(customer)
        db.session.flush()
    else:
        customer.full_name = full_name or customer.full_name
        if mobile and not customer.mobile:
            customer.mobile = mobile
        elif mobile:
            customer.mobile = mobile
        if email:
            # Only set email if empty or same account
            if not customer.email or customer.email.lower() == email.lower():
                customer.email = email.lower()
        customer.preferred_lang = preferred_lang

    reference = generate_booking_reference()
    booking = Booking(
        reference=reference,
        customer_id=customer.id,
        service_id=service_id,
        booking_type=booking_type,
        status="Pending",
        preferred_lang=preferred_lang,
        special_requests=special_requests,
    )
    db.session.add(booking)
    db.session.flush()

    detail = BookingDetail(booking_id=booking.id)
    if detail_data:
        extra = dict(detail_data.get("extra_data") or {})
        for key, value in detail_data.items():
            if key == "extra_data":
                continue
            if hasattr(detail, key):
                # Coerce numeric FKs
                if key == "package_id" and value is not None:
                    try:
                        value = int(value)
                    except (TypeError, ValueError):
                        value = None
                if key == "number_of_people" and value is not None:
                    try:
                        value = int(value)
                    except (TypeError, ValueError):
                        value = None
                setattr(detail, key, value)
            else:
                extra[key] = value
        detail.extra_data = extra
    db.session.add(detail)

    log = BookingStatusLog(
        booking_id=booking.id,
        old_status=None,
        new_status="Pending",
        note="Booking submitted by customer",
    )
    db.session.add(log)

    db.session.commit()
    return booking


def update_booking_status(booking: Booking, new_status: str, note: str | None = None, admin_id: int | None = None):
    """Update status. When moving to Confirmed, mark related payments as verified."""
    from datetime import datetime
    from app.models import Payment

    old = booking.status
    booking.status = new_status
    log = BookingStatusLog(
        booking_id=booking.id,
        old_status=old,
        new_status=new_status,
        note=note,
        changed_by_id=admin_id,
    )
    db.session.add(log)

    revenue_statuses = {"Confirmed", "Processing", "Completed"}
    if new_status in revenue_statuses:
        pays = Payment.query.filter_by(booking_id=booking.id).all()
        for pay in pays:
            if (pay.status or "").lower() in ("pending", "submitted", "payment verification", ""):
                pay.status = "verified"
                pay.verified_at = datetime.utcnow()
                if admin_id:
                    pay.verified_by_id = admin_id
            elif (pay.status or "").lower() == "verified":
                if not pay.verified_at:
                    pay.verified_at = datetime.utcnow()

    db.session.commit()
    return booking
