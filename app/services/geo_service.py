"""Resolve client IP and approximate location label."""
from __future__ import annotations

import logging
from flask import request

logger = logging.getLogger(__name__)


def client_ip() -> str:
    # Vercel / proxies
    xff = request.headers.get("X-Forwarded-For") or request.headers.get("x-forwarded-for")
    if xff:
        return xff.split(",")[0].strip()
    real = request.headers.get("X-Real-IP") or request.headers.get("x-real-ip")
    if real:
        return real.strip()
    return (request.remote_addr or "").strip()


def lookup_ip_location(ip: str) -> dict:
    """
    Returns {label, lat, lng, city, region, country}.
    Uses ip-api.com (HTTP, free, no key) — skip private IPs.
    """
    out = {"label": None, "lat": None, "lng": None, "city": None, "region": None, "country": None}
    if not ip or ip in ("127.0.0.1", "::1") or ip.startswith("10.") or ip.startswith("192.168."):
        out["label"] = "Local / private network"
        return out
    try:
        import requests

        r = requests.get(
            f"http://ip-api.com/json/{ip}",
            params={"fields": "status,message,country,regionName,city,lat,lon,query"},
            timeout=4,
        )
        data = r.json()
        if data.get("status") != "success":
            return out
        city = data.get("city") or ""
        region = data.get("regionName") or ""
        country = data.get("country") or ""
        parts = [p for p in (city, region, country) if p]
        out["label"] = ", ".join(parts) if parts else None
        out["lat"] = data.get("lat")
        out["lng"] = data.get("lon")
        out["city"] = city
        out["region"] = region
        out["country"] = country
    except Exception as e:
        logger.warning("IP lookup failed for %s: %s", ip, e)
    return out


def capture_login_geo(user) -> None:
    """Attach last IP / location onto a Customer (or Admin) model instance before commit."""
    try:
        ip = client_ip()
        ua = (request.headers.get("User-Agent") or "")[:300]
        geo = lookup_ip_location(ip)
        if hasattr(user, "last_ip"):
            user.last_ip = ip or None
        if hasattr(user, "last_user_agent"):
            user.last_user_agent = ua or None
        if hasattr(user, "last_lat") and geo.get("lat") is not None:
            user.last_lat = float(geo["lat"])
        if hasattr(user, "last_lng") and geo.get("lng") is not None:
            user.last_lng = float(geo["lng"])
        if hasattr(user, "last_location_label"):
            user.last_location_label = geo.get("label")
    except Exception as e:
        logger.warning("capture_login_geo: %s", e)
