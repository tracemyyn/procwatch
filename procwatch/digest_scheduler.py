"""Digest scheduler: fires a digest callback at a configurable interval."""

from __future__ import annotations

import time
from typing import Callable, Optional

from procwatch.digest import build_digest, format_digest, reset_digest, DigestReport

_last_flush: float = time.time()
_interval: float = 300.0  # default 5 minutes


def configure(interval_seconds: float) -> None:
    """Set the flush interval in seconds."""
    global _interval
    _interval = interval_seconds


def reset_digest_scheduler() -> None:
    """Reset the scheduler state and digest buffer."""
    global _last_flush
    _last_flush = time.time()
    reset_digest()


def maybe_flush(
    callback: Callable[[DigestReport, str], None],
    now: Optional[float] = None,
) -> bool:
    """Check elapsed time; if interval exceeded, build & deliver digest.

    Returns True if a flush occurred, False otherwise.
    """
    global _last_flush
    ts = now if now is not None else time.time()
    if ts - _last_flush < _interval:
        return False

    report = build_digest()
    text = format_digest(report)
    callback(report, text)
    _last_flush = ts
    reset_digest()
    return True


def seconds_until_next_flush(now: Optional[float] = None) -> float:
    """Return how many seconds remain until the next scheduled flush."""
    ts = now if now is not None else time.time()
    elapsed = ts - _last_flush
    remaining = _interval - elapsed
    return max(0.0, remaining)
