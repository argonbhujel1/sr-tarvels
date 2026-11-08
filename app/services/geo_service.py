"""Client IP (ISP) + device GPS reverse geocode."""
from __future__ import annotations

import logging
from flask import request

logger = logging.getLogger(__name__)


def client_ip() -> str:
    xff = request.headers.get("X-Forwarded-For") or request.headers.get("x-forwarded-for")
    if xff:
        return xff.split(",")[0].strip()
    real = request.headers.get("X-Real-IP") or request.headers.get("x-real-ip")
    if real:
        return real.strip()
    return (request.remote_addr or "").strip()


def lookup_ip_location(ip: str) -> dict:
    """ISP / network-level location only (not street-level)."""
    out = {"label": None, "lat": None, "lng": None, "city": None, "region": None, "country": None}
    if not ip or ip in ("127.0.0.1", "::1") or ip.startswith("10.") or ip.startswith("192.168."):
        out["label"] = "Local / private network"
        return out
    try:
        import requests

        r = requests.get(
            f"http://ip-api.com/json/{ip}",
            params={"fields": "status,message,country,regionName,city,lat,lon,isp,query"},
            timeout=4,
        )
        data = r.json()
        if data.get("status") != "success":
            return out
        city = data.get("city") or ""
        region = data.get("regionName") or ""
        country = data.get("country") or ""
        isp = data.get("isp") or ""
        parts = [p for p in (city, region, country) if p]
        label = ", ".join(parts) if parts else None
        if isp and label:
            label = f"{label} (ISP: {isp})"
        elif isp:
            label = f"ISP: {isp}"
        out["label"] = label
        out["lat"] = data.get("lat")
        out["lng"] = data.get("lon")
        out["city"] = city
        out["region"] = region
        out["country"] = country
    except Exception as e:
        logger.warning("IP lookup failed for %s: %s", ip, e)
    return out


def reverse_geocode(lat: float, lng: float) -> str | None:
    """OpenStreetMap Nominatim — more precise place name from GPS coords."""
    try:
        import requests

        r = requests.get(
            "https://nominatim.openstreetmap.org/reverse",
            params={
                "lat": lat,
                "lon": lng,
                "format": "json",
                "zoom": 18,
                "addressdetails": 1,
            },
            headers={"User-Agent": "SRAllServiceHubNepal/1.0 (contact@srtravels)"},
            timeout=6,
        )
        r.raise_for_status()
        data = r.json()
        addr = data.get("address") or {}
        # Prefer local neighbourhood / village / suburb for Nepal-style labels
        parts = []
        for key in (
            "neighbourhood",
            "suburb",
            "village",
            "hamlet",
            "city_district",
            "municipality",
            "city",
            "town",
            "county",
            "state_district",
            "state",
            "country",
        ):
            val = addr.get(key)
            if val and val not in parts:
                parts.append(val)
            if len(parts) >= 4:
                break
        if parts:
            return ", ".join(parts)
        return data.get("display_name")
    except Exception as e:
        logger.warning("reverse geocode failed: %s", e)
        return None


def capture_login_geo(user) -> None:
    """Store IP + ISP location only. GPS is filled later from browser."""
    try:
        ip = client_ip()
        ua = (request.headers.get("User-Agent") or "")[:300]
        geo = lookup_ip_location(ip)
        if hasattr(user, "last_ip"):
            user.last_ip = ip or None
        if hasattr(user, "last_user_agent"):
            user.last_user_agent = ua or None
        if hasattr(user, "last_ip_location_label"):
            user.last_ip_location_label = geo.get("label")
        # Do NOT overwrite GPS lat/lng/label if already from device
        if getattr(user, "location_source", None) != "gps":
            if hasattr(user, "last_lat") and geo.get("lat") is not None:
                user.last_lat = float(geo["lat"])
            if hasattr(user, "last_lng") and geo.get("lng") is not None:
                user.last_lng = float(geo["lng"])
            if hasattr(user, "last_location_label"):
                user.last_location_label = geo.get("label")
            if hasattr(user, "location_source"):
                user.location_source = "ip"
    except Exception as e:
        logger.warning("capture_login_geo: %s", e)


def apply_device_gps(user, lat: float, lng: float, accuracy: float | None = None) -> None:
    label = reverse_geocode(lat, lng)
    if accuracy is not None and label:
        label = f"{label} (±{int(accuracy)}m)"
    user.last_lat = float(lat)
    user.last_lng = float(lng)
    if label:
        user.last_location_label = label[:250]
    if hasattr(user, "location_source"):
        user.location_source = "gps"
