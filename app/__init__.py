from flask import Flask, request, session, g
from config import config_by_name
from extensions import init_extensions, db
import os


def create_app(config_name=None):
    if config_name is None:
        config_name = os.getenv("FLASK_ENV", "development")

    # Absolute paths so Vercel / serverless can find templates & static
    _pkg_dir = os.path.abspath(os.path.dirname(__file__))
    app = Flask(
        __name__,
        template_folder=os.path.join(_pkg_dir, "templates"),
        static_folder=os.path.join(_pkg_dir, "static"),
        instance_relative_config=True,
    )
    app.root_path = _pkg_dir
    app.config.from_object(config_by_name.get(config_name, config_by_name["default"]))

    init_extensions(app)

    # Load models without shadowing Flask `app` (never use `import app.models` here)
    from app import models as _models  # noqa: F401

    # Auto-create tables on Neon/Vercel when missing (set AUTO_INIT_DB=1)
    if os.getenv("AUTO_INIT_DB", "1").lower() in ("1", "true", "yes"):
        with app.app_context():
            try:
                from sqlalchemy import text
                with db.engine.begin() as conn:
                    conn.execute(text("ALTER TABLE customers ALTER COLUMN mobile DROP NOT NULL"))
            except Exception:
                pass
            try:
                db.create_all()
                try:
                    from sqlalchemy import text, inspect
                    dialect = db.engine.dialect.name
                    with db.engine.begin() as conn:
                        if dialect == "postgresql":
                            # Add missing columns safely via information_schema
                            checks = [
                                ("faqs", "is_featured", "ALTER TABLE faqs ADD COLUMN is_featured BOOLEAN DEFAULT FALSE"),
                                ("service_categories", "image_url", "ALTER TABLE service_categories ADD COLUMN image_url TEXT"),
                                ("customers", "password_hash", "ALTER TABLE customers ADD COLUMN password_hash VARCHAR(255)"),
                                ("customers", "google_id", "ALTER TABLE customers ADD COLUMN google_id VARCHAR(120)"),
                                ("customers", "is_active", "ALTER TABLE customers ADD COLUMN is_active BOOLEAN DEFAULT TRUE"),
                                ("customers", "email_notify", "ALTER TABLE customers ADD COLUMN email_notify BOOLEAN DEFAULT TRUE"),
                                ("customers", "last_login", "ALTER TABLE customers ADD COLUMN last_login TIMESTAMP"),
                                ("customers", "avatar_url", "ALTER TABLE customers ADD COLUMN avatar_url TEXT"),
                                ("customers", "reset_token", "ALTER TABLE customers ADD COLUMN reset_token VARCHAR(64)"),
                                ("customers", "reset_token_expires", "ALTER TABLE customers ADD COLUMN reset_token_expires TIMESTAMP"),
                                ("customers", "push_subscription", "ALTER TABLE customers ADD COLUMN push_subscription TEXT"),
                                ("customers", "push_enabled", "ALTER TABLE customers ADD COLUMN push_enabled BOOLEAN DEFAULT TRUE"),
                                ("customers", "facebook_id", "ALTER TABLE customers ADD COLUMN facebook_id VARCHAR(120)"),
                                ("customers", "last_ip", "ALTER TABLE customers ADD COLUMN last_ip VARCHAR(64)"),
                                ("customers", "last_user_agent", "ALTER TABLE customers ADD COLUMN last_user_agent VARCHAR(300)"),
                                ("customers", "last_lat", "ALTER TABLE customers ADD COLUMN last_lat DOUBLE PRECISION"),
                                ("customers", "last_lng", "ALTER TABLE customers ADD COLUMN last_lng DOUBLE PRECISION"),
                                ("customers", "last_location_label", "ALTER TABLE customers ADD COLUMN last_location_label VARCHAR(250)"),
                                ("testimonials", "mobile", "ALTER TABLE testimonials ADD COLUMN mobile VARCHAR(30)"),
                                ("testimonials", "customer_id", "ALTER TABLE testimonials ADD COLUMN customer_id INTEGER"),
                                ("testimonials", "created_at", "ALTER TABLE testimonials ADD COLUMN created_at TIMESTAMP"),
                            ]
                            for table, col, ddl in checks:
                                exists = conn.execute(text(
                                    "SELECT 1 FROM information_schema.columns "
                                    "WHERE table_name=:t AND column_name=:c"
                                ), {"t": table, "c": col}).fetchone()
                                if not exists:
                                    conn.execute(text(ddl))
                                    print(f"Added {table}.{col}")
                            try:
                                conn.execute(text("ALTER TABLE bookings ALTER COLUMN customer_id DROP NOT NULL"))
                            except Exception:
                                pass
                            try:
                                conn.execute(text("ALTER TABLE customers ALTER COLUMN mobile DROP NOT NULL"))
                            except Exception:
                                pass
                            for stmt in [
                                "ALTER TABLE payment_methods ALTER COLUMN logo_url TYPE TEXT",
                                "ALTER TABLE payment_methods ALTER COLUMN qr_image_url TYPE TEXT",
                                "ALTER TABLE payment_methods ALTER COLUMN external_url TYPE TEXT",
                                "ALTER TABLE payments ALTER COLUMN receipt_url TYPE TEXT",
                            ]:
                                try:
                                    conn.execute(text(stmt))
                                except Exception:
                                    pass
                        else:
                            for stmt in [
                                "ALTER TABLE payment_methods ALTER COLUMN logo_url TYPE TEXT",
                                "ALTER TABLE payment_methods ALTER COLUMN qr_image_url TYPE TEXT",
                                "ALTER TABLE payment_methods ALTER COLUMN external_url TYPE TEXT",
                                "ALTER TABLE payments ALTER COLUMN receipt_url TYPE TEXT",
                                "ALTER TABLE service_categories ADD COLUMN image_url TEXT",
                                "ALTER TABLE faqs ADD COLUMN is_featured BOOLEAN DEFAULT 0",
                            ]:
                                try:
                                    conn.execute(text(stmt))
                                except Exception:
                                    pass
                except Exception as _alter_e:
                    print("column widen note:", _alter_e)
                # Seed only if empty (no homepage sections yet)
                from app.models import HomepageSection, Admin
                if HomepageSection.query.count() == 0:
                    from app.seed import seed_data
                    seed_data()
                    print("AUTO_INIT_DB: tables created and seeded")
                if Admin.query.count() == 0:
                    email = app.config.get("ADMIN_EMAIL")
                    password = app.config.get("ADMIN_PASSWORD")
                    if email and password:
                        admin = Admin(email=email, full_name="Site Administrator", role="superadmin")
                        admin.set_password(password)
                        db.session.add(admin)
                        db.session.commit()
                        print(f"AUTO_INIT_DB: admin created {email}")
                # Ensure homepage section keys exist (for updates without full reseed)
                try:
                    from app.models import HomepageSection
                    defaults = [
                        ("categories", "हाम्रा सेवा श्रेणीहरू", "Our Service Categories", "सात मुख्य श्रेणीमा पूर्ण सेवा", "Complete services across seven main categories", 3),
                        ("popular", "लोकप्रिय सेवाहरू", "Popular Services", "", "", 4),
                        ("destinations_home", "लोकप्रिय गन्तव्यहरू", "Popular Destinations", "", "", 5),
                        ("why_1", "विश्वसनीय", "Trusted", "पारदर्शी प्रक्रिया र सुरक्षित कागजात व्यवस्थापन", "Transparent process and secure document handling", 71),
                        ("why_2", "छिटो सेवा", "Fast Service", "अनलाइन बुकिङ र द्रुत प्रतिक्रिया", "Online booking and quick response", 72),
                        ("why_3", "एकै प्लेटफर्म", "One Platform", "टिकट, भिसा, टुर, कागजात — सबै यहाँ", "Tickets, visa, tours, documents — all here", 73),
                        ("process_1", "सेवा छान्नुहोस्", "Choose Service", "आवश्यक सेवा चयन गर्नुहोस्", "Select the service you need", 81),
                        ("process_2", "फारम भर्नुहोस्", "Fill Form", "विवरण र सम्पर्क जानकारी", "Details and contact information", 82),
                        ("process_3", "ट्र्याक गर्नुहोस्", "Track", "रेफरेन्स नम्बरबाट स्थिति", "Status via reference number", 83),
                        ("process_4", "पुष्टि", "Confirm", "भुक्तानी र पुष्टि", "Payment and confirmation", 84),
                    ]
                    for key, tn, te, cn, ce, so in defaults:
                        if not HomepageSection.query.filter_by(key=key).first():
                            db.session.add(HomepageSection(
                                key=key, title_ne=tn, title_en=te,
                                content_ne=cn, content_en=ce,
                                is_enabled=True, sort_order=so,
                            ))
                    db.session.commit()
                except Exception as _hs:
                    print("homepage sections ensure:", _hs)

            except Exception as e:
                print("AUTO_INIT_DB note:", e)

    # Language handling
    @app.before_request
    def set_language():
        lang = request.args.get("lang") or session.get("lang") or app.config.get("DEFAULT_LANG", "ne")
        if lang not in app.config.get("SUPPORTED_LANGS", ["ne", "en"]):
            lang = "ne"
        session["lang"] = lang
        g.lang = lang

    # Register blueprints
    from app.routes.public import public_bp
    from app.routes.booking import booking_bp
    from app.routes.admin import admin_bp
    from app.routes.auth import auth_bp

    app.register_blueprint(public_bp)
    app.register_blueprint(booking_bp, url_prefix="/booking")
    app.register_blueprint(admin_bp, url_prefix="/admin")
    app.register_blueprint(auth_bp)

    # Context processors
    @app.context_processor
    def inject_globals():
        from app.models import PaymentMethod, SiteSetting, Branch
        lang = getattr(g, "lang", "ne")
        payment_methods = []
        branches = []
        try:
            payment_methods = (
                PaymentMethod.query.filter_by(is_enabled=True)
                .order_by(PaymentMethod.sort_order)
                .all()
            )
            branches = Branch.query.filter_by(is_published=True).order_by(Branch.sort_order).all()
        except Exception:
            pass

        def setting(key, default=""):
            try:
                s = SiteSetting.query.filter_by(key=key).first()
                if not s:
                    return default
                return s.value_ne if lang == "ne" else (s.value_en or s.value_ne or default)
            except Exception:
                return default

        return {
            "lang": lang,
            "payment_methods": payment_methods,
            "setting": setting,
            "branches": branches,
            "app_name": app.config.get("APP_NAME"),
            "current_year": 2026,
        }

    # CLI helpers
    @app.cli.command("init-db")
    def init_db():
        """Create tables and seed initial data."""
        db.create_all()
        try:
            from sqlalchemy import text
            with db.engine.begin() as conn:
                for stmt in [
                    "ALTER TABLE payment_methods ALTER COLUMN logo_url TYPE TEXT",
                    "ALTER TABLE payment_methods ALTER COLUMN qr_image_url TYPE TEXT",
                    "ALTER TABLE payment_methods ALTER COLUMN external_url TYPE TEXT",
                    "ALTER TABLE payments ALTER COLUMN receipt_url TYPE TEXT",
                            "ALTER TABLE service_categories ADD COLUMN image_url TEXT",
                            "ALTER TABLE faqs ADD COLUMN is_featured BOOLEAN DEFAULT FALSE",
                ]:
                    try:
                        conn.execute(text(stmt))
                    except Exception:
                        pass
        except Exception as _alter_e:
            print("column widen note:", _alter_e)
        # SQLite: add new columns if missing (dev convenience)
        try:
            from sqlalchemy import text
            with db.engine.connect() as conn:
                cols = [r[1] for r in conn.execute(text("PRAGMA table_info(team_members)")).fetchall()]
                if cols and "is_collaborator" not in cols:
                    conn.execute(text("ALTER TABLE team_members ADD COLUMN is_collaborator BOOLEAN DEFAULT 0"))
                    conn.commit()
                    print("Added is_collaborator column to team_members")
                if cols and "phone" not in cols:
                    conn.execute(text("ALTER TABLE team_members ADD COLUMN phone VARCHAR(40)"))
                    conn.commit()
                if cols and "video_url" not in cols:
                    conn.execute(text("ALTER TABLE team_members ADD COLUMN video_url VARCHAR(500)"))
                    conn.commit()
                    print("Added phone/video_url to team_members")

                scols = [r[1] for r in conn.execute(text("PRAGMA table_info(services)")).fetchall()]
                if scols and "price_npr" not in scols:
                    conn.execute(text("ALTER TABLE services ADD COLUMN price_npr NUMERIC(12,2)"))
                    conn.commit()
                    print("Added price_npr to services")
                try:
                    ccols = [r[1] for r in conn.execute(text("PRAGMA table_info(service_categories)")).fetchall()]
                    if ccols and "image_url" not in ccols:
                        conn.execute(text("ALTER TABLE service_categories ADD COLUMN image_url TEXT"))
                        conn.commit()
                        print("Added image_url to service_categories")
                except Exception as e4:
                    print("categories column note:", e4)
                try:
                    fcols = [r[1] for r in conn.execute(text("PRAGMA table_info(faqs)")).fetchall()]
                    if fcols and "is_featured" not in fcols:
                        conn.execute(text("ALTER TABLE faqs ADD COLUMN is_featured BOOLEAN DEFAULT 0"))
                        conn.commit()
                        print("Added is_featured to faqs")
                except Exception as e5:
                    print("faqs column note:", e5)

                pcols = [r[1] for r in conn.execute(text("PRAGMA table_info(packages)")).fetchall()]
                if pcols and "min_payment" not in pcols:
                    conn.execute(text("ALTER TABLE packages ADD COLUMN min_payment NUMERIC(12,2)"))
                    conn.commit()
                    print("Added min_payment to packages")
        except Exception as e:
            print("Note (schema check):", e)
        from app.seed import seed_data
        seed_data()
        print("Database initialized and seeded.")


    @app.cli.command("create-admin")
    def create_admin():
        from app.models import Admin
        email = app.config.get("ADMIN_EMAIL")
        password = app.config.get("ADMIN_PASSWORD")
        if Admin.query.filter_by(email=email).first():
            print("Admin already exists.")
            return
        admin = Admin(email=email, full_name="Site Administrator", role="superadmin")
        admin.set_password(password)
        db.session.add(admin)
        db.session.commit()
        print(f"Admin created: {email}")

    return app
