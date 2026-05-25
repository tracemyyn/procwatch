"""Formatting helpers for silence-window status output."""

from __future__ import annotations

from datetime import datetime
from typing import List

from procwatch.silencer import SilenceWindow, get_windows, is_silenced

_DAY_NAMES = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]


def _fmt_days(days: List[int]) -> str:
    if sorted(days) == list(range(7)):
        return "every day"
    return ",".join(_DAY_NAMES[d] for d in sorted(days))


def _fmt_window(w: SilenceWindow) -> str:
    start = w.start.strftime("%H:%M")
    end = w.end.strftime("%H:%M")
    return (
        f"  [{w.name}] {start}-{end}  glob={w.name_glob!r}  days={_fmt_days(w.days)}"
    )


def format_silence_table() -> str:
    """Return a human-readable table of all registered silence windows."""
    windows = get_windows()
    if not windows:
        return "No silence windows configured."
    lines = ["Silence windows:", "-" * 50]
    for w in windows:
        lines.append(_fmt_window(w))
    return "\n".join(lines)


def format_silenced_line(process_name: str, at: datetime | None = None) -> str:
    """One-liner indicating whether a process is currently silenced."""
    silenced = is_silenced(process_name, at=at)
    status = "SILENCED" if silenced else "active"
    ts = (at or datetime.now()).strftime("%H:%M:%S")
    return f"[{ts}] {process_name}: {status}"
