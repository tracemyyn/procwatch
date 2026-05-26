"""Persistent in-memory event log for procwatch alerts and system events."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Optional
import time


@dataclass
class EventEntry:
    timestamp: float
    level: str          # "info", "warning", "critical"
    pid: int
    name: str
    message: str
    tags: List[str] = field(default_factory=list)


_log: List[EventEntry] = []
_max_entries: int = 500


def reset_event_log() -> None:
    """Clear all entries (primarily for tests)."""
    global _log
    _log = []


def set_max_entries(n: int) -> None:
    """Configure the maximum number of entries to retain."""
    global _max_entries
    _max_entries = n


def record_event(
    pid: int,
    name: str,
    message: str,
    level: str = "info",
    tags: Optional[List[str]] = None,
    ts: Optional[float] = None,
) -> EventEntry:
    """Append a new event to the log, evicting oldest if over capacity."""
    entry = EventEntry(
        timestamp=ts if ts is not None else time.time(),
        level=level,
        pid=pid,
        name=name,
        message=message,
        tags=list(tags or []),
    )
    _log.append(entry)
    if len(_log) > _max_entries:
        del _log[: len(_log) - _max_entries]
    return entry


def get_events(
    pid: Optional[int] = None,
    level: Optional[str] = None,
    since: Optional[float] = None,
) -> List[EventEntry]:
    """Return filtered events from the log."""
    results = _log
    if pid is not None:
        results = [e for e in results if e.pid == pid]
    if level is not None:
        results = [e for e in results if e.level == level]
    if since is not None:
        results = [e for e in results if e.timestamp >= since]
    return list(results)


def all_events() -> List[EventEntry]:
    """Return a shallow copy of the full event log."""
    return list(_log)
