"""Alert deduplication: suppress identical alerts within a time window."""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from typing import Dict, Optional, Tuple

from procwatch.notifier import Alert

# (pid, metric) -> last alert timestamp
_DedupStore = Dict[Tuple[int, str], float]

_store: _DedupStore = {}
_window_seconds: float = 60.0


@dataclass
class DedupState:
    window_seconds: float
    entries: Dict[Tuple[int, str], float] = field(default_factory=dict)


def reset_dedup(window_seconds: float = 60.0) -> None:
    """Clear all dedup state and set the dedup window."""
    global _store, _window_seconds
    _store = {}
    _window_seconds = window_seconds


def _make_key(alert: Alert) -> Tuple[int, str]:
    """Return a dedup key derived from PID and metric name."""
    metric = "cpu" if alert.cpu_percent is not None else "mem"
    return (alert.pid, metric)


def is_duplicate(alert: Alert, now: Optional[float] = None) -> bool:
    """Return True if an equivalent alert was already dispatched within the window."""
    if now is None:
        now = time.time()
    key = _make_key(alert)
    last = _store.get(key)
    if last is None:
        return False
    return (now - last) < _window_seconds


def record(alert: Alert, now: Optional[float] = None) -> None:
    """Record that an alert has been dispatched, updating the dedup store."""
    if now is None:
        now = time.time()
    key = _make_key(alert)
    _store[key] = now


def get_state() -> DedupState:
    """Return a snapshot of the current dedup state."""
    return DedupState(window_seconds=_window_seconds, entries=dict(_store))


def maybe_dispatch(alert: Alert, now: Optional[float] = None) -> bool:
    """Return True and record the alert if it is not a duplicate; False otherwise."""
    if now is None:
        now = time.time()
    if is_duplicate(alert, now=now):
        return False
    record(alert, now=now)
    return True
