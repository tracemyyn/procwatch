"""Builds structured webhook payload dicts from Alert objects."""

from __future__ import annotations

import platform
from datetime import datetime, timezone
from typing import Any

from procwatch.notifier import Alert

_VERSION = "1.0"


def _iso_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def build_base_payload(alert: Alert) -> dict[str, Any]:
    """Return a minimal payload dict from an Alert."""
    return {
        "version": _VERSION,
        "timestamp": _iso_now(),
        "host": platform.node(),
        "pid": alert.pid,
        "name": alert.name,
        "cpu_percent": alert.cpu_percent,
        "mem_percent": alert.mem_percent,
        "message": alert.message,
    }


def build_rich_payload(
    alert: Alert,
    tags: list[str] | None = None,
    severity: str = "info",
    extra: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Return an enriched payload with optional tags, severity, and extras."""
    payload = build_base_payload(alert)
    payload["severity"] = severity
    payload["tags"] = tags or []
    if extra:
        payload.update(extra)
    return payload


def payload_to_slack(alert: Alert, tags: list[str] | None = None) -> dict[str, Any]:
    """Format a Slack-compatible payload with an attachments block."""
    colour_map = {"info": "#36a64f", "warning": "#ffcc00", "critical": "#ff0000"}
    severity = "critical" if alert.cpu_percent >= 90 or alert.mem_percent >= 90 else (
        "warning" if alert.cpu_percent >= 70 or alert.mem_percent >= 70 else "info"
    )
    colour = colour_map.get(severity, "#36a64f")
    return {
        "text": f":warning: procwatch alert on `{platform.node()}`",
        "attachments": [
            {
                "color": colour,
                "title": f"Process: {alert.name} (PID {alert.pid})",
                "text": alert.message,
                "fields": [
                    {"title": "CPU %", "value": str(alert.cpu_percent), "short": True},
                    {"title": "MEM %", "value": str(alert.mem_percent), "short": True},
                    {"title": "Severity", "value": severity, "short": True},
                    {"title": "Tags", "value": ", ".join(tags or []) or "—", "short": True},
                ],
                "footer": "procwatch",
                "ts": int(datetime.now(timezone.utc).timestamp()),
            }
        ],
    }
