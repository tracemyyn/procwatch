"""Notification backends: webhook and desktop alerts."""

import json
import logging
import urllib.error
import urllib.request
from dataclasses import dataclass
from typing import Optional

try:
    from plyer import notification as plyer_notification
    _PLYER_AVAILABLE = True
except ImportError:
    _PLYER_AVAILABLE = False

logger = logging.getLogger(__name__)


@dataclass
class Alert:
    pid: int
    name: str
    cpu_percent: float
    memory_mb: float
    message: str


def send_webhook(url: str, alert: Alert, timeout: int = 5) -> bool:
    """POST alert payload to a webhook URL. Returns True on success."""
    payload = json.dumps({
        "pid": alert.pid,
        "name": alert.name,
        "cpu_percent": alert.cpu_percent,
        "memory_mb": round(alert.memory_mb, 2),
        "message": alert.message,
    }).encode("utf-8")

    req = urllib.request.Request(
        url,
        data=payload,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=timeout):
            return True
    except (urllib.error.URLError, OSError) as exc:
        logger.warning("Webhook delivery failed: %s", exc)
        return False


def send_desktop(alert: Alert, app_name: str = "procwatch") -> bool:
    """Show a desktop notification. Returns True if plyer is available."""
    if not _PLYER_AVAILABLE:
        logger.debug("plyer not installed; skipping desktop notification")
        return False
    try:
        plyer_notification.notify(
            title=f"{app_name}: {alert.name} spike",
            message=alert.message,
            app_name=app_name,
            timeout=6,
        )
        return True
    except Exception as exc:  # plyer raises various platform errors
        logger.warning("Desktop notification failed: %s", exc)
        return False


def dispatch(alert: Alert, webhook_url: Optional[str], desktop: bool) -> None:
    """Dispatch an alert via configured channels."""
    if webhook_url:
        send_webhook(webhook_url, alert)
    if desktop:
        send_desktop(alert)
