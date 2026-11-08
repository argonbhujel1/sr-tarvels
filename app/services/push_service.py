"""Web Push notifications for registered customers."""
from __future__ import annotations

import json
import logging
import os
from flask import current_app
from extensions import db

logger = logging.getLogger(__name__)


def vapid_configured() -> bool:
    return bool(
        current_app.config.get("VAPID_PUBLIC_KEY")
        and current_app.config.get("VAPID_PRIVATE_KEY")
    )


def get_vapid_public_key() -> str:
    return current_app.config.get("VAPID_PUBLIC_KEY") or ""


def send_push_to_subscription(subscription_info: dict, title: str, body: str, url: str = "/") -> bool:
    if not vapid_configured():
        return False
    try:
        from pywebpush import webpush, WebPushException

        claims = {
            "sub": current_app.config.get("VAPID_CLAIM_EMAIL")
            or os.getenv("VAPID_CLAIM_EMAIL")
            or "mailto:srallservicenepal@gmail.com"
        }
        payload = json.dumps({
            "title": title,
            "body": body,
            "url": url,
            "icon": "/static/icons/icon-192.png",
        })
        webpush(
            subscription_info=subscription_info,
            data=payload,
            vapid_private_key=current_app.config["VAPID_PRIVATE_KEY"],
            vapid_claims=claims,
        )
        return True
    except Exception as e:
        logger.warning("Web push failed: %s", e)
        return False


def notify_users_push(title: str, body: str, url: str = "/") -> int:
    """Send push to all active customers with a stored subscription."""
    from app.models import Customer

    if not vapid_configured():
        logger.info("VAPID not configured — skip push")
        return 0

    sent = 0
    users = Customer.query.filter_by(is_active=True, push_enabled=True).all()
    for u in users:
        if not u.push_subscription:
            continue
        try:
            sub = json.loads(u.push_subscription)
            if send_push_to_subscription(sub, title, body, url):
                sent += 1
            else:
                # drop invalid subscription
                pass
        except Exception as e:
            logger.warning("Push user %s: %s", u.id, e)
    return sent
