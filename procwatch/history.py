"""Tracks alert history to avoid duplicate notifications within a cooldown window."""

import time
from dataclasses import dataclass, field
from typing import Dict, Optional, Tuple


@dataclass
class HistoryEntry:
    pid: int
    process_name: str
    last_alerted_at: float
    alert_count: int = 1


# Key: (pid, process_name)
_history: Dict[Tuple[int, str], HistoryEntry] = {}


def _make_key(pid: int, process_name: str) -> Tuple[int, str]:
    return (pid, process_name)


def record_alert(pid: int, process_name: str) -> None:
    """Record that an alert was dispatched for this process."""
    key = _make_key(pid, process_name)
    if key in _history:
        entry = _history[key]
        entry.last_alerted_at = time.time()
        entry.alert_count += 1
    else:
        _history[key] = HistoryEntry(
            pid=pid,
            process_name=process_name,
            last_alerted_at=time.time(),
        )


def is_in_cooldown(pid: int, process_name: str, cooldown_seconds: float) -> bool:
    """Return True if this process was alerted within the cooldown window."""
    key = _make_key(pid, process_name)
    if key not in _history:
        return False
    elapsed = time.time() - _history[key].last_alerted_at
    return elapsed < cooldown_seconds


def get_entry(pid: int, process_name: str) -> Optional[HistoryEntry]:
    """Return the history entry for a process, or None if not found."""
    return _history.get(_make_key(pid, process_name))


def clear_history() -> None:
    """Clear all alert history (useful for testing or resets)."""
    _history.clear()


def prune_old_entries(max_age_seconds: float) -> int:
    """Remove entries older than max_age_seconds. Returns number removed."""
    now = time.time()
    to_remove = [
        key for key, entry in _history.items()
        if (now - entry.last_alerted_at) > max_age_seconds
    ]
    for key in to_remove:
        del _history[key]
    return len(to_remove)
