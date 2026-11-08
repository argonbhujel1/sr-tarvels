from flask import Blueprint, render_template, request, redirect, url_for, flash, g, current_app, session
from flask_login import current_user
from app.models.customer import Customer
from app.models import Service, Booking
from app.services.booking_service import create_booking
from app.services.email_service import render_and_send_template
from extensions import db

booking_bp = Blueprint("booking", __name__)


def require_customer():
    """Booking requires a logged-in customer account."""
    ok = (
        current_user.is_authenticated
        and (
            isinstance(current_user, Customer)
            or getattr(current_user, "__class__", type).__name__ == "Customer"
            or str(getattr(current_user, "get_id", lambda: "")()).startswith("c:")
        )
    )
    if not ok:
        session["next_url"] = request.url
        flash(
            "Please login or create an account to book a service."
            if getattr(g, "lang", "ne") == "en"
            else "सेवा लिन खाता बनाउनुहोस् वा लगइन गर्नुहोस्।",
            "error",
        )
        return redirect(url_for("auth.login", next=request.path))
    return None



@booking_bp.route("/", methods=["GET"])
def index():
    """Booking type selector."""
    services = Service.query.filter_by(is_published=True).order_by(Service.sort_order).all()
    return render_template("public/booking/index.html", services=services)


@booking_bp.route("/flight", methods=["GET", "POST"])
def flight():
    blocked = require_customer()
    if blocked:
        return blocked

    if request.method == "POST":
        return _handle_booking(
            booking_type="flight",
            detail_data={
                "trip_type": request.form.get("trip_type"),
                "departure": request.form.get("departure"),
                "destination": request.form.get("destination"),
                "departure_date": request.form.get("departure_date") or None,
                "return_date": request.form.get("return_date") or None,
                "passengers": int(request.form.get("passengers") or 1),
                "travel_class": request.form.get("travel_class"),
            },
        )
    return render_template("public/booking/flight.html")


@booking_bp.route("/visa", methods=["GET", "POST"])
def visa():
    blocked = require_customer()
    if blocked:
        return blocked

    if request.method == "POST":
        return _handle_booking(
            booking_type="visa",
            detail_data={
                "destination": request.form.get("destination_country"),
                "visa_type": request.form.get("visa_type"),
                "travel_purpose": request.form.get("travel_purpose"),
                "nationality": request.form.get("nationality"),
                "planned_travel_date": request.form.get("planned_travel_date") or None,
            },
        )
    return render_template("public/booking/visa.html")


@booking_bp.route("/tour", methods=["GET", "POST"])
def tour():
    blocked = require_customer()
    if blocked:
        return blocked

    from app.models import Package
    packages = Package.query.filter_by(is_published=True).order_by(Package.sort_order).all()
    selected = None
    pkg_id = request.args.get("package") or request.form.get("package_id")
    if pkg_id:
        selected = Package.query.get(pkg_id)
    from app.models import PaymentMethod
    payment_methods = PaymentMethod.query.filter_by(is_enabled=True).order_by(PaymentMethod.sort_order).all()
    # Advance amount: min_payment preferred, else price_from
    def _pkg_amount(pkg):
        if not pkg:
            return None
        if pkg.min_payment:
            return pkg.min_payment
        return pkg.price_from

    if request.method == "POST":
        package_id = request.form.get("package_id")
        pkg = Package.query.get(package_id) if package_id else None
        amt = _pkg_amount(pkg)
        return _handle_booking(
            booking_type="tour",
            detail_data={
                "travel_date": request.form.get("travel_date"),
                "number_of_people": request.form.get("number_of_people"),
                "package_id": int(package_id) if package_id and str(package_id).isdigit() else None,
                "extra_data": {
                    "package_id": package_id,
                    "package_name": (pkg.get_title("en") if pkg and hasattr(pkg, "get_title") else (pkg.title_en if pkg else "")),
                    "package_name_ne": (pkg.title_ne if pkg else ""),
                    "price_from": str(pkg.price_from) if pkg and pkg.price_from else None,
                    "min_payment": str(pkg.min_payment) if pkg and pkg.min_payment else None,
                },
            },
            require_payment=bool(amt),
            payment_amount=amt,
        )
    req = bool(_pkg_amount(selected))
    return render_template(
        "public/booking/tour.html",
        packages=packages,
        selected_package=selected,
        require_payment=req,
        amount=_pkg_amount(selected) if selected else None,
        currency=(selected.currency if selected else "NPR"),
        payment_methods=payment_methods,
    )


@booking_bp.route("/general", methods=["GET", "POST"])
def general():
    blocked = require_customer()
    if blocked:
        return blocked

    """Generic inquiry for documentation, police, insurance, etc."""
    from app.models import PaymentMethod
    service_slug = request.args.get("service")
    service = None
    if service_slug:
        service = Service.query.filter_by(slug=service_slug, is_published=True).first()
    require_payment = bool(service and service.price_npr)
    amount = service.price_npr if require_payment else None
    payment_methods = PaymentMethod.query.filter_by(is_enabled=True).order_by(PaymentMethod.sort_order).all()
    if request.method == "POST":
        return _handle_booking(
            booking_type=request.form.get("booking_type") or "inquiry",
            service_id=service.id if service else None,
            detail_data={"extra_data": {k: v for k, v in request.form.items() if k not in ("csrf_token",)}},
            require_payment=require_payment,
            payment_amount=amount,
        )
    return render_template(
        "public/booking/general.html",
        service=service,
        require_payment=require_payment,
        amount=amount,
        currency="NPR",
        payment_methods=payment_methods,
    )


def _handle_booking(
    booking_type: str,
    detail_data: dict | None = None,
    service_id: int | None = None,
    require_payment: bool = False,
    payment_amount=None,
):
    full_name = request.form.get("full_name", "").strip()
    mobile = request.form.get("mobile", "").strip()
    email = request.form.get("email", "").strip() or None
    special = request.form.get("special_requests", "").strip() or None

    # Prefer logged-in customer profile
    logged_customer = None
    if current_user.is_authenticated and isinstance(current_user, Customer):
        logged_customer = current_user
        if not full_name:
            full_name = (current_user.full_name or "").strip()
        if not mobile:
            mobile = (current_user.mobile or "").strip()
        if not email and current_user.email:
            email = current_user.email

    if not full_name:
        flash("Name is required." if g.lang == "en" else "नाम आवश्यक छ।", "error")
        return redirect(request.url)

    # Mobile strongly preferred but allow OAuth users without mobile once
    if not mobile and not logged_customer:
        flash("Name and mobile are required." if g.lang == "en" else "नाम र मोबाइल आवश्यक छ।", "error")
        return redirect(request.url)

    # Compulsory payment proof when price is fixed
    if require_payment and payment_amount:
        txn = request.form.get("transaction_id", "").strip()
        method_id = request.form.get("payment_method_id", "").strip()
        proof = request.files.get("payment_proof")
        if not txn or not method_id or not proof or not proof.filename:
            flash(
                "Transaction number, payment method and payment screenshot are required."
                if g.lang == "en"
                else "Transaction number, भुक्तानी विधि र भुक्तानी स्क्रिनसट अनिवार्य छ।",
                "error",
            )
            return redirect(request.url)

    try:
        booking = create_booking(
            full_name=full_name,
            mobile=mobile or None,
            email=email,
            booking_type=booking_type,
            service_id=service_id,
            preferred_lang=g.lang,
            special_requests=special,
            detail_data=detail_data or {},
            customer_id=logged_customer.id if logged_customer else None,
        )

        from app.services.storage_service import save_local_upload
        from app.models import Document, Payment

        # Save uploaded documents
        files = request.files.getlist("documents")
        for f in files:
            if f and f.filename:
                url = save_local_upload(f, subfolder="docs")
                if url:
                    doc = Document(
                        booking_id=booking.id,
                        original_filename=f.filename,
                        stored_filename=url.split("/")[-1],
                        cloudinary_url=url,
                        mime_type=f.mimetype,
                        is_private=True,
                    )
                    db.session.add(doc)

        # Save payment proof
        if require_payment and payment_amount:
            proof = request.files.get("payment_proof")
            proof_url = None
            if proof and proof.filename:
                proof_url = save_local_upload(proof, subfolder="payments")
            pay = Payment(
                booking_id=booking.id,
                payment_method_id=int(request.form.get("payment_method_id")),
                amount=payment_amount,
                currency="NPR",
                transaction_id=request.form.get("transaction_id", "").strip(),
                status="submitted",
                receipt_url=proof_url,
                notes="Customer submitted payment proof with booking"
                + ("" if proof_url else " (proof file upload failed — check Cloudinary)"),
            )
            db.session.add(pay)
            booking.status = "Payment Verification"

        db.session.commit()

    except Exception as e:
        current_app.logger.exception("Booking creation failed")
        db.session.rollback()
        msg = str(e)[:180]
        flash(
            ("Booking failed: " + msg)
            if g.lang == "en"
            else ("बुकिङ असफल: " + msg),
            "error",
        )
        return redirect(request.url)

    # Send confirmation email (if email provided and SMTP configured)
    if email:
        tracking_url = url_for("booking.track", _external=True) + f"?ref={booking.reference}&mobile={mobile}"
        render_and_send_template(
            "booking_received",
            to=email,
            lang=g.lang,
            context={
                "customer_name": full_name,
                "booking_id": booking.reference,
                "service_name": booking_type,
                "tracking_url": tracking_url,
                "company_name": current_app.config.get("APP_NAME"),
            },
            booking_id=booking.id,
        )

    try:
        from app.services.email_service import send_booking_received_email
        send_booking_received_email(
            booking,
            customer_name=current_user.full_name if current_user.is_authenticated else request.form.get("full_name", ""),
            customer_email=(current_user.email if current_user.is_authenticated and getattr(current_user, "email", None) else request.form.get("email", "")),
            lang=getattr(g, "lang", "ne"),
        )
    except Exception as _mail_e:
        current_app.logger.warning("booking mail: %s", _mail_e)
    return redirect(url_for("booking.success", ref=booking.reference))



@booking_bp.route("/success")
def success():
    ref = request.args.get("ref")
    return render_template("public/booking/success.html", reference=ref)


@booking_bp.route("/track", methods=["GET", "POST"])
def track():
    booking = None
    error = None
    if request.method == "POST" or (request.args.get("ref") and request.args.get("mobile")):
        ref = (request.form.get("reference") or request.args.get("ref") or "").strip().upper()
        mobile = (request.form.get("mobile") or request.args.get("mobile") or "").strip()
        if ref and mobile:
            booking = (
                Booking.query.filter_by(reference=ref)
                .join(Booking.customer)
                .filter_by(mobile=mobile)
                .first()
            )
            if not booking:
                error = "Booking not found. Please check reference and mobile." if g.lang == "en" else "बुकिङ फेला परेन। रेफरेन्स र मोबाइल जाँच गर्नुहोस्।"
        else:
            error = "Both fields are required." if g.lang == "en" else "दुवै फिल्ड आवश्यक छन्।"
    return render_template("public/booking/track.html", booking=booking, error=error)
