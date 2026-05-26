"""Retry logic for webhook/notification dispatch with backoff."""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from typing import Callable, Any


@dataclass
class RetryConfig:
    max_attempts: int = 3
    base_delay: float = 1.0
    backoff_factor: float = 2.0
    max_delay: float = 30.0


@dataclass
class RetryResult:
    success: bool
    attempts: int
    last_error: str = ""
    value: Any = None


def _compute_delay(attempt: int, cfg: RetryConfig) -> float:
    """Return delay in seconds for the given attempt number (0-indexed)."""
    delay = cfg.base_delay * (cfg.backoff_factor ** attempt)
    return min(delay, cfg.max_delay)


def with_retry(
    fn: Callable[[], Any],
    cfg: RetryConfig | None = None,
    *,
    _sleep: Callable[[float], None] = time.sleep,
) -> RetryResult:
    """Call *fn* up to cfg.max_attempts times, backing off between failures.

    Returns a RetryResult describing the outcome.
    """
    if cfg is None:
        cfg = RetryConfig()

    last_error = ""
    for attempt in range(cfg.max_attempts):
        try:
            value = fn()
            return RetryResult(success=True, attempts=attempt + 1, value=value)
        except Exception as exc:  # noqa: BLE001
            last_error = str(exc)
            if attempt < cfg.max_attempts - 1:
                delay = _compute_delay(attempt, cfg)
                _sleep(delay)

    return RetryResult(success=False, attempts=cfg.max_attempts, last_error=last_error)


def retry_config_from_dict(data: dict) -> RetryConfig:
    """Build a RetryConfig from a plain dict (e.g. loaded from config file)."""
    return RetryConfig(
        max_attempts=int(data.get("max_attempts", 3)),
        base_delay=float(data.get("base_delay", 1.0)),
        backoff_factor=float(data.get("backoff_factor", 2.0)),
        max_delay=float(data.get("max_delay", 30.0)),
    )
