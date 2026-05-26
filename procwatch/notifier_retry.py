"""Wraps notifier.dispatch with retry logic for resilient alert delivery."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Callable

from procwatch.notifier import Alert, dispatch
from procwatch.retry import RetryConfig, RetryResult, with_retry


@dataclass
class DispatchResult:
    """Outcome of a resilient dispatch attempt."""
    delivered: bool
    attempts: int
    channel: str
    last_error: str = ""


def _make_dispatch_fn(
    alert: Alert,
    webhook_url: str | None,
    use_desktop: bool,
) -> Callable[[], bool]:
    """Return a zero-argument callable that runs dispatch and raises on failure."""
    def _fn() -> bool:
        ok = dispatch(alert, webhook_url=webhook_url, use_desktop=use_desktop)
        if not ok:
            raise RuntimeError("dispatch returned False")
        return ok
    return _fn


def dispatch_with_retry(
    alert: Alert,
    *,
    webhook_url: str | None = None,
    use_desktop: bool = False,
    retry_cfg: RetryConfig | None = None,
    _sleep_fn=None,
) -> DispatchResult:
    """Dispatch *alert* with automatic retries on transient failures.

    Parameters
    ----------
    alert:        The alert to dispatch.
    webhook_url:  Optional webhook endpoint.
    use_desktop:  Whether to attempt a desktop notification.
    retry_cfg:    Retry parameters; uses defaults when *None*.
    """
    if retry_cfg is None:
        retry_cfg = RetryConfig()

    channel = "webhook" if webhook_url else ("desktop" if use_desktop else "none")
    fn = _make_dispatch_fn(alert, webhook_url, use_desktop)

    kwargs = {}
    if _sleep_fn is not None:
        kwargs["_sleep"] = _sleep_fn

    result: RetryResult = with_retry(fn, retry_cfg, **kwargs)

    return DispatchResult(
        delivered=result.success,
        attempts=result.attempts,
        channel=channel,
        last_error=result.last_error,
    )
