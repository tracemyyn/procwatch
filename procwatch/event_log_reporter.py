"""Formatting helpers for the event log."""

from __future__ import annotations

import datetime
from typing import List

from procwatch.event_log import EventEntry

_LEVEL_LABEL = {
    "info": "INFO    ",
    "warning": "WARNING ",
    "critical": "CRITICAL",
}


def _fmt_ts(ts: float) -> str:
    return datetime.datetime.fromtimestamp(ts).strftime("%Y-%m-%d %H:%M:%S")


def format_event_line(entry: EventEntry) -> str:
    """Return a single formatted log line for one event."""
    label = _LEVEL_LABEL.get(entry.level, entry.level.upper().ljust(8))
    tag_str = " [" + ",".join(entry.tags) + "]" if entry.tags else ""
    return (
        f"{_fmt_ts(entry.timestamp)}  {label}  "
        f"pid={entry.pid} {entry.name!r}{tag_str}  {entry.message}"
    )


def format_event_table(entries: List[EventEntry]) -> str:
    """Return a multi-line table of events."""
    if not entries:
        return "(no events)"
    header = f"{'TIMESTAMP':<19}  {'LEVEL':<8}  {'PID':>6}  {'NAME':<20}  MESSAGE"
    sep = "-" * len(header)
    lines = [header, sep]
    for e in entries:
        label = _LEVEL_LABEL.get(e.level, e.level.upper().ljust(8))
        tag_str = " [" + ",".join(e.tags) + "]" if e.tags else ""
        lines.append(
            f"{_fmt_ts(e.timestamp):<19}  {label:<8}  {e.pid:>6}  "
            f"{e.name:<20}  {e.message}{tag_str}"
        )
    return "\n".join(lines)


def format_event_summary(entries: List[EventEntry]) -> str:
    """Return a short summary line for a list of events."""
    total = len(entries)
    by_level: dict[str, int] = {}
    for e in entries:
        by_level[e.level] = by_level.get(e.level, 0) + 1
    parts = [f"{v} {k}" for k, v in sorted(by_level.items())]
    detail = ", ".join(parts) if parts else "none"
    return f"Event log: {total} total ({detail})"
