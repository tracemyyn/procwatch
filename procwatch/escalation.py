"""Escalation policy: upgrade alert severity based on repeated spikes."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, Optional

# Severity levels in ascending order
LEVELS = ["info", "warning", "critical"]

_state: Dict[str, int] = {}  # key -> consecutive spike count


@dataclass
class EscalationResult:
    pid: int
    name: str
    severity: str
    consecutive: int


def reset_escalation() -> None:
    """Clear all escalation counters (useful for tests)."""
    _state.clear()


def _make_key(pid: int, name: str) -> str:
    return f"{pid}:{name}"


def record_spike(pid: int, name: str) -> EscalationResult:
    """Record a spike for the given process and return the current severity."""
    key = _make_key(pid, name)
    _state[key] = _state.get(key, 0) + 1
    consecutive = _state[key]
    severity = _level_for(consecutive)
    return EscalationResult(pid=pid, name=name, severity=severity, consecutive=consecutive)


def clear_spike(pid: int, name: str) -> None:
    """Reset the consecutive counter when a process returns to normal."""
    key = _make_key(pid, name)
    _state.pop(key, None)


def get_severity(pid: int, name: str) -> Optional[str]:
    """Return current severity for a process, or None if no spikes recorded."""
    key = _make_key(pid, name)
    count = _state.get(key)
    if count is None:
        return None
    return _level_for(count)


def _level_for(consecutive: int) -> str:
    """Map consecutive spike count to a severity level."""
    if consecutive >= 5:
        return LEVELS[2]  # critical
    if consecutive >= 2:
        return LEVELS[1]  # warning
    return LEVELS[0]      # info
