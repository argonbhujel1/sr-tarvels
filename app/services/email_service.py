from flask import current_app, render_template
from flask_mail import Message
from extensions import mail, db
from app.models import EmailLog, EmailTemplate, SiteSetting
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


def _brand_context() -> dict:
    def s(key, default=""):
        row = SiteSetting.query.filter_by(key=key).first()
        if not row:
            return default
        return row.value_ne or row.value_en or default

    return {
        "app_name": current_app.config.get("APP_NAME", "SR All Service Hub Nepal"),
        "tagline": s("tagline", "एक प्लेटफर्म। हरेक सेवा। हरेक यात्रा।"),
        "logo_url": s("logo_url"),
        "phone": s("phone", "+977 9713799042"),
        "phone2": s("phone2", "+977 9851440623"),
        "email": s("email", "srallservicenepal@gmail.com"),
        "address": s("address", "Urlabari, Koshi Province, Nepal"),
        "hours": s("hours", "बिहान ७:०० – बेलुका ९:००, सोमबारदेखि आइतबारसम्म"),
        "website": current_app.config.get("APP_URL") or "https://srtravels.argan.com.np",
    }


def wrap_email_html(inner_html: str, email_reason: str = "", **extra) -> str:
    """Wrap any body HTML in the decorative brand shell (single header + footer)."""
    ctx = _brand_context()
    ctx.update(extra)
    ctx["email_reason"] = email_reason
    # Use a simple string layout to avoid Jinja block issues
    logo = ctx.get("logo_url") or ""
    logo_html = f'<img src="{logo}" alt="" style="max-height:52px;width:auto;margin-bottom:10px;border-radius:6px;">' if logo else ""
    website = ctx.get("website") or ""
    return f'''<!DOCTYPE html>
<html><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"></head>
<body style="margin:0;padding:0;background:#F6F8FA;font-family:Arial,Helvetica,sans-serif;color:#172331;">
<table role="presentation" width="100%" cellspacing="0" cellpadding="0" style="background:#F6F8FA;padding:28px 12px;">
<tr><td align="center">
<table role="presentation" width="600" cellspacing="0" cellpadding="0" style="max-width:600px;width:100%;background:#ffffff;border-radius:14px;overflow:hidden;border:1px solid #e5e9ef;">
<tr><td style="background:linear-gradient(135deg,#081D33,#10243A);padding:22px 24px;text-align:center;">
{logo_html}
<div style="color:#FFFFFF;font-size:18px;font-weight:700;">{ctx.get("app_name","")}</div>
<div style="color:#C9A45C;font-size:13px;margin-top:6px;">{ctx.get("tagline","")}</div>
</td></tr>
<tr><td style="padding:28px 26px;">
{f'<p style="margin:0 0 10px;font-size:12px;color:#C9A45C;font-weight:700;letter-spacing:0.04em;text-transform:uppercase;">{email_reason}</p>' if email_reason else ""}
{inner_html}
</td></tr>
<tr><td style="background:#081D33;padding:20px 26px;color:rgba(255,255,255,0.9);font-size:13px;line-height:1.75;">
<div style="color:#C9A45C;font-weight:700;margin-bottom:8px;">{ctx.get("app_name","")}</div>
<div>📞 {ctx.get("phone","")} · {ctx.get("phone2","")}</div>
<div>✉️ {ctx.get("email","")}</div>
<div>📍 {ctx.get("address","")}</div>
<div>🕒 {ctx.get("hours","")}</div>
{f'<div style="margin-top:8px;"><a href="{website}" style="color:#C9A45C;text-decoration:none;">{website}</a></div>' if website else ""}
<div style="margin-top:14px;font-size:11px;color:rgba(255,255,255,0.5);">
Designed &amp; Engineered by <a href="https://bamstudio.argan.com.np" style="color:#C9A45C;text-decoration:underline;" target="_blank">BAM Studio</a>
</div>
</td></tr>
</table>
</td></tr></table>
</body></html>'''


def send_email(
    to: str,
    subject: str,
    html_body: str,
    *,
    template_key: str | None = None,
    booking_id: int | None = None,
    auto_wrap: bool = True,
    email_reason: str = "",
) -> bool:
    """Send HTML email and log result. Returns True on success."""
    if not to:
        return False
    # If body is not already a full document, wrap once
    body = html_body or ""
    if auto_wrap and body and "<html" not in body.lower():
        body = wrap_email_html(body, email_reason=email_reason)

    log = EmailLog(
        template_key=template_key,
        to_email=to,
        subject=subject,
        status="pending",
        booking_id=booking_id,
    )
    db.session.add(log)
    db.session.commit()

    try:
        msg = Message(
            subject=subject,
            recipients=[to],
            html=body,
            sender=current_app.config.get("MAIL_DEFAULT_SENDER"),
            reply_to=current_app.config.get("MAIL_REPLY_TO"),
        )
        mail.send(msg)
        log.status = "sent"
        log.sent_at = datetime.utcnow()
        db.session.commit()
        return True
    except Exception as e:
        logger.exception("Email send failed")
        log.status = "failed"
        log.error_message = str(e)[:500]
        log.retry_count = (log.retry_count or 0) + 1
        db.session.commit()
        return False


def render_and_send_template(
    template_key: str,
    to: str,
    lang: str = "ne",
    context: dict | None = None,
    booking_id: int | None = None,
) -> bool:
    """Prefer filesystem template; fall back to DB body; always one decorative shell."""
    context = dict(context or {})
    brand = _brand_context()
    context.update(brand)

    subject = None
    inner = None

    # 1) Filesystem template (extends base or stands alone)
    try:
        full = render_template(f"emails/{template_key}.html", lang=lang, **context)
        if full and full.strip():
            # Already decorative if it includes full html from base
            if "<html" in full.lower():
                subject = context.get("email_subject") or f"{brand.get('app_name')} — update"
                return send_email(to, subject, full, template_key=template_key, booking_id=booking_id, auto_wrap=False)
            inner = full
    except Exception as e:
        logger.info("No file template %s: %s", template_key, e)

    # 2) DB template
    tpl = EmailTemplate.query.filter_by(key=template_key, is_enabled=True).first()
    if tpl:
        subject = (tpl.subject_ne if lang == "ne" else tpl.subject_en) or subject
        body = (tpl.body_ne if lang == "ne" else tpl.body_en) or ""
        for k, v in context.items():
            body = body.replace("{{" + k + "}}", str(v or ""))
            if subject:
                subject = subject.replace("{{" + k + "}}", str(v or ""))
        if body.strip():
            inner = body

    if not inner or not str(inner).strip():
        return False

    if not subject:
        subject = f"[{brand.get('app_name')}] Notification"

    reason = context.get("email_reason") or ""
    if "<html" in str(inner).lower():
        return send_email(to, subject, inner, template_key=template_key, booking_id=booking_id, auto_wrap=False)
    return send_email(
        to, subject, inner, template_key=template_key, booking_id=booking_id, auto_wrap=True, email_reason=reason
    )


def send_contact_emails(msg_obj, lang: str = "ne") -> None:
    brand = _brand_context()
    admin_to = brand.get("email") or current_app.config.get("MAIL_USERNAME") or current_app.config.get("ADMIN_EMAIL")
    ctx = {
        **brand,
        "name": msg_obj.name,
        "email_from": msg_obj.email or "—",
        "mobile": msg_obj.mobile or "—",
        "subject": msg_obj.subject or "Contact form",
        "message": msg_obj.message,
        "lang": lang,
    }
    if admin_to:
        try:
            html = render_template("emails/contact_admin.html", email_reason="Contact form · Admin alert", **ctx)
            send_email(
                admin_to,
                f"[Contact] {msg_obj.subject or 'New message'} — {msg_obj.name}",
                html,
                template_key="contact_admin",
                auto_wrap=False,
            )
        except Exception as e:
            logger.exception("Contact admin email failed: %s", e)

    if msg_obj.email:
        try:
            html = render_template("emails/contact_user.html", email_reason="Contact confirmation · सन्देश पुष्टि", **ctx)
            subj = "सन्देश प्राप्त भयो | Message received" if lang == "ne" else "We received your message"
            send_email(msg_obj.email, subj, html, template_key="contact_user", auto_wrap=False)
        except Exception as e:
            logger.exception("Contact user email failed: %s", e)


def send_welcome_email(user, lang: str = "ne", via_google: bool = False) -> bool:
    if not user.email:
        return False
    brand = _brand_context()
    html = render_template(
        "emails/welcome.html",
        name=user.full_name,
        lang=lang,
        via_google=via_google,
        email_reason="Account welcome · खाता स्वागत",
        **brand,
    )
    subject = f"स्वागत छ | Welcome to {brand.get('app_name', 'SR All Service Hub Nepal')}"
    return send_email(user.email, subject, html, template_key="welcome", auto_wrap=False)


def send_booking_received_email(booking, customer_name: str, customer_email: str, lang: str = "ne") -> bool:
    if not customer_email:
        return False
    brand = _brand_context()
    track_url = f"{brand.get('website', '').rstrip('/')}/booking/track?ref={booking.reference}"
    service_name = None
    try:
        if booking.service:
            service_name = booking.service.name_ne if lang == "ne" else booking.service.name_en
    except Exception:
        pass
    html = render_template(
        "emails/booking_received.html",
        name=customer_name,
        reference=booking.reference,
        service_name=service_name or getattr(booking, "booking_type", ""),
        status=getattr(booking, "status", "Pending"),
        track_url=track_url,
        lang=lang,
        email_reason="Booking received · बुकिङ प्राप्त",
        **brand,
    )
    subject = f"Booking {booking.reference} received | बुकिङ प्राप्त"
    return send_email(
        customer_email, subject, html, template_key="booking_received", booking_id=booking.id, auto_wrap=False
    )


def send_booking_status_email(booking, customer, new_status: str, note: str = "", lang: str = "ne") -> bool:
    if not customer or not getattr(customer, "email", None):
        return False
    brand = _brand_context()
    track_url = f"{brand.get('website', '').rstrip('/')}/booking/track?ref={booking.reference}"
    if getattr(customer, "mobile", None):
        track_url += f"&mobile={customer.mobile}"
    try:
        html = render_template(
            "emails/booking_status_update.html",
            name=customer.full_name,
            reference=booking.reference,
            status=new_status,
            note=note or "",
            track_url=track_url,
            lang=lang or "ne",
            email_reason="Booking update · बुकिङ अपडेट",
            **brand,
        )
        subject = f"Booking update – {booking.reference}"
        return send_email(
            customer.email, subject, html, template_key="booking_status_update", booking_id=booking.id, auto_wrap=False
        )
    except Exception as e:
        logger.exception("booking status template failed: %s", e)
        # inline fallback body
        note_html = (note or "").replace("\n", "<br>")
        inner = f"""
        <h2 style="margin:0 0 12px;color:#10243A;">Booking status update</h2>
        <p>Hello <strong>{customer.full_name}</strong>,</p>
        <p>Your booking <strong>{booking.reference}</strong> is now: <strong style="color:#C9A45C;">{new_status}</strong>.</p>
        {f'<p>{note_html}</p>' if note else ''}
        <p><a href="{track_url}" style="background:#10243A;color:#fff;padding:12px 24px;border-radius:8px;text-decoration:none;">Track booking</a></p>
        """
        html = wrap_email_html(inner, email_reason="Booking update · बुकिङ अपडेट")
        return send_email(
            customer.email,
            f"Booking update – {booking.reference}",
            html,
            template_key="booking_status_update",
            booking_id=booking.id,
            auto_wrap=False,
        )


