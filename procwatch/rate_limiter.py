"""Global rate limiter that caps the total number of alerts dispatched per time window."""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from typing import Optional

_DEFAULT_WINDOW_SECONDS = 60
_DEFAULT_MAX_ALERTS = 20


@dataclass
class RateLimiterState:
    window_seconds: int
    max_alerts: int
    window_start: float = field(default_factory=time.monotonic)
    alert_count: int = 0


_state: Optional[RateLimiterState] = None


def reset_rate_limiter(
    window_seconds: int = _DEFAULT_WINDOW_SECONDS,
    max_alerts: int = _DEFAULT_MAX_ALERTS,
) -> RateLimiterState:
    """Initialise (or reset) the global rate limiter."""
    global _state
    _state = RateLimiterState(
        window_seconds=window_seconds,
        max_alerts=max_alerts,
        window_start=time.monotonic(),
        alert_count=0,
    )
    return _state


def _ensure_state() -> RateLimiterState:
    global _state
    if _state is None:
        _state = RateLimiterState(
            window_seconds=_DEFAULT_WINDOW_SECONDS,
            max_alerts=_DEFAULT_MAX_ALERTS,
        )
    return _state


def _maybe_roll_window(state: RateLimiterState) -> None:
    """Advance the window if the current one has expired."""
    now = time.monotonic()
    if now - state.window_start >= state.window_seconds:
        state.window_start = now
        state.alert_count = 0


def is_allowed() -> bool:
    """Return True and increment the counter if the global rate limit has not been hit."""
    state = _ensure_state()
    _maybe_roll_window(state)
    if state.alert_count < state.max_alerts:
        state.alert_count += 1
        return True
    return False


def get_state() -> Optional[RateLimiterState]:
    """Return the current limiter state without mutating it."""
    return _state


def remaining() -> int:
    """Return how many alerts are still allowed in the current window."""
    state = _ensure_state()
    _maybe_roll_window(state)
    return max(0, state.max_alerts - state.alert_count)
