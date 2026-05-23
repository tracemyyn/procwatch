"""Export alert history to JSON or CSV for offline analysis."""

from __future__ import annotations

import csv
import io
import json
from datetime import datetime
from typing import List

from procwatch.history import HistoryEntry, list_entries


def _entry_to_dict(key: str, entry: HistoryEntry) -> dict:
    """Convert a history *key* + *entry* pair to a plain dict."""
    name, _, pid_str = key.partition(":")
    return {
        "key": key,
        "name": name,
        "pid": int(pid_str) if pid_str.isdigit() else None,
        "alert_count": entry.alert_count,
        "last_alert_ts": entry.last_alert_ts,
        "last_alert_iso": datetime.fromtimestamp(entry.last_alert_ts).isoformat(),
    }


def export_json(indent: int = 2) -> str:
    """Return the full alert history serialised as a JSON string."""
    rows = [
        _entry_to_dict(key, entry) for key, entry in list_entries()
    ]
    return json.dumps(rows, indent=indent)


def export_csv() -> str:
    """Return the full alert history serialised as a CSV string."""
    rows = [
        _entry_to_dict(key, entry) for key, entry in list_entries()
    ]
    if not rows:
        return ""

    fieldnames = ["key", "name", "pid", "alert_count", "last_alert_ts", "last_alert_iso"]
    buf = io.StringIO()
    writer = csv.DictWriter(buf, fieldnames=fieldnames, lineterminator="\n")
    writer.writeheader()
    writer.writerows(rows)
    return buf.getvalue()


def export_to_file(path: str, fmt: str = "json") -> None:
    """Write the alert history to *path* in the requested *fmt* (``json`` or ``csv``)."""
    if fmt == "csv":
        content = export_csv()
    elif fmt == "json":
        content = export_json()
    else:
        raise ValueError(f"Unsupported export format: {fmt!r}")

    with open(path, "w", encoding="utf-8") as fh:
        fh.write(content)
