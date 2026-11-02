"""Customer authentication: register, login, Google OAuth."""
import os
from datetime import datetime
from urllib.parse import urlencode
from flask import (
    Blueprint, render_template, request, redirect, url_for, flash, g, session, current_app
)
from flask_login import login_user, logout_user, login_required, current_user
from extensions import db
from app.models import Customer

auth_bp = Blueprint("auth", __name__, url_prefix="/auth")


def _is_customer():
    return current_user.is_authenticated and isinstance(current_user, Customer)


def _generate_otp() -> str:
    import secrets
    return f"{secrets.randbelow(10**6):06d}"


def _send_register_otp(email: str, otp: str, name: str = "") -> bool:
    from app.services.email_service import send_email, wrap_email_html
    lang = session.get("lang") or getattr(g, "lang", "ne")
    if lang == "en":
        subject = "Your registration OTP – SR All Service Hub"
        inner = f"""
        <h2 style="margin:0 0 12px;color:#10243A;">Verify your email</h2>
        <p>Hello <strong>{name or 'there'}</strong>,</p>
        <p>Use this one-time code to complete registration. It expires in 15 minutes.</p>
        <p style="text-align:center;margin:24px 0;">
          <span style="display:inline-block;background:#F6F8FA;border:1px solid #e5e9ef;border-radius:10px;padding:14px 28px;font-size:28px;letter-spacing:0.35em;font-weight:700;color:#10243A;">{otp}</span>
        </p>
        <p style="color:#666;font-size:13px;">If you did not request this, ignore this email.</p>
        """
        reason = "Registration OTP"
    else:
        subject = "दर्ता OTP – SR All Service Hub"
        inner = f"""
        <h2 style="margin:0 0 12px;color:#10243A;">इमेल प्रमाणीकरण</h2>
        <p>नमस्ते <strong>{name or ''}</strong>,</p>
        <p>दर्ता पूरा गर्न यो एकपटकको कोड प्रयोग गर्नुहोस्। १५ मिनेटमा म्याद सकिन्छ।</p>
        <p style="text-align:center;margin:24px 0;">
          <span style="display:inline-block;background:#F6F8FA;border:1px solid #e5e9ef;border-radius:10px;padding:14px 28px;font-size:28px;letter-spacing:0.35em;font-weight:700;color:#10243A;">{otp}</span>
        </p>
        <p style="color:#666;font-size:13px;">यदि तपाईंले अनुरोध गर्नुभएको होइन भने यो इमेल बेवास्ता गर्नुहोस्।</p>
        """
        reason = "दर्ता OTP · Registration OTP"
    html = wrap_email_html(inner, email_reason=reason)
    return send_email(email, subject, html, template_key="register_otp", auto_wrap=False)


@auth_bp.route("/register", methods=["GET", "POST"])
def register():
    if _is_customer():
        return redirect(url_for("public.home"))
    if request.method == "POST":
        name = request.form.get("full_name", "").strip()
        email = request.form.get("email", "").strip().lower()
        mobile = request.form.get("mobile", "").strip()
        password = request.form.get("password", "")
        if not name or not email or not password:
            flash("Name, email and password required." if g.lang == "en" else "नाम, इमेल र पासवर्ड आवश्यक।", "error")
            return redirect(url_for("auth.register"))
        if len(password) < 6:
            flash("Password must be at least 6 characters." if g.lang == "en" else "पासवर्ड कम्तीमा ६ अक्षरको हुनुपर्छ।", "error")
            return redirect(url_for("auth.register"))
        if Customer.query.filter_by(email=email).first():
            flash("Email already registered." if g.lang == "en" else "यो इमेल पहिले नै दर्ता छ।", "error")
            return redirect(url_for("auth.register"))
        otp = _generate_otp()
        session["pending_register"] = {
            "full_name": name,
            "email": email,
            "mobile": mobile or None,
            "password": password,
            "otp": otp,
            "expires": (datetime.utcnow().timestamp() + 15 * 60),
        }
        try:
            ok = _send_register_otp(email, otp, name)
            if not ok:
                flash(
                    "Could not send OTP email. Check SMTP settings."
                    if g.lang == "en"
                    else "OTP इमेल पठाउन सकिएन। SMTP जाँच गर्नुहोस्।",
                    "error",
                )
                session.pop("pending_register", None)
                return redirect(url_for("auth.register"))
        except Exception as e:
            current_app.logger.exception("register OTP: %s", e)
            flash(
                "Could not send OTP email."
                if g.lang == "en"
                else "OTP इमेल पठाउन सकिएन।",
                "error",
            )
            session.pop("pending_register", None)
            return redirect(url_for("auth.register"))
        flash(
            "OTP sent to your email. Enter it to complete registration."
            if g.lang == "en"
            else "तपाईंको Gmail/इमेलमा OTP पठाइयो। दर्ता पूरा गर्न कोड हाल्नुहोस्।",
            "success",
        )
        return redirect(url_for("auth.verify_register_otp"))
    return render_template("auth/register.html")


@auth_bp.route("/register/verify-otp", methods=["GET", "POST"])
def verify_register_otp():
    if _is_customer():
        return redirect(url_for("public.home"))
    pending = session.get("pending_register")
    if not pending:
        flash(
            "No pending registration. Start again."
            if g.lang == "en"
            else "दर्ता सुरु भएको छैन। फेरि प्रयास गर्नुहोस्।",
            "error",
        )
        return redirect(url_for("auth.register"))
    if request.method == "POST":
        # Resend
        if request.form.get("action") == "resend":
            otp = _generate_otp()
            pending["otp"] = otp
            pending["expires"] = datetime.utcnow().timestamp() + 15 * 60
            session["pending_register"] = pending
            try:
                _send_register_otp(pending["email"], otp, pending.get("full_name") or "")
                flash("OTP resent." if g.lang == "en" else "OTP फेरि पठाइयो।", "success")
            except Exception as e:
                current_app.logger.warning("resend OTP: %s", e)
                flash("Could not resend OTP." if g.lang == "en" else "OTP पठाउन सकिएन।", "error")
            return redirect(url_for("auth.verify_register_otp"))

        code = (request.form.get("otp") or "").strip().replace(" ", "")
        expires = pending.get("expires") or 0
        if datetime.utcnow().timestamp() > expires:
            session.pop("pending_register", None)
            flash(
                "OTP expired. Register again."
                if g.lang == "en"
                else "OTP को म्याद सकियो। फेरि दर्ता गर्नुहोस्।",
                "error",
            )
            return redirect(url_for("auth.register"))
        if code != str(pending.get("otp")):
            flash("Invalid OTP." if g.lang == "en" else "OTP गलत छ।", "error")
            return redirect(url_for("auth.verify_register_otp"))
        if Customer.query.filter_by(email=pending["email"]).first():
            session.pop("pending_register", None)
            flash("Email already registered." if g.lang == "en" else "यो इमेल पहिले नै दर्ता छ।", "error")
            return redirect(url_for("auth.login"))
        user = Customer(
            full_name=pending["full_name"],
            email=pending["email"],
            mobile=pending.get("mobile") or None,
        )
        user.set_password(pending["password"])
        try:
            from app.services.geo_service import capture_login_geo
            capture_login_geo(user)
        except Exception:
            pass
        db.session.add(user)
        db.session.commit()
        session.pop("pending_register", None)
        try:
            from app.services.email_service import send_welcome_email
            send_welcome_email(user, lang=getattr(g, "lang", "ne"), via_google=False)
        except Exception as e:
            current_app.logger.warning("welcome email: %s", e)
        login_user(user, remember=True)
        flash("Account created." if g.lang == "en" else "खाता सिर्जना भयो।", "success")
        next_url = request.args.get("next") or session.pop("next_url", None) or url_for("public.home")
        return redirect(next_url)
    return render_template(
        "auth/verify_otp.html",
        email=pending.get("email"),
        masked_email=_mask_email(pending.get("email") or ""),
    )


def _mask_email(email: str) -> str:
    if not email or "@" not in email:
        return email or ""
    local, _, domain = email.partition("@")
    if len(local) <= 2:
        masked = local[0] + "*"
    else:
        masked = local[0] + "*" * (len(local) - 2) + local[-1]
    return f"{masked}@{domain}"


@auth_bp.route("/login", methods=["GET", "POST"])
def login():
    if _is_customer():
        return redirect(url_for("public.home"))
    if request.method == "POST":
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")
        user = Customer.query.filter_by(email=email).first()
        if not user or not user.check_password(password):
            flash("Invalid email or password." if g.lang == "en" else "इमेल वा पासवर्ड गलत।", "error")
            return redirect(url_for("auth.login"))
        if not user.is_active:
            flash("Account disabled." if g.lang == "en" else "खाता निष्क्रिय छ।", "error")
            return redirect(url_for("auth.login"))
        user.last_login = datetime.utcnow()
        try:
            from app.services.geo_service import capture_login_geo
            capture_login_geo(user)
        except Exception:
            pass
        db.session.commit()
        login_user(user, remember=True)
        next_url = request.args.get("next") or session.pop("next_url", None) or url_for("public.home")
        return redirect(next_url)
    return render_template("auth/login.html")


@auth_bp.route("/logout")
def logout():
    logout_user()
    return redirect(url_for("public.home"))


@auth_bp.route("/google")
def google_login():
    client_id = current_app.config.get("GOOGLE_CLIENT_ID") or os.getenv("GOOGLE_CLIENT_ID")
    if not client_id:
        flash(
            "Google login is not configured. Use email/password."
            if g.lang == "en"
            else "Google लगइन सेट छैन। इमेल/पासवर्ड प्रयोग गर्नुहोस्।",
            "error",
        )
        return redirect(url_for("auth.login"))
    redirect_uri = url_for("auth.google_callback", _external=True)
    params = {
        "client_id": client_id,
        "redirect_uri": redirect_uri,
        "response_type": "code",
        # Basic scopes (reliable). Phone is requested via People API when available.
        "scope": "openid email profile",
        "access_type": "online",
        "prompt": "select_account",
    }
    return redirect("https://accounts.google.com/o/oauth2/v2/auth?" + urlencode(params))


@auth_bp.route("/google/callback")
def google_callback():
    import requests as http_requests

    code = request.args.get("code")
    if not code:
        flash("Google login cancelled.", "error")
        return redirect(url_for("auth.login"))

    client_id = current_app.config.get("GOOGLE_CLIENT_ID") or os.getenv("GOOGLE_CLIENT_ID")
    client_secret = current_app.config.get("GOOGLE_CLIENT_SECRET") or os.getenv("GOOGLE_CLIENT_SECRET")
    redirect_uri = url_for("auth.google_callback", _external=True)

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
        data = info.json()
    except Exception as e:
        current_app.logger.exception("Google OAuth failed: %s", e)
        flash("Google login failed." if g.lang == "en" else "Google लगइन असफल।", "error")
        return redirect(url_for("auth.login"))

    google_id = data.get("sub")
    email = (data.get("email") or "").lower()
    name = data.get("name") or email.split("@")[0]
    picture = data.get("picture")  # Google profile photo URL

    # Try People API for phone numbers (only if scope was granted)
    phone = None
    try:
        people = http_requests.get(
            "https://people.googleapis.com/v1/people/me",
            params={"personFields": "phoneNumbers,names,photos,emailAddresses"},
            headers={"Authorization": f"Bearer {tokens['access_token']}"},
            timeout=10,
        )
        if people.status_code == 200:
            pdata = people.json()
            nums = pdata.get("phoneNumbers") or []
            if nums:
                phone = (nums[0].get("value") or "").strip() or None
            if not picture:
                photos = pdata.get("photos") or []
                if photos:
                    picture = (photos[0].get("url") or "").strip() or None
    except Exception as e:
        current_app.logger.info("Google People phone fetch skipped: %s", e)

    user = Customer.query.filter_by(google_id=google_id).first()
    if not user and email:
        user = Customer.query.filter_by(email=email).first()
    is_new = False
    if not user:
        user = Customer(
            full_name=name,
            email=email or None,
            google_id=google_id,
            mobile=phone,
            avatar_url=picture or None,
        )
        db.session.add(user)
        is_new = True
    else:
        user.google_id = google_id
        if name and not user.full_name:
            user.full_name = name
        if picture:
            user.avatar_url = picture
        if phone and not user.mobile:
            user.mobile = phone
    user.last_login = datetime.utcnow()
    try:
        from app.services.geo_service import capture_login_geo
        capture_login_geo(user)
    except Exception:
        pass
    db.session.commit()
    if is_new:
        try:
            from app.services.email_service import send_welcome_email
            send_welcome_email(user, lang=session.get("lang", "ne"), via_google=True)
        except Exception as e:
            current_app.logger.warning("welcome email google: %s", e)
    login_user(user, remember=True)
    next_url = session.pop("next_url", None) or url_for("public.home")
    if not user.mobile:
        flash(
            "Please add your mobile number in profile."
            if session.get("lang") == "en"
            else "कृपया प्रोफाइलमा मोबाइल नम्बर थप्नुहोस्।",
            "info",
        )
        if not session.get("next_url"):
            next_url = url_for("auth.profile")
    return redirect(next_url)



@auth_bp.route("/profile", methods=["GET", "POST"])
@login_required
def profile():
    if not isinstance(current_user, Customer):
        return redirect(url_for("auth.login"))
    if request.method == "POST":
        current_user.full_name = request.form.get("full_name", current_user.full_name).strip()
        current_user.mobile = request.form.get("mobile", "").strip() or current_user.mobile
        current_user.nationality = request.form.get("nationality", "").strip() or None
        current_user.preferred_lang = request.form.get("preferred_lang") or current_user.preferred_lang
        current_user.email_notify = request.form.get("email_notify") == "on"
        current_user.push_enabled = request.form.get("push_enabled") == "on"
        if not current_user.push_enabled:
            current_user.push_subscription = None
        f = request.files.get("avatar")
        if f and f.filename:
            from app.services.storage_service import save_local_upload
            url = save_local_upload(f, subfolder="avatars")
            if url:
                current_user.avatar_url = url
        pw = request.form.get("password", "").strip()
        if pw and len(pw) >= 6:
            current_user.set_password(pw)
        db.session.commit()
        flash("Profile updated." if g.lang == "en" else "प्रोफाइल अपडेट भयो।", "success")
        return redirect(url_for("auth.profile"))
    return render_template("auth/profile.html")


@auth_bp.route("/forgot-password", methods=["GET", "POST"])
def forgot_password():
    if request.method == "POST":
        email = request.form.get("email", "").strip().lower()
        user = Customer.query.filter_by(email=email).first()
        if user:
            import secrets
            from datetime import timedelta
            user.reset_token = secrets.token_urlsafe(32)
            user.reset_token_expires = datetime.utcnow() + timedelta(hours=2)
            db.session.commit()
            try:
                from app.services.email_service import send_email, _brand_context
                brand = _brand_context()
                reset_url = url_for("auth.reset_password", token=user.reset_token, _external=True)
                html = render_template(
                    "emails/password_reset.html",
                    name=user.full_name,
                    reset_url=reset_url,
                    email_reason="Password reset · पासवर्ड रिसेट",
                    **brand,
                )
                send_email(
                    user.email,
                    "Password reset | पासवर्ड रिसेट — SR All Service Hub",
                    html,
                    template_key="password_reset",
                )
            except Exception as e:
                current_app.logger.exception("Reset email failed: %s", e)
        flash(
            "If that email exists, a reset link was sent."
            if g.lang == "en"
            else "यदि इमेल मिलेमा रिसेट लिङ्क पठाइएको छ।",
            "success",
        )
        return redirect(url_for("auth.login"))
    return render_template("auth/forgot_password.html")


@auth_bp.route("/reset-password/<token>", methods=["GET", "POST"])
def reset_password(token):
    user = Customer.query.filter_by(reset_token=token).first()
    if not user or not user.reset_token_expires or user.reset_token_expires < datetime.utcnow():
        flash("Invalid or expired reset link." if g.lang == "en" else "लिङ्क अमान्य वा सकिएको छ।", "error")
        return redirect(url_for("auth.forgot_password"))
    if request.method == "POST":
        pw = request.form.get("password", "")
        if len(pw) < 6:
            flash("Password too short." if g.lang == "en" else "पासवर्ड छोटो भयो।", "error")
            return redirect(request.url)
        user.set_password(pw)
        user.reset_token = None
        user.reset_token_expires = None
        db.session.commit()
        flash("Password updated. Please login." if g.lang == "en" else "पासवर्ड अपडेट भयो। लगइन गर्नुहोस्।", "success")
        return redirect(url_for("auth.login"))
    return render_template("auth/reset_password.html")



@auth_bp.route("/push-public-key")
def push_public_key():
    from flask import jsonify
    from app.services.push_service import get_vapid_public_key, vapid_configured
    return jsonify({
        "publicKey": get_vapid_public_key(),
        "enabled": vapid_configured(),
    })


@auth_bp.route("/push-subscribe", methods=["POST"])
@login_required
def push_subscribe():
    from flask import jsonify
    if not isinstance(current_user, Customer):
        return jsonify({"ok": False, "error": "login required"}), 401
    data = request.get_json(silent=True) or {}
    import json
    if not data.get("endpoint"):
        return jsonify({"ok": False, "error": "invalid subscription"}), 400
    current_user.push_subscription = json.dumps(data)
    current_user.push_enabled = True
    db.session.commit()
    return jsonify({"ok": True})


@auth_bp.route("/push-unsubscribe", methods=["POST"])
@login_required
def push_unsubscribe():
    from flask import jsonify
    if not isinstance(current_user, Customer):
        return jsonify({"ok": False}), 401
    current_user.push_subscription = None
    current_user.push_enabled = False
    db.session.commit()
    return jsonify({"ok": True})



@auth_bp.route("/facebook")
def facebook_login():
    app_id = current_app.config.get("FACEBOOK_APP_ID") or os.getenv("FACEBOOK_APP_ID")
    if not app_id:
        flash(
            "Facebook login is not configured."
            if g.lang == "en"
            else "Facebook लगइन सेट छैन।",
            "error",
        )
        return redirect(url_for("auth.login"))
    redirect_uri = url_for("auth.facebook_callback", _external=True)
    params = {
        "client_id": app_id,
        "redirect_uri": redirect_uri,
        # user_mobile_phone requires app review; email+profile always available
        "scope": "email,public_profile",
        "response_type": "code",
    }
    return redirect("https://www.facebook.com/v18.0/dialog/oauth?" + urlencode(params))


@auth_bp.route("/facebook/callback")
def facebook_callback():
    import requests as http_requests

    code = request.args.get("code")
    if not code:
        flash("Facebook login cancelled.", "error")
        return redirect(url_for("auth.login"))
    app_id = current_app.config.get("FACEBOOK_APP_ID") or os.getenv("FACEBOOK_APP_ID")
    app_secret = current_app.config.get("FACEBOOK_APP_SECRET") or os.getenv("FACEBOOK_APP_SECRET")
    redirect_uri = url_for("auth.facebook_callback", _external=True)
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
            params={"fields": "id,name,email,picture.type(large)", "access_token": access_token},
            timeout=15,
        )
        info.raise_for_status()
        data = info.json()
    except Exception as e:
        current_app.logger.exception("Facebook OAuth failed: %s", e)
        flash("Facebook login failed." if g.lang == "en" else "Facebook लगइन असफल।", "error")
        return redirect(url_for("auth.login"))

    fb_id = str(data.get("id") or "")
    email = (data.get("email") or "").lower() or None
    name = data.get("name") or (email.split("@")[0] if email else "User")
    picture = None
    try:
        pic = data.get("picture") or {}
        if isinstance(pic, dict):
            picture = (pic.get("data") or {}).get("url")
        elif isinstance(pic, str):
            picture = pic
    except Exception:
        picture = None
    if not picture and fb_id:
        picture = f"https://graph.facebook.com/{fb_id}/picture?type=large"
    # Phone rarely available without special FB permissions / app review
    phone = (data.get("mobile_phone") or data.get("phone") or "").strip() or None

    user = Customer.query.filter_by(facebook_id=fb_id).first() if fb_id else None
    if not user and email:
        user = Customer.query.filter_by(email=email).first()
    is_new = False
    if not user:
        user = Customer(
            full_name=name,
            email=email,
            facebook_id=fb_id,
            mobile=phone,
            avatar_url=picture or None,
        )
        db.session.add(user)
        is_new = True
    else:
        user.facebook_id = fb_id
        if name and not user.full_name:
            user.full_name = name
        if picture:
            user.avatar_url = picture
        if phone and not user.mobile:
            user.mobile = phone
    user.last_login = datetime.utcnow()
    try:
        from app.services.geo_service import capture_login_geo
        capture_login_geo(user)
    except Exception:
        pass
    db.session.commit()
    if is_new and email:
        try:
            from app.services.email_service import send_welcome_email
            send_welcome_email(user, lang=session.get("lang", "ne"), via_google=False)
        except Exception as e:
            current_app.logger.warning("welcome email fb: %s", e)
    login_user(user, remember=True)
    next_url = session.pop("next_url", None) or url_for("public.home")
    if not user.mobile:
        flash(
            "Please add your mobile number in profile."
            if session.get("lang") == "en"
            else "कृपया प्रोफाइलमा मोबाइल नम्बर थप्नुहोस्।",
            "info",
        )
        if not session.get("next_url"):
            next_url = url_for("auth.profile")
    return redirect(next_url)
