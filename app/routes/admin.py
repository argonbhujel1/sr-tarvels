from flask import current_app, Blueprint, render_template, request, redirect, url_for, flash, g
from flask_login import login_user, logout_user, login_required, current_user
from extensions import db, limiter
from app.models import (
    Admin, Booking, BookingDetail, ContactMessage, Payment, Service, ServiceCategory,
    PaymentMethod, HomepageSection, Page, FAQ, SiteSetting, Branch,
    Destination, Package, Offer, Testimonial, Gallery, TeamMember
)
from datetime import datetime
from sqlalchemy import func

admin_bp = Blueprint("admin", __name__, template_folder="../templates/admin")


@admin_bp.route("/login", methods=["GET", "POST"])
@limiter.limit("10 per minute")
def login():
    if current_user.is_authenticated:
        return redirect(url_for("admin.dashboard"))
    if request.method == "POST":
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")
        admin = Admin.query.filter_by(email=email, is_active=True).first()
        if admin and admin.check_password(password):
            login_user(admin, remember=True)
            admin.last_login = datetime.utcnow()
            db.session.commit()
            return redirect(url_for("admin.dashboard"))
        flash("Invalid credentials", "error")
    return render_template("admin/login.html")




@admin_bp.route("/oauth/google")
def oauth_google():
    """Google login for admins — email must already exist in Admin table."""
    import os
    from urllib.parse import urlencode
    client_id = current_app.config.get("GOOGLE_CLIENT_ID") or os.getenv("GOOGLE_CLIENT_ID")
    if not client_id:
        flash("Google OAuth not configured", "error")
        return redirect(url_for("admin.login"))
    redirect_uri = url_for("admin.oauth_google_callback", _external=True)
    params = {
        "client_id": client_id,
        "redirect_uri": redirect_uri,
        "response_type": "code",
        "scope": "openid email profile",
        "prompt": "select_account",
    }
    return redirect("https://accounts.google.com/o/oauth2/v2/auth?" + urlencode(params))


@admin_bp.route("/oauth/google/callback")
def oauth_google_callback():
    import os
    import requests as http_requests
    from app.models import Admin
    code = request.args.get("code")
    if not code:
        flash("Google login cancelled", "error")
        return redirect(url_for("admin.login"))
    client_id = current_app.config.get("GOOGLE_CLIENT_ID") or os.getenv("GOOGLE_CLIENT_ID")
    client_secret = current_app.config.get("GOOGLE_CLIENT_SECRET") or os.getenv("GOOGLE_CLIENT_SECRET")
    redirect_uri = url_for("admin.oauth_google_callback", _external=True)
    try:
        token_res = http_requests.post(
            "https://oauth2.googleapis.com/token",
            data={
                "code": code,
                "client_id": client_id,
                "client_secret": client_secret,
                "redirect_uri": redirect_uri,
                "grant_type": "authorization_code",
            },
            timeout=15,
        )
        token_res.raise_for_status()
        tokens = token_res.json()
        info = http_requests.get(
            "https://www.googleapis.com/oauth2/v3/userinfo",
            headers={"Authorization": f"Bearer {tokens['access_token']}"},
            timeout=15,
        )
        info.raise_for_status()
        email = (info.json().get("email") or "").lower()
    except Exception as e:
        current_app.logger.exception("admin google oauth: %s", e)
        flash("Google login failed", "error")
        return redirect(url_for("admin.login"))
    if not email:
        flash("No email from Google", "error")
        return redirect(url_for("admin.login"))
    admin = Admin.query.filter_by(email=email).first()
    if not admin:
        flash("This email is not authorized for admin access. Add it under Admin accounts first.", "error")
        return redirect(url_for("admin.login"))
    login_user(admin, remember=True)
    return redirect(url_for("admin.dashboard"))


@admin_bp.route("/oauth/facebook")
def oauth_facebook():
    import os
    from urllib.parse import urlencode
    app_id = current_app.config.get("FACEBOOK_APP_ID") or os.getenv("FACEBOOK_APP_ID")
    if not app_id:
        flash("Facebook OAuth not configured", "error")
        return redirect(url_for("admin.login"))
    redirect_uri = url_for("admin.oauth_facebook_callback", _external=True)
    params = {
        "client_id": app_id,
        "redirect_uri": redirect_uri,
        "scope": "email,public_profile",
        "response_type": "code",
    }
    return redirect("https://www.facebook.com/v18.0/dialog/oauth?" + urlencode(params))


@admin_bp.route("/oauth/facebook/callback")
def oauth_facebook_callback():
    import os
    import requests as http_requests
    from app.models import Admin
    code = request.args.get("code")
    if not code:
        flash("Facebook login cancelled", "error")
        return redirect(url_for("admin.login"))
    app_id = current_app.config.get("FACEBOOK_APP_ID") or os.getenv("FACEBOOK_APP_ID")
    app_secret = current_app.config.get("FACEBOOK_APP_SECRET") or os.getenv("FACEBOOK_APP_SECRET")
    redirect_uri = url_for("admin.oauth_facebook_callback", _external=True)
    try:
        token_res = http_requests.get(
            "https://graph.facebook.com/v18.0/oauth/access_token",
            params={
                "client_id": app_id,
                "client_secret": app_secret,
                "redirect_uri": redirect_uri,
                "code": code,
            },
            timeout=15,
        )
        token_res.raise_for_status()
        access_token = token_res.json().get("access_token")
        info = http_requests.get(
            "https://graph.facebook.com/me",
            params={"fields": "id,name,email", "access_token": access_token},
            timeout=15,
        )
        info.raise_for_status()
        email = (info.json().get("email") or "").lower()
    except Exception as e:
        current_app.logger.exception("admin fb oauth: %s", e)
        flash("Facebook login failed", "error")
        return redirect(url_for("admin.login"))
    if not email:
        flash("No email from Facebook (permission required)", "error")
        return redirect(url_for("admin.login"))
    admin = Admin.query.filter_by(email=email).first()
    if not admin:
        flash("This email is not authorized for admin access. Add it under Admin accounts first.", "error")
        return redirect(url_for("admin.login"))
    login_user(admin, remember=True)
    return redirect(url_for("admin.dashboard"))



@admin_bp.route("/logout")
@login_required
def logout():
    logout_user()
    return redirect(url_for("admin.login"))


@admin_bp.route("/")
@login_required
def dashboard():
    total_bookings = Booking.query.count()
    pending = Booking.query.filter_by(status="Pending").count()
    confirmed = Booking.query.filter(Booking.status.in_(["Confirmed", "Processing", "Completed"])).count()
    completed = Booking.query.filter_by(status="Completed").count()
    new_messages = ContactMessage.query.filter_by(is_read=False).count()
    recent = Booking.query.order_by(Booking.submitted_at.desc()).limit(10).all()
    return render_template(
        "admin/dashboard.html",
        total_bookings=total_bookings,
        pending=pending,
        confirmed=confirmed,
        completed=completed,
        new_messages=new_messages,
        recent=recent,
    )


# ─── Bookings ───────────────────────────────────────────────

@admin_bp.route("/bookings")
@login_required
def bookings():
    from sqlalchemy.orm import joinedload
    status = request.args.get("status")
    q = (
        Booking.query.options(
            joinedload(Booking.details).joinedload(BookingDetail.package),
            joinedload(Booking.customer),
            joinedload(Booking.service),
        )
        .order_by(Booking.submitted_at.desc())
    )
    if status:
        q = q.filter_by(status=status)
    items = q.limit(100).all()
    return render_template("admin/bookings.html", bookings=items, current_status=status)


@admin_bp.route("/bookings/<int:id>", methods=["GET", "POST"])
@login_required
def booking_detail(id):
    from sqlalchemy.orm import joinedload
    booking = (
        Booking.query.options(
            joinedload(Booking.details).joinedload(BookingDetail.package),
            joinedload(Booking.customer),
            joinedload(Booking.service),
            joinedload(Booking.payments),
            joinedload(Booking.documents),
            joinedload(Booking.status_logs),
        )
        .filter_by(id=id)
        .first_or_404()
    )
    if request.method == "POST":
        new_status = request.form.get("status")
        note = request.form.get("note", "").strip()
        if new_status and new_status != booking.status:
            from app.services.booking_service import update_booking_status
            update_booking_status(booking, new_status, note=note, admin_id=current_user.id)
            # Notify customer by email if available
            cust = booking.customer
            if cust and cust.email:
                try:
                    from app.services.email_service import send_booking_status_email, send_email, wrap_email_html
                    ok = send_booking_status_email(
                        booking,
                        cust,
                        new_status,
                        note=note or "",
                        lang="ne",
                    )
                    if not ok:
                        # Guaranteed decorative fallback
                        brand_note = (note or "").replace(chr(10), "<br>")
                        track = f"https://srtravels.argan.com.np/booking/track?ref={booking.reference}"
                        inner = f"""
                        <h2 style="margin:0 0 12px;color:#10243A;">Booking status update</h2>
                        <p>Hello <strong>{cust.full_name}</strong>,</p>
                        <p>Your booking status has changed.</p>
                        <table width="100%" style="background:#F6F8FA;border-radius:8px;font-size:14px;">
                          <tr><td style="padding:12px;color:#666;">Booking number</td><td style="padding:12px;"><strong>{booking.reference}</strong></td></tr>
                          <tr><td style="padding:12px;color:#666;">New status</td><td style="padding:12px;"><strong style="color:#C9A45C;">{new_status}</strong></td></tr>
                          {"<tr><td style='padding:12px;color:#666;'>Note</td><td style='padding:12px;'>"+brand_note+"</td></tr>" if note else ""}
                        </table>
                        <p style="text-align:center;margin:20px 0;"><a href="{track}" style="background:#10243A;color:#fff;padding:12px 24px;border-radius:8px;text-decoration:none;font-weight:700;">Track booking</a></p>
                        """
                        html = wrap_email_html(inner, email_reason="Booking update · बुकिङ अपडेट")
                        send_email(
                            cust.email,
                            f"Booking update – {booking.reference}",
                            html,
                            template_key="booking_status_update",
                            booking_id=booking.id,
                            auto_wrap=False,
                        )
                except Exception as e:
                    from flask import current_app
                    current_app.logger.exception("status email: %s", e)
            flash("Status updated" + (" (email notified)" if cust and cust.email else ""), "success")
        return redirect(url_for("admin.booking_detail", id=id))
    return render_template("admin/booking_detail.html", booking=booking)


@admin_bp.route("/bookings/<int:id>/delete", methods=["POST"])
@login_required
def booking_delete(id):
    booking = Booking.query.get_or_404(id)
    ref = booking.reference
    try:
        db.session.delete(booking)
        db.session.commit()
        flash(f"Booking {ref} deleted", "success")
    except Exception as e:
        db.session.rollback()
        flash(f"Could not delete booking: {e}", "error")
    return redirect(url_for("admin.bookings"))


# ─── Messages ───────────────────────────────────────────────

@admin_bp.route("/messages")
@login_required
def messages():
    items = ContactMessage.query.order_by(ContactMessage.created_at.desc()).limit(50).all()
    return render_template("admin/messages.html", messages=items)


@admin_bp.route("/messages/<int:id>", methods=["GET", "POST"])
@login_required
def message_detail(id):
    msg = ContactMessage.query.get_or_404(id)
    if not msg.is_read:
        msg.is_read = True
        db.session.commit()
    if request.method == "POST":
        reply_body = request.form.get("reply_body", "").strip()
        if reply_body and msg.email:
            from app.services.email_service import send_email, wrap_email_html
            from flask import current_app
            subject = f"Re: {msg.subject or 'Your inquiry'} — {current_app.config.get('APP_NAME')}"
            inner = f"""
              <h2 style="margin:0 0 12px;color:#10243A;font-size:20px;">Reply to your inquiry</h2>
              <p style="margin:0 0 12px;line-height:1.6;">Dear <strong>{msg.name}</strong>,</p>
              <p style="margin:0 0 8px;color:#666;font-size:13px;">Regarding: {msg.subject or 'your message'}</p>
              <div style="background:#F6F8FA;padding:16px;border-radius:8px;margin:1rem 0;line-height:1.65;color:#172331;">
                {reply_body.replace(chr(10), '<br>')}
              </div>
              <p style="color:#666;font-size:0.9rem;margin-top:1rem;">— {current_app.config.get('APP_NAME')}</p>
            """
            html = wrap_email_html(inner, email_reason="Message reply · सन्देश जवाफ")
            ok = send_email(to=msg.email, subject=subject, html_body=html, template_key="contact_reply", auto_wrap=False)
            if ok:
                flash("Reply sent by email", "success")
            else:
                flash("Reply could not be sent (check SMTP settings)", "error")
        elif not msg.email:
            flash("No email on this message — cannot reply by mail", "error")
        else:
            flash("Reply body required", "error")
        return redirect(url_for("admin.message_detail", id=id))
    return render_template("admin/message_detail.html", message=msg)



# ─── Payment Methods ────────────────────────────────────────

@admin_bp.route("/payment-methods", methods=["GET", "POST"])
@login_required
def payment_methods():
    from app.services.storage_service import save_local_upload
    if request.method == "POST":
        method_id = request.form.get("id")
        method = PaymentMethod.query.get(method_id)
        if method:
            method.is_enabled = request.form.get("is_enabled") == "on"
            method.instructions_ne = request.form.get("instructions_ne", "")
            method.instructions_en = request.form.get("instructions_en", "")
            method.sort_order = int(request.form.get("sort_order") or 0)
            if request.form.get("logo_url"):
                method.logo_url = request.form.get("logo_url")
            if "external_url" in request.form:
                method.external_url = request.form.get("external_url", "").strip() or None
            if request.form.get("qr_image_url"):
                method.qr_image_url = request.form.get("qr_image_url")
            logo_f = request.files.get("logo_file")
            if logo_f and logo_f.filename:
                url = save_local_upload(logo_f, subfolder="payments")
                if url:
                    method.logo_url = url
            qr_f = request.files.get("qr_file")
            if qr_f and qr_f.filename:
                url = save_local_upload(qr_f, subfolder="payments")
                if url:
                    method.qr_image_url = url
            db.session.commit()
            flash(f"{method.name_en} updated", "success")
        return redirect(url_for("admin.payment_methods"))
    methods = PaymentMethod.query.order_by(PaymentMethod.sort_order).all()
    return render_template("admin/payment_methods.html", methods=methods)



@admin_bp.route("/payments")
@login_required
def payments():
    methods = PaymentMethod.query.order_by(PaymentMethod.sort_order).all()
    payments = Payment.query.order_by(Payment.created_at.desc()).limit(50).all()
    return render_template("admin/payments.html", methods=methods, payments=payments)


# ─── Homepage Sections (CMS) ────────────────────────────────

@admin_bp.route("/homepage")
@login_required
def homepage():
    sections = HomepageSection.query.order_by(HomepageSection.sort_order).all()
    return render_template("admin/homepage.html", sections=sections)


@admin_bp.route("/homepage/<int:id>", methods=["GET", "POST"])
@login_required
def homepage_edit(id):
    section = HomepageSection.query.get_or_404(id)
    if request.method == "POST":
        section.title_ne = request.form.get("title_ne", "")
        section.title_en = request.form.get("title_en", "")
        section.subtitle_ne = request.form.get("subtitle_ne", "")
        section.subtitle_en = request.form.get("subtitle_en", "")
        section.content_ne = request.form.get("content_ne", "")
        section.content_en = request.form.get("content_en", "")
        section.cta_text_ne = request.form.get("cta_text_ne", "")
        section.cta_text_en = request.form.get("cta_text_en", "")
        section.cta_url = request.form.get("cta_url", "")
        section.image_url = request.form.get("image_url", "") or section.image_url
        f = request.files.get("image_file")
        if f and f.filename:
            from app.services.storage_service import save_local_upload
            url = save_local_upload(f, subfolder="homepage")
            if url:
                section.image_url = url
        section.is_enabled = request.form.get("is_enabled") == "on"
        section.sort_order = int(request.form.get("sort_order") or 0)
        db.session.commit()
        # Email registered users when announcement section is updated
        if section.key == "announcement" and section.is_enabled:
            try:
                from app.models import Customer
                from app.services.email_service import send_email, _brand_context
                from flask import render_template
                brand = _brand_context()
                title = section.title_en or section.title_ne or "Announcement"
                body_txt = section.content_en or section.content_ne or section.subtitle_en or section.subtitle_ne or ""
                html_base = f"""<!DOCTYPE html><html><body style="margin:0;background:#F6F8FA;font-family:Arial,sans-serif;">
                    <table width="100%" style="padding:24px 12px;"><tr><td align="center">
                    <table width="600" style="max-width:600px;background:#fff;border-radius:12px;overflow:hidden;border:1px solid #e5e9ef;">
                    <tr><td style="background:#081D33;padding:20px;text-align:center;">
                    {"<img src='"+str(brand.get('logo_url') or '')+"' style='max-height:48px;margin-bottom:8px;'>" if brand.get('logo_url') else ""}
                    <div style="color:#C9A45C;font-size:18px;font-weight:700;">{brand.get('app_name','')}</div>
                    </td></tr>
                    <tr><td style="padding:28px 24px;color:#172331;">
                    <h2 style="margin:0 0 12px;color:#10243A;">New announcement</h2>
                    <p style="font-size:16px;font-weight:600;color:#C9A45C;">{title}</p>
                    <p style="line-height:1.6;">{body_txt}</p>
                    {"<p><img src='"+section.image_url+"' style='max-width:100%;border-radius:8px;'></p>" if section.image_url else ""}
                    <p style="margin-top:16px;"><a href="{brand.get('website') or '#'}" style="color:#C9A45C;">Visit website</a></p>
                    </td></tr>
                    <tr><td style="background:#081D33;padding:16px 24px;color:rgba(255,255,255,0.85);font-size:13px;">
                    {brand.get('app_name','')} · {brand.get('phone','')} · {brand.get('email','')}
                    </td></tr></table></td></tr></table></body></html>"""
                sent = set()
                users = Customer.query.filter_by(is_active=True, email_notify=True).all()
                for u in users:
                    if not u.email:
                        continue
                    send_email(u.email, f"[SR] {title}", html_base, template_key="announcement")
                    sent.add(u.email.lower())
                from app.models import NewsletterSubscriber
                for sub in NewsletterSubscriber.query.filter_by(is_active=True).all():
                    if sub.email and sub.email.lower() not in sent:
                        send_email(sub.email, f"[SR] {title}", html_base, template_key="announcement_newsletter")
                        sent.add(sub.email.lower())
                try:
                    from app.services.push_service import notify_users_push
                    body = (section.subtitle_en or section.subtitle_ne or section.content_en or section.content_ne or "")[:120]
                    notify_users_push(title, body or "New announcement from SR All Service Hub", "/")
                except Exception as _pe:
                    from flask import current_app
                    current_app.logger.warning("push announce: %s", _pe)
            except Exception as e:
                from flask import current_app
                current_app.logger.exception("Announcement notify failed: %s", e)
        flash("Section saved", "success")
        return redirect(url_for("admin.homepage"))
    return render_template("admin/homepage_edit.html", section=section)


# ─── Pages (CMS) ────────────────────────────────────────────

@admin_bp.route("/pages")
@login_required
def pages():
    items = Page.query.order_by(Page.slug).all()
    return render_template("admin/pages.html", pages=items)


@admin_bp.route("/pages/<int:id>", methods=["GET", "POST"])
@login_required
def page_edit(id):
    page = Page.query.get_or_404(id)
    if request.method == "POST":
        page.title_ne = request.form.get("title_ne", "")
        page.title_en = request.form.get("title_en", "")
        page.content_ne = request.form.get("content_ne", "")
        page.content_en = request.form.get("content_en", "")
        page.meta_title_ne = request.form.get("meta_title_ne", "")
        page.meta_title_en = request.form.get("meta_title_en", "")
        page.meta_description_ne = request.form.get("meta_description_ne", "")
        page.meta_description_en = request.form.get("meta_description_en", "")
        page.is_published = request.form.get("is_published") == "on"
        db.session.commit()
        flash("Page saved", "success")
        return redirect(url_for("admin.pages"))
    return render_template("admin/page_edit.html", page=page)


# ─── Services (CMS) ─────────────────────────────────────────

@admin_bp.route("/services")
@login_required
def services():
    categories = ServiceCategory.query.order_by(ServiceCategory.sort_order).all()
    services = Service.query.order_by(Service.sort_order).all()
    return render_template("admin/services.html", categories=categories, services=services)




@admin_bp.route("/categories/<int:id>", methods=["GET", "POST"])
@login_required
def category_edit(id):
    cat = ServiceCategory.query.get_or_404(id)
    if request.method == "POST":
        cat.name_ne = request.form.get("name_ne", "")
        cat.name_en = request.form.get("name_en", "")
        cat.description_ne = request.form.get("description_ne", "")
        cat.description_en = request.form.get("description_en", "")
        cat.image_url = request.form.get("image_url", "") or cat.image_url
        f = request.files.get("image_file")
        if f and f.filename:
            from app.services.storage_service import save_local_upload
            url = save_local_upload(f, subfolder="categories")
            if url:
                cat.image_url = url
        cat.is_published = request.form.get("is_published") == "on"
        cat.sort_order = int(request.form.get("sort_order") or 0)
        db.session.commit()
        flash("Category saved", "success")
        return redirect(url_for("admin.services"))
    return render_template("admin/category_edit.html", category=cat)


@admin_bp.route("/services/<int:id>", methods=["GET", "POST"])
@login_required
def service_edit(id):
    service = Service.query.get_or_404(id)
    categories = ServiceCategory.query.order_by(ServiceCategory.sort_order).all()
    if request.method == "POST":
        service.name_ne = request.form.get("name_ne", "")
        service.name_en = request.form.get("name_en", "")
        service.short_desc_ne = request.form.get("short_desc_ne", "")
        service.short_desc_en = request.form.get("short_desc_en", "")
        service.description_ne = request.form.get("description_ne", "")
        service.description_en = request.form.get("description_en", "")
        service.requirements_ne = request.form.get("requirements_ne", "")
        service.requirements_en = request.form.get("requirements_en", "")
        service.pricing_info_ne = request.form.get("pricing_info_ne", "")
        service.pricing_info_en = request.form.get("pricing_info_en", "")
        _p = request.form.get("price_npr", "").strip()
        service.price_npr = float(_p) if _p else None
        service.image_url = request.form.get("image_url", "")
        service.category_id = int(request.form.get("category_id") or service.category_id)
        service.is_featured = request.form.get("is_featured") == "on"
        service.is_published = request.form.get("is_published") == "on"
        service.requires_documents = request.form.get("requires_documents") == "on"
        service.sort_order = int(request.form.get("sort_order") or 0)
        db.session.commit()
        flash("Service saved", "success")
        return redirect(url_for("admin.services"))
    return render_template("admin/service_edit.html", service=service, categories=categories)



@admin_bp.route("/services/new", methods=["GET", "POST"])
@login_required
def service_new():
    categories = ServiceCategory.query.order_by(ServiceCategory.sort_order).all()
    if request.method == "POST":
        from werkzeug.utils import secure_filename
        slug = request.form.get("slug", "").strip().lower().replace(" ", "-")
        if not slug:
            flash("Slug is required", "error")
            return redirect(url_for("admin.service_new"))
        if Service.query.filter_by(slug=slug).first():
            flash("Slug already exists", "error")
            return redirect(url_for("admin.service_new"))
        service = Service(
            slug=slug,
            name_ne=request.form.get("name_ne", ""),
            name_en=request.form.get("name_en", ""),
            short_desc_ne=request.form.get("short_desc_ne", ""),
            short_desc_en=request.form.get("short_desc_en", ""),
            description_ne=request.form.get("description_ne", ""),
            description_en=request.form.get("description_en", ""),
            category_id=int(request.form.get("category_id")),
            is_published=request.form.get("is_published") == "on",
            is_featured=request.form.get("is_featured") == "on",
            requires_documents=request.form.get("requires_documents") == "on",
        )
        db.session.add(service)
        db.session.commit()
        flash("Service created", "success")
        return redirect(url_for("admin.services"))
    return render_template("admin/service_edit.html", service=None, categories=categories)



# ─── FAQs ───────────────────────────────────────────────────

@admin_bp.route("/faqs")
@login_required
def faqs():
    items = FAQ.query.order_by(FAQ.sort_order).all()
    return render_template("admin/faqs.html", faqs=items)


@admin_bp.route("/faqs/<int:id>", methods=["GET", "POST"])
@login_required
def faq_edit(id):
    faq = FAQ.query.get_or_404(id)
    if request.method == "POST":
        faq.question_ne = request.form.get("question_ne", "")
        faq.question_en = request.form.get("question_en", "")
        faq.answer_ne = request.form.get("answer_ne", "")
        faq.answer_en = request.form.get("answer_en", "")
        faq.is_published = request.form.get("is_published") == "on"
        faq.is_featured = request.form.get("is_featured") == "on"
        faq.sort_order = int(request.form.get("sort_order") or 0)
        db.session.commit()
        flash("FAQ saved", "success")
        return redirect(url_for("admin.faqs"))
    return render_template("admin/faq_edit.html", faq=faq)


@admin_bp.route("/faqs/new", methods=["GET", "POST"])
@login_required
def faq_new():
    if request.method == "POST":
        faq = FAQ(
            question_ne=request.form.get("question_ne", ""),
            question_en=request.form.get("question_en", ""),
            answer_ne=request.form.get("answer_ne", ""),
            answer_en=request.form.get("answer_en", ""),
            is_published=request.form.get("is_published") == "on",
            is_featured=request.form.get("is_featured") == "on",
            sort_order=int(request.form.get("sort_order") or 0),
        )
        db.session.add(faq)
        db.session.commit()
        flash("FAQ created", "success")
        return redirect(url_for("admin.faqs"))
    return render_template("admin/faq_edit.html", faq=None)


# ─── Site Settings ──────────────────────────────────────────

@admin_bp.route("/settings", methods=["GET", "POST"])
@login_required
def settings():
    from app.services.storage_service import save_local_upload

    text_keys = [
        "company_name", "tagline", "email", "facebook", "instagram", "tiktok", "youtube", "linkedin", "twitter", "hours", "map_embed_html", "whatsapp",
        "footer_intro_ne", "footer_intro_en",
        "logo_url", "favicon_url", "bam_logo_url", "hero_bg_url",
        "popup_title_ne", "popup_title_en", "popup_body_ne", "popup_body_en", "popup_image_url",
    ]
    if request.method == "POST":
        for key in text_keys:
            val_ne = request.form.get(f"{key}_ne", request.form.get(key, ""))
            val_en = request.form.get(f"{key}_en", request.form.get(key, ""))
            s = SiteSetting.query.filter_by(key=key).first()
            if not s:
                s = SiteSetting(key=key)
                db.session.add(s)
            # Always persist text (allow clear/empty). File-only keys skip empty overwrite.
            if key in ("logo_url", "favicon_url", "bam_logo_url", "hero_bg_url", "popup_image_url"):
                if val_ne:
                    s.value_ne = val_ne
                if val_en:
                    s.value_en = val_en
            else:
                s.value_ne = val_ne if val_ne is not None else ""
                s.value_en = val_en if val_en is not None else (s.value_en or "")

        # File uploads override URL fields
        for field, key in [
            ("logo_file", "logo_url"),
            ("favicon_file", "favicon_url"),
            ("bam_logo_file", "bam_logo_url"),
            ("hero_bg_file", "hero_bg_url"),
        ]:
            f = request.files.get(field)
            if f and f.filename:
                url = save_local_upload(f, subfolder="branding")
                if url:
                    s = SiteSetting.query.filter_by(key=key).first()
                    if not s:
                        s = SiteSetting(key=key)
                        db.session.add(s)
                    s.value_ne = url

        # Popup toggle
        pe = SiteSetting.query.filter_by(key="popup_enabled").first()
        if not pe:
            pe = SiteSetting(key="popup_enabled")
            db.session.add(pe)
        pe.value_ne = "1" if request.form.get("popup_enabled") == "on" else "0"
        pf = request.files.get("popup_image_file")
        upload_fail = False
        if pf and pf.filename:
            from app.services.storage_service import save_local_upload
            purl = save_local_upload(pf, subfolder="branding")
            if purl:
                ps = SiteSetting.query.filter_by(key="popup_image_url").first()
                if not ps:
                    ps = SiteSetting(key="popup_image_url")
                    db.session.add(ps)
                ps.value_ne = purl
                ps.value_en = purl
            else:
                upload_fail = True

        try:
            db.session.commit()
            if upload_fail:
                flash("Settings saved, but image upload failed. Set Cloudinary env vars on Vercel.", "error")
            else:
                flash("Settings saved", "success")
        except Exception as e:
            db.session.rollback()
            flash(f"Save failed: {e}", "error")
        return redirect(url_for("admin.settings"))

    settings_map = {s.key: s for s in SiteSetting.query.all()}
    return render_template("admin/settings.html", settings=settings_map, keys=text_keys)



# ─── Branches ───────────────────────────────────────────────

@admin_bp.route("/branches")
@login_required
def branches():
    items = Branch.query.order_by(Branch.sort_order).all()
    return render_template("admin/branches.html", branches=items)


@admin_bp.route("/branches/<int:id>", methods=["GET", "POST"])
@login_required
def branch_edit(id):
    branch = Branch.query.get_or_404(id)
    if request.method == "POST":
        branch.name_ne = request.form.get("name_ne", "")
        branch.name_en = request.form.get("name_en", "")
        branch.address_ne = request.form.get("address_ne", "")
        branch.address_en = request.form.get("address_en", "")
        branch.phone = request.form.get("phone", "")
        branch.email = request.form.get("email", "")
        branch.whatsapp = request.form.get("whatsapp", "")
        branch.hours_ne = request.form.get("hours_ne", "")
        branch.hours_en = request.form.get("hours_en", "")
        branch.is_published = request.form.get("is_published") == "on"
        branch.sort_order = int(request.form.get("sort_order") or 0)
        db.session.commit()
        flash("Branch saved", "success")
        return redirect(url_for("admin.branches"))
    return render_template("admin/branch_edit.html", branch=branch)


# ─── Team Members ───────────────────────────────────────────

@admin_bp.route("/team")
@login_required
def team_members():
    items = TeamMember.query.order_by(TeamMember.sort_order).all()
    return render_template("admin/team.html", members=items)


@admin_bp.route("/team/<int:id>", methods=["GET", "POST"])
@login_required
def team_edit(id):
    from app.services.storage_service import save_local_upload
    member = TeamMember.query.get_or_404(id)
    if request.method == "POST":
        member.name = request.form.get("name", "")
        member.position_ne = request.form.get("position_ne", "")
        member.position_en = request.form.get("position_en", "")
        member.phone = request.form.get("phone", "")
        member.video_url = request.form.get("video_url", "")
        member.bio_ne = request.form.get("bio_ne", "")
        member.bio_en = request.form.get("bio_en", "")
        member.sort_order = int(request.form.get("sort_order") or 0)
        member.is_published = request.form.get("is_published") == "on"
        member.is_collaborator = request.form.get("is_collaborator") == "on"
        if request.form.get("image_url"):
            member.image_url = request.form.get("image_url")
        f = request.files.get("image_file")
        if f and f.filename:
            url = save_local_upload(f, subfolder="team")
            if url:
                member.image_url = url
        db.session.commit()
        flash("Team member saved", "success")
        return redirect(url_for("admin.team_members"))
    return render_template("admin/team_edit.html", member=member)


@admin_bp.route("/team/new", methods=["GET", "POST"])
@login_required
def team_new():
    from app.services.storage_service import save_local_upload
    if request.method == "POST":
        member = TeamMember(
            name=request.form.get("name", ""),
            position_ne=request.form.get("position_ne", ""),
            position_en=request.form.get("position_en", ""),
            phone=request.form.get("phone", ""),
            video_url=request.form.get("video_url", ""),
            bio_ne=request.form.get("bio_ne", ""),
            bio_en=request.form.get("bio_en", ""),
            sort_order=int(request.form.get("sort_order") or 0),
            is_published=request.form.get("is_published") == "on",
            is_collaborator=request.form.get("is_collaborator") == "on",
        )
        if request.form.get("image_url"):
            member.image_url = request.form.get("image_url")
        f = request.files.get("image_file")
        if f and f.filename:
            url = save_local_upload(f, subfolder="team")
            if url:
                member.image_url = url
        db.session.add(member)
        db.session.commit()
        flash("Team member created", "success")
        return redirect(url_for("admin.team_members"))
    return render_template("admin/team_edit.html", member=None)


# ─── Packages ───────────────────────────────────────────────

@admin_bp.route("/packages")
@login_required
def packages_admin():
    items = Package.query.order_by(Package.sort_order).all()
    return render_template("admin/packages.html", packages=items)


@admin_bp.route("/packages/<int:id>", methods=["GET", "POST"])
@login_required
def package_edit(id):
    from app.services.storage_service import save_local_upload
    pkg = Package.query.get_or_404(id)
    if request.method == "POST":
        pkg.title_ne = request.form.get("title_ne", "")
        pkg.title_en = request.form.get("title_en", "")
        pkg.short_desc_ne = request.form.get("short_desc_ne", "")
        pkg.short_desc_en = request.form.get("short_desc_en", "")
        pkg.description_ne = request.form.get("description_ne", "")
        pkg.description_en = request.form.get("description_en", "")
        pkg.price_from = request.form.get("price_from") or None
        _mp = request.form.get("min_payment", "").strip()
        pkg.min_payment = float(_mp) if _mp else None
        pkg.currency = request.form.get("currency") or "NPR"
        pkg.duration_days = int(request.form.get("duration_days") or 0) or None
        pkg.is_featured = request.form.get("is_featured") == "on"
        pkg.is_published = request.form.get("is_published") == "on"
        pkg.sort_order = int(request.form.get("sort_order") or 0)
        if request.form.get("image_url"):
            pkg.image_url = request.form.get("image_url")
        f = request.files.get("image_file")
        if f and f.filename:
            url = save_local_upload(f, subfolder="packages")
            if url:
                pkg.image_url = url
        db.session.commit()
        flash("Package saved", "success")
        return redirect(url_for("admin.packages_admin"))
    return render_template("admin/package_edit.html", package=pkg)


@admin_bp.route("/packages/new", methods=["GET", "POST"])
@login_required
def package_new():
    from app.services.storage_service import save_local_upload
    if request.method == "POST":
        slug = request.form.get("slug", "").strip().lower().replace(" ", "-")
        if not slug or Package.query.filter_by(slug=slug).first():
            flash("Valid unique slug required", "error")
            return redirect(url_for("admin.package_new"))
        pkg = Package(
            slug=slug,
            title_ne=request.form.get("title_ne", ""),
            title_en=request.form.get("title_en", ""),
            short_desc_ne=request.form.get("short_desc_ne", ""),
            short_desc_en=request.form.get("short_desc_en", ""),
            description_ne=request.form.get("description_ne", ""),
            description_en=request.form.get("description_en", ""),
            price_from=request.form.get("price_from") or None,
            min_payment=(float(request.form.get("min_payment")) if request.form.get("min_payment") else None),
            currency=request.form.get("currency") or "NPR",
            duration_days=int(request.form.get("duration_days") or 0) or None,
            is_featured=request.form.get("is_featured") == "on",
            is_published=request.form.get("is_published") == "on",
            sort_order=int(request.form.get("sort_order") or 0),
        )
        f = request.files.get("image_file")
        if f and f.filename:
            url = save_local_upload(f, subfolder="packages")
            if url:
                pkg.image_url = url
        elif request.form.get("image_url"):
            pkg.image_url = request.form.get("image_url")
        db.session.add(pkg)
        db.session.commit()
        flash("Package created", "success")
        return redirect(url_for("admin.packages_admin"))
    return render_template("admin/package_edit.html", package=None)


@admin_bp.route("/packages/<int:id>/delete", methods=["POST"])
@login_required
def package_delete(id):
    pkg = Package.query.get_or_404(id)
    title = pkg.title_en or pkg.title_ne or pkg.slug
    try:
        # Detach from booking_details so FK does not block
        from app.models import BookingDetail
        for det in BookingDetail.query.filter_by(package_id=pkg.id).all():
            det.package_id = None
        db.session.delete(pkg)
        db.session.commit()
        flash(f"Package “{title}” deleted", "success")
    except Exception as e:
        db.session.rollback()
        flash(f"Could not delete package: {e}", "error")
    return redirect(url_for("admin.packages_admin"))


# ─── Destinations ───────────────────────────────────────────

@admin_bp.route("/destinations")
@login_required
def destinations_admin():
    items = Destination.query.order_by(Destination.sort_order).all()
    return render_template("admin/destinations.html", destinations=items)


@admin_bp.route("/destinations/<int:id>", methods=["GET", "POST"])
@login_required
def destination_edit(id):
    from app.services.storage_service import save_local_upload
    item = Destination.query.get_or_404(id)
    if request.method == "POST":
        item.name_ne = request.form.get("name_ne", "")
        item.name_en = request.form.get("name_en", "")
        item.description_ne = request.form.get("description_ne", "")
        item.description_en = request.form.get("description_en", "")
        item.country = request.form.get("country", "")
        item.is_featured = request.form.get("is_featured") == "on"
        item.is_published = request.form.get("is_published") == "on"
        item.sort_order = int(request.form.get("sort_order") or 0)
        if request.form.get("image_url"):
            item.image_url = request.form.get("image_url")
        f = request.files.get("image_file")
        if f and f.filename:
            url = save_local_upload(f, subfolder="destinations")
            if url:
                item.image_url = url
        db.session.commit()
        flash("Destination saved", "success")
        return redirect(url_for("admin.destinations_admin"))
    return render_template("admin/destination_edit.html", destination=item)


@admin_bp.route("/destinations/new", methods=["GET", "POST"])
@login_required
def destination_new():
    from app.services.storage_service import save_local_upload
    if request.method == "POST":
        slug = request.form.get("slug", "").strip().lower().replace(" ", "-")
        if not slug or Destination.query.filter_by(slug=slug).first():
            flash("Valid unique slug required", "error")
            return redirect(url_for("admin.destination_new"))
        item = Destination(
            slug=slug,
            name_ne=request.form.get("name_ne", ""),
            name_en=request.form.get("name_en", ""),
            description_ne=request.form.get("description_ne", ""),
            description_en=request.form.get("description_en", ""),
            country=request.form.get("country", ""),
            is_featured=request.form.get("is_featured") == "on",
            is_published=request.form.get("is_published") == "on",
            sort_order=int(request.form.get("sort_order") or 0),
        )
        f = request.files.get("image_file")
        if f and f.filename:
            url = save_local_upload(f, subfolder="destinations")
            if url:
                item.image_url = url
        elif request.form.get("image_url"):
            item.image_url = request.form.get("image_url")
        db.session.add(item)
        db.session.commit()
        flash("Destination created", "success")
        return redirect(url_for("admin.destinations_admin"))
    return render_template("admin/destination_edit.html", destination=None)


@admin_bp.route("/users")
@login_required
def users():
    from app.models import Customer
    items = Customer.query.order_by(Customer.created_at.desc()).all()
    return render_template("admin/users.html", users=items)



@admin_bp.route("/users/<int:id>")
@login_required
def user_view(id):
    from app.models import Customer, Booking
    user = Customer.query.get_or_404(id)
    bookings = Booking.query.filter_by(customer_id=user.id).order_by(Booking.submitted_at.desc()).limit(20).all()
    return render_template("admin/user_view.html", user=user, bookings=bookings)


@admin_bp.route("/users/<int:id>/edit", methods=["GET", "POST"])
@login_required
def user_edit(id):
    from app.models import Customer
    user = Customer.query.get_or_404(id)
    if request.method == "POST":
        user.full_name = request.form.get("full_name", user.full_name).strip()
        user.email = request.form.get("email", "").strip().lower() or user.email
        user.mobile = request.form.get("mobile", "").strip() or None
        user.nationality = request.form.get("nationality", "").strip() or None
        user.notes = request.form.get("notes", "").strip() or None
        user.is_active = request.form.get("is_active") == "on"
        user.email_notify = request.form.get("email_notify") == "on"
        user.push_enabled = request.form.get("push_enabled") == "on"
        db.session.commit()
        flash("User updated", "success")
        return redirect(url_for("admin.user_view", id=user.id))
    return render_template("admin/user_edit.html", user=user)


@admin_bp.route("/users/<int:id>/delete", methods=["POST"])
@login_required
def user_delete(id):
    from app.models import Customer, Booking
    user = Customer.query.get_or_404(id)
    try:
        # Detach bookings so FK does not block delete
        Booking.query.filter_by(customer_id=user.id).update({"customer_id": None})
        db.session.delete(user)
        db.session.commit()
        flash("User deleted", "success")
    except Exception as e:
        db.session.rollback()
        flash(f"Could not delete user: {e}", "error")
    return redirect(url_for("admin.users"))



@admin_bp.route("/admins", methods=["GET", "POST"])
@login_required
def admin_accounts():
    """List / add admin emails (for OAuth whitelist + password accounts)."""
    from app.models import Admin
    from werkzeug.security import generate_password_hash
    if request.method == "POST":
        email = request.form.get("email", "").strip().lower()
        name = request.form.get("full_name", "").strip() or "Admin"
        password = request.form.get("password", "").strip()
        if not email:
            flash("Email required", "error")
        elif Admin.query.filter_by(email=email).first():
            flash("Admin already exists", "error")
        else:
            a = Admin(email=email, full_name=name, role="admin")
            if password:
                a.set_password(password)
            else:
                # random unusable password until set
                a.set_password(generate_password_hash(email)[:24])
            db.session.add(a)
            db.session.commit()
            flash("Admin email added — can use Google/Facebook login with this email", "success")
        return redirect(url_for("admin.admin_accounts"))
    items = Admin.query.order_by(Admin.id).all()
    return render_template("admin/admins.html", admins=items)



@admin_bp.route("/reviews")
@login_required
def reviews():
    from app.models import Testimonial
    items = Testimonial.query.order_by(Testimonial.id.desc()).all()
    return render_template("admin/reviews.html", items=items)


@admin_bp.route("/reviews/<int:id>/toggle", methods=["POST"])
@login_required
def review_toggle(id):
    from app.models import Testimonial
    row = Testimonial.query.get_or_404(id)
    row.is_published = not row.is_published
    db.session.commit()
    flash("Review " + ("published" if row.is_published else "disabled"), "success")
    return redirect(url_for("admin.reviews"))


@admin_bp.route("/reviews/<int:id>/delete", methods=["POST"])
@login_required
def review_delete(id):
    from app.models import Testimonial
    row = Testimonial.query.get_or_404(id)
    db.session.delete(row)
    db.session.commit()
    flash("Review deleted", "success")
    return redirect(url_for("admin.reviews"))
