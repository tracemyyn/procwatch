"""Rate-limiting / throttle helpers for procwatch alerts.

Provides a simple token-bucket throttler so that a noisy process cannot
flood webhooks or desktop notifications beyond a configurable rate.
"""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from typing import Dict, Tuple

# (process_name, pid) -> (tokens, last_refill_timestamp)
_buckets: Dict[Tuple[str, int], Tuple[float, float]] = {}


@dataclass
class ThrottleConfig:
    """Parameters for the token-bucket algorithm."""

    max_tokens: float = 5.0      # burst capacity
    refill_rate: float = 1.0     # tokens added per second
    cost: float = 1.0            # tokens consumed per alert


def _refill(tokens: float, last_refill: float, cfg: ThrottleConfig) -> Tuple[float, float]:
    """Return (new_tokens, now) after applying elapsed-time refill."""
    now = time.monotonic()
    elapsed = now - last_refill
    new_tokens = min(cfg.max_tokens, tokens + elapsed * cfg.refill_rate)
    return new_tokens, now


def reset_buckets() -> None:
    """Clear all throttle state (useful in tests)."""
    _buckets.clear()


def is_allowed(name: str, pid: int, cfg: ThrottleConfig | None = None) -> bool:
    """Return True and consume a token if the alert should be sent.

    Returns False when the bucket is empty (alert should be suppressed).
    """
    if cfg is None:
        cfg = ThrottleConfig()

    key = (name, pid)
    if key not in _buckets:
        _buckets[key] = (cfg.max_tokens, time.monotonic())

    tokens, last_refill = _buckets[key]
    tokens, now = _refill(tokens, last_refill, cfg)

    if tokens < cfg.cost:
        _buckets[key] = (tokens, now)
        return False

    _buckets[key] = (tokens - cfg.cost, now)
    return True


def get_bucket(name: str, pid: int) -> Tuple[float, float] | None:
    """Return the current (tokens, last_refill) for a key, or None."""
    return _buckets.get((name, pid))
