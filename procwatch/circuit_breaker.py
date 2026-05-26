"""Circuit breaker for webhook/notification dispatch.

Prevents repeated calls to a failing endpoint by opening the circuit
after a configurable number of consecutive failures.
"""
from __future__ import annotations

import time
from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, Optional


class CircuitState(str, Enum):
    CLOSED = "closed"      # normal — calls pass through
    OPEN = "open"          # failing — calls are blocked
    HALF_OPEN = "half_open"  # probing — one call allowed


@dataclass
class BreakerEntry:
    state: CircuitState = CircuitState.CLOSED
    failures: int = 0
    opened_at: Optional[float] = None
    last_failure_at: Optional[float] = None


@dataclass
class BreakerConfig:
    failure_threshold: int = 3       # failures before opening
    recovery_timeout: float = 60.0   # seconds before half-open probe


_breakers: Dict[str, BreakerEntry] = {}
_config: BreakerConfig = BreakerConfig()


def reset_breaker() -> None:
    """Clear all breaker state (test helper)."""
    _breakers.clear()


def configure(failure_threshold: int = 3, recovery_timeout: float = 60.0) -> None:
    global _config
    _config = BreakerConfig(
        failure_threshold=failure_threshold,
        recovery_timeout=recovery_timeout,
    )


def _ensure(key: str) -> BreakerEntry:
    if key not in _breakers:
        _breakers[key] = BreakerEntry()
    return _breakers[key]


def is_allowed(key: str) -> bool:
    """Return True if a call for *key* should be attempted."""
    entry = _ensure(key)
    now = time.monotonic()

    if entry.state == CircuitState.CLOSED:
        return True

    if entry.state == CircuitState.OPEN:
        elapsed = now - (entry.opened_at or now)
        if elapsed >= _config.recovery_timeout:
            entry.state = CircuitState.HALF_OPEN
            return True
        return False

    # HALF_OPEN — allow the single probe
    return True


def record_success(key: str) -> None:
    """Call after a successful dispatch to close / reset the circuit."""
    entry = _ensure(key)
    entry.state = CircuitState.CLOSED
    entry.failures = 0
    entry.opened_at = None


def record_failure(key: str) -> CircuitState:
    """Call after a failed dispatch; returns the new circuit state."""
    entry = _ensure(key)
    entry.failures += 1
    entry.last_failure_at = time.monotonic()

    if entry.failures >= _config.failure_threshold:
        entry.state = CircuitState.OPEN
        entry.opened_at = time.monotonic()
    return entry.state


def get_entry(key: str) -> Optional[BreakerEntry]:
    return _breakers.get(key)
