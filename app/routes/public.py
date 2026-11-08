from flask import Blueprint, render_template, g, request, redirect, url_for, session, current_app, flash
from app.models import (
    ServiceCategory, Service, Destination, Package, Offer,
    Testimonial, FAQ, Page, HomepageSection, Branch, Gallery
)

public_bp = Blueprint("public", __name__)


@public_bp.route("/")
def home():
    lang = g.lang
    sections = {
        s.key: s for s in HomepageSection.query.filter_by(is_enabled=True).order_by(HomepageSection.sort_order).all()
    }
    categories = ServiceCategory.query.filter_by(is_published=True).order_by(ServiceCategory.sort_order).all()
    featured_services = Service.query.filter_by(is_published=True, is_featured=True).limit(6).all()
    destinations = Destination.query.filter_by(is_published=True).order_by(Destination.sort_order).limit(4).all()
    packages = Package.query.filter_by(is_published=True, is_featured=True).limit(4).all()
    offers = Offer.query.filter_by(is_published=True).order_by(Offer.sort_order).limit(3).all()
    testimonials = Testimonial.query.filter_by(is_published=True).order_by(Testimonial.id.desc()).limit(5).all()
    faqs = []
    try:
        faqs = FAQ.query.filter_by(is_published=True, is_featured=True).order_by(FAQ.sort_order).limit(6).all()
        if not faqs:
            faqs = FAQ.query.filter_by(is_published=True).order_by(FAQ.sort_order).limit(4).all()
    except Exception:
        try:
            from extensions import db
            db.session.rollback()
            faqs = FAQ.query.filter_by(is_published=True).order_by(FAQ.sort_order).limit(4).all()
        except Exception:
            from extensions import db
            db.session.rollback()
            faqs = []
    branches = Branch.query.filter_by(is_published=True).order_by(Branch.sort_order).all()

    from app.models import SiteSetting
    def _s(key, default=""):
        row = SiteSetting.query.filter_by(key=key).first()
        return (row.value_ne if row and row.value_ne else default)

    popup_enabled = _s("popup_enabled") in ("1", "true", "yes", "on")
    popup_title = _s("popup_title_ne") if g.lang == "ne" else (_s("popup_title_en") or _s("popup_title_ne"))
    popup_body = _s("popup_body_ne") if g.lang == "ne" else (_s("popup_body_en") or _s("popup_body_ne"))
    popup_image = _s("popup_image_url")
    # Enable popup if flag on AND (title/body/image present)
    if popup_enabled and not (popup_title or popup_body or popup_image):
        popup_enabled = False
    if not popup_title and popup_image:
        popup_title = ""
    if not popup_title and not popup_image:
        popup_title = "स्वागत छ" if g.lang == "ne" else "Welcome"

    return render_template(
        "public/home.html",
        sections=sections,
        categories=categories,
        featured_services=featured_services,
        destinations=destinations,
        packages=packages,
        offers=offers,
        testimonials=testimonials,
        faqs=faqs,
        branches=branches,
        popup_enabled=popup_enabled,
        popup_title=popup_title,
        popup_body=popup_body,
        popup_image=popup_image,
    )


@public_bp.route("/set-lang/<lang>")
def set_lang(lang):
    if lang in current_app.config.get("SUPPORTED_LANGS", ["ne", "en"]):
        session["lang"] = lang
    next_url = request.args.get("next") or request.referrer or url_for("public.home")
    return redirect(next_url)


@public_bp.route("/about")
def about():
    from app.models import TeamMember
    page = Page.query.filter_by(slug="about", is_published=True).first()
    # role stored in position or we use a simple convention:
    # team = normal members/owners; collaborators marked via bio starting with [collab] or separate later
    team_members = (
        TeamMember.query.filter_by(is_published=True, is_collaborator=False)
        .order_by(TeamMember.sort_order).all()
    )
    collaborators = (
        TeamMember.query.filter_by(is_published=True, is_collaborator=True)
        .order_by(TeamMember.sort_order).all()
    )
    return render_template(
        "public/about.html",
        page=page,
        team_members=team_members,
        collaborators=collaborators,
    )



@public_bp.route("/services")
def services():
    categories = ServiceCategory.query.filter_by(is_published=True).order_by(ServiceCategory.sort_order).all()
    return render_template("public/services.html", categories=categories)


@public_bp.route("/services/<slug>")
def service_detail(slug):
    service = Service.query.filter_by(slug=slug, is_published=True).first_or_404()
    return render_template("public/service_detail.html", service=service)


@public_bp.route("/destinations")
def destinations():
    items = Destination.query.filter_by(is_published=True).order_by(Destination.sort_order).all()
    return render_template("public/destinations.html", destinations=items)


@public_bp.route("/packages")
def packages():
    items = Package.query.filter_by(is_published=True).order_by(Package.sort_order).all()
    return render_template("public/packages.html", packages=items)


@public_bp.route("/packages/<slug>")
def package_detail(slug):
    item = Package.query.filter_by(slug=slug, is_published=True).first_or_404()
    return render_template("public/packages.html", packages=[item])



@public_bp.route("/offers")
def offers():
    items = Offer.query.filter_by(is_published=True).order_by(Offer.sort_order).all()
    return render_template("public/offers.html", offers=items)


@public_bp.route("/gallery")
def gallery():
    items = Gallery.query.filter_by(is_published=True).order_by(Gallery.sort_order).all()
    return render_template("public/gallery.html", items=items)


@public_bp.route("/testimonials", methods=["GET", "POST"])
def testimonials():
    from flask_login import current_user
    from app.models.customer import Customer
    from extensions import db
    if request.method == "POST":
        if not current_user.is_authenticated or not isinstance(current_user, Customer):
            flash("Please login to submit a review." if g.lang == "en" else "रिव्यू दिन लगइन गर्नुहोस्।", "error")
            return redirect(url_for("auth.login", next=url_for("public.testimonials")))
        content = (request.form.get("content") or "").strip()
        rating = request.form.get("rating", type=int) or 5
        rating = max(1, min(5, rating))
        if not content:
            flash("Review text required." if g.lang == "en" else "रिव्यू लेख्नुहोस्।", "error")
            return redirect(url_for("public.testimonials"))
        # Direct publish for logged-in users
        trow = Testimonial(
            customer_name=current_user.full_name,
            content_ne=content,
            content_en=content,
            rating=rating,
            image_url=getattr(current_user, "avatar_url", None),
            mobile=getattr(current_user, "mobile", None),
            customer_id=current_user.id,
            is_published=True,
            sort_order=0,
        )
        db.session.add(trow)
        db.session.commit()
        flash("Thank you! Your review is published." if g.lang == "en" else "धन्यवाद! तपाईंको रिव्यू प्रकाशित भयो।", "success")
        return redirect(url_for("public.testimonials"))
    items = Testimonial.query.filter_by(is_published=True).order_by(Testimonial.id.desc()).all()
    return render_template("public/testimonials.html", items=items)


@public_bp.route("/newsletter", methods=["POST"])
def newsletter_subscribe():
    from extensions import db
    from app.models import NewsletterSubscriber
    email = (request.form.get("email") or "").strip().lower()
    if not email or "@" not in email:
        flash("Valid email required." if g.lang == "en" else "मान्य इमेल आवश्यक।", "error")
        return redirect(request.referrer or url_for("public.home"))
    existing = NewsletterSubscriber.query.filter_by(email=email).first()
    if existing:
        existing.is_active = True
    else:
        db.session.add(NewsletterSubscriber(email=email, is_active=True))
    db.session.commit()
    flash("Subscribed to newsletter." if g.lang == "en" else "न्यूजलेटरमा सदस्यता भयो।", "success")
    return redirect(request.referrer or url_for("public.home"))


@public_bp.route("/faqs")
def faqs():
    items = FAQ.query.filter_by(is_published=True).order_by(FAQ.sort_order).all()
    return render_template("public/faqs.html", faqs=items)


@public_bp.route("/contact", methods=["GET", "POST"])
def contact():
    from app.models import ContactMessage
    from extensions import db
    if request.method == "POST":
        msg = ContactMessage(
            name=request.form.get("name", "").strip(),
            email=request.form.get("email", "").strip(),
            mobile=request.form.get("mobile", "").strip(),
            subject=request.form.get("subject", "").strip(),
            message=request.form.get("message", "").strip(),
        )
        if msg.name and msg.message:
            db.session.add(msg)
            db.session.commit()
            try:
                from app.services.email_service import send_contact_emails
                send_contact_emails(msg, lang=getattr(g, "lang", "ne"))
            except Exception as e:
                current_app.logger.exception("Contact email error: %s", e)
            return render_template("public/contact.html", success=True)
    return render_template("public/contact.html", success=False)


@public_bp.route("/privacy")
@public_bp.route("/privacy/")
def privacy():
    """Public Privacy Policy — no login required. Always HTTP 200 with full policy text."""
    return render_template("public/privacy.html")


@public_bp.route("/data-deletion")
@public_bp.route("/data-deletion/")
def data_deletion():
    """Public user data deletion instructions (Facebook / account data). No login required."""
    return render_template("public/data_deletion.html")



@public_bp.route("/terms")
def terms():
    page = Page.query.filter_by(slug="terms", is_published=True).first()
    return render_template("public/page.html", page=page, page_title="Terms & Conditions")


@public_bp.route("/cancellation")
def cancellation():
    page = Page.query.filter_by(slug="cancellation", is_published=True).first()
    return render_template("public/page.html", page=page, page_title="Cancellation & Refund Policy")


@public_bp.route("/robots.txt")
def robots():
    return current_app.send_static_file("robots.txt")


@public_bp.route("/sitemap.xml")
def sitemap():
    # Minimal sitemap; expand in production
    from flask import Response
    base = current_app.config.get("APP_URL", "")
    urls = ["/", "/about", "/services", "/contact", "/track"]
    xml = '<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
    for u in urls:
        xml += f"  <url><loc>{base}{u}</loc></url>\n"
    xml += "</urlset>"
    return Response(xml, mimetype="application/xml")


@public_bp.route("/destinations/<slug>/inquire", methods=["GET", "POST"])
def destination_inquire(slug):
    item = Destination.query.filter_by(slug=slug, is_published=True).first_or_404()
    if request.method == "POST":
        from app.services.booking_service import create_booking
        from flask import flash, redirect, url_for, g
        full_name = request.form.get("full_name", "").strip()
        mobile = request.form.get("mobile", "").strip()
        email = request.form.get("email", "").strip() or None
        special = request.form.get("special_requests", "").strip() or None
        if not full_name or not mobile:
            flash("Name and mobile required", "error")
            return redirect(request.url)
        booking = create_booking(
            full_name=full_name,
            mobile=mobile,
            email=email,
            booking_type="destination",
            preferred_lang=g.lang,
            special_requests=special,
            detail_data={
                "destination": item.name_en,
                "extra_data": {
                    "destination_slug": item.slug,
                    "destination_name": item.name_en,
                    "travel_date": request.form.get("travel_date"),
                    "people": request.form.get("people"),
                },
            },
        )
        return redirect(url_for("booking.success", ref=booking.reference))
    return render_template("public/destination_inquire.html", destination=item)

