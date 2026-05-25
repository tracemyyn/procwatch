"""watchdog.py — Detects and reports stale/unresponsive watch cycles.

A cycle is considered stale when the scheduler has not ticked within
`stale_seconds` of the expected interval.  The watchdog can be polled
or asked to raise an alert via the notifier.
"""
from __future__ import annotations

import time
from dataclasses import dataclass, field
from typing import Optional

from procwatch.scheduler import get_state

# Module-level state so tests can reset it easily.
_watchdog: Optional["WatchdogState"] = None


@dataclass
class WatchdogState:
    interval_seconds: float
    stale_seconds: float
    started_at: float = field(default_factory=time.time)
    last_ok_at: float = field(default_factory=time.time)
    stale_count: int = 0


def reset_watchdog() -> None:
    """Clear module-level watchdog state (useful in tests)."""
    global _watchdog
    _watchdog = None


def init_watchdog(interval_seconds: float, stale_factor: float = 3.0) -> WatchdogState:
    """Initialise (or re-initialise) the watchdog.

    *stale_factor* multiples *interval_seconds* to derive the stale
    threshold — e.g. factor 3 means three missed ticks before stale.
    """
    global _watchdog
    stale_seconds = interval_seconds * stale_factor
    _watchdog = WatchdogState(
        interval_seconds=interval_seconds,
        stale_seconds=stale_seconds,
    )
    return _watchdog


def check_stale(now: Optional[float] = None) -> bool:
    """Return True when the scheduler appears stale.

    Uses the scheduler's *last_tick_at* timestamp when available,
    otherwise falls back to the watchdog's own *last_ok_at*.
    """
    global _watchdog
    if _watchdog is None:
        return False

    now = now if now is not None else time.time()
    state = get_state()
    last_tick = state.last_tick_at if (state and state.last_tick_at) else _watchdog.last_ok_at

    elapsed = now - last_tick
    if elapsed > _watchdog.stale_seconds:
        _watchdog.stale_count += 1
        return True

    _watchdog.last_ok_at = now
    return False


def get_watchdog() -> Optional[WatchdogState]:
    """Return current watchdog state or None if uninitialised."""
    return _watchdog


def stale_summary() -> str:
    """Return a human-readable summary of the current watchdog status."""
    wd = _watchdog
    if wd is None:
        return "watchdog: not initialised"
    stale = check_stale()
    status = "STALE" if stale else "OK"
    return (
        f"watchdog: {status} | interval={wd.interval_seconds}s "
        f"stale_threshold={wd.stale_seconds}s stale_count={wd.stale_count}"
    )
