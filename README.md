# SR All Service Hub Nepal

**Production-ready corporate website & online booking management platform**

Brand: SR All Service Hub Nepal  
Travel identity: SR Travels & Tours / Success Route Travels & Tours  
Technology Partner: **BAM Studio**  
Tagline: *One Platform. Every Service. Every Journey.*

---

## Stack

- Python 3.12 + Flask
- SQLAlchemy + Flask-Migrate
- PostgreSQL (Neon recommended)
- Jinja2 + Vanilla JS + Custom CSS (no Bootstrap/Tailwind/React)
- Cloudinary (media)
- Google Gmail SMTP (App Password)
- OpenStreetMap + Leaflet ready
- Bilingual: Nepali (default) + English

---

## Quick Start

```bash
# 1. Clone / unzip and enter
cd sr-all-service-hub

# 2. Virtualenv
python3.12 -m venv venv
source venv/bin/activate   # Windows: venv\Scripts\activate

# 3. Install
pip install -r requirements.txt

# 4. Environment
cp .env.example .env
# Edit .env — set DATABASE_URL (Neon), SECRET_KEY, Cloudinary, Gmail App Password

# 5. Database
export FLASK_APP=app.py
flask init-db          # creates tables + seed data
flask create-admin     # creates admin from .env credentials

# 6. Run
flask run
# or: python app.py
```

Open:

- Public site: http://127.0.0.1:5000 (opens in Nepali)
- Admin: http://127.0.0.1:5000/admin/login

Default admin (change immediately):

- Email: value of `ADMIN_EMAIL` in `.env`
- Password: value of `ADMIN_PASSWORD` in `.env`

---

## What is implemented

### Public website
- Premium navy/gold design system
- Nepali-first bilingual UI (language switcher + session/localStorage)
- Homepage with all major sections
- Services (7 categories) + detail pages
- Booking forms: Flight, Visa, Tour, General inquiry
- Unique booking references: `SR-2026-00001`
- Public booking tracking (reference + mobile)
- Contact form
- Privacy / Terms / Cancellation pages
- **Premium footer** with:
  - Clickable eSewa, Khalti, Fonepay logos (official external links, `target="_blank"` + `rel="noopener noreferrer"`)
  - BAM Studio technology credit (permanent, gold, links to https://bamstudio.argan.com.np/)
  - Company contact & quick links

### Booking & operations
- Guest booking (no account required)
- Status workflow + history logs
- Customer-facing status labels (Nepali/English)
- Email confirmation skeleton (Gmail SMTP)

### Admin
- Secure login (rate-limited)
- Dashboard (counts, recent bookings, revenue placeholder)
- Bookings list + detail + status update
- Contact messages
- Payment methods enable/disable + instructions
- Services overview

### Architecture
- Modular structure (`models/`, `routes/`, `services/`, `templates/`)
- All major SQLAlchemy models defined
- Seed data for categories, services, payment methods, branches, FAQs, email templates
- CSRF, password hashing, secure sessions, input handling

---

## Payment logos (footer)

- eSewa → https://esewa.com.np/
- Khalti → https://khalti.com/
- Fonepay → https://fonepay.com/

Logos use official brand asset URLs where available, with clean text fallback if the image fails to load.  
**No claim is made that SR is an authorized merchant/partner** unless the company confirms that relationship. Admin can enable/disable each method.

---

## What still needs configuration / extension

| Area | Status | Notes |
|------|--------|-------|
| Neon PostgreSQL | Required | Set `DATABASE_URL` |
| Gmail SMTP | Required for live email | Use Google **App Password**, never normal password |
| Cloudinary | Optional | For production image/document uploads |
| Real payment gateways | Not simulated | Only enable when you have merchant credentials + official API integration |
| Full CMS editors | Foundation | Models + basic admin present; rich homepage/page/service editors can be expanded |
| Document private storage | Model ready | Wire Cloudinary signed URLs + access control |
| Leaflet maps | Ready | Add branch map on contact/branches pages |
| Email template designer | DB-backed templates | Expand admin UI for visual editing |

---

## Company information (editable)

- **Company**: SR All Service Hub Nepal Pvt. Ltd.
- **Urlabari**: Near Radhika Ma Vi, Old Sabji Bajar Line, 5 Madhumalla Road, Puspanagari, Urlabari-05, Koshi Province, Nepal  
  Phone: +977 9713799042
- **Kathmandu**: +977 9851440623 / +977 9852683942
- **Email**: srallservicenepal@gmail.com
- **Facebook**: https://www.facebook.com/SRallservicehubNepal/
- **Hours**: 7:00 AM – 9:00 PM, Monday–Sunday

Do not invent registration numbers, awards or certifications.

---

## Production checklist

1. Strong `SECRET_KEY`
2. Neon (or other) PostgreSQL with SSL
3. Gmail App Password + test email
4. Cloudinary credentials
5. HTTPS (Vercel / Railway / Render / VPS + Nginx)
6. Change default admin password
7. Configure real payment methods only after merchant onboarding
8. Review all public content in both languages
9. Set `FLASK_ENV=production`
10. Enable database backups

---

## Project structure

```
sr-all-service-hub/
├── app.py
├── config.py
├── extensions.py
├── requirements.txt
├── .env.example
├── README.md
├── app/
│   ├── __init__.py
│   ├── seed.py
│   ├── models/
│   ├── routes/          # public, booking, admin
│   ├── services/        # booking_service, email_service
│   ├── templates/
│   └── static/
├── migrations/
└── tests/
```

---

**Designed & Engineered by BAM Studio**  
https://bamstudio.argan.com.np/  
BUILD · CREATE · GROW
