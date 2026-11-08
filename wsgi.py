"""WSGI entry for Vercel / Gunicorn."""
from app import create_app

application = create_app()
# Vercel looks for `app`
app = application
