"""Integrate silence windows into the alert dispatch pipeline."""

from __future__ import annotations

from typing import List, Optional

from procwatch.config import Config
from procwatch.notifier import Alert
from procwatch.silencer import (
    SilenceWindow,
    add_window,
    is_silenced,
    reset_silencer,
    windows_from_config,
)


def init_silencer_from_config(cfg: Config) -> List[SilenceWindow]:
    """Read silence_windows from *cfg* and register them.

    cfg.extra is expected to carry a ``silence_windows`` list of dicts.
    Returns the list of windows that were added.
    """
    raw: List[dict] = getattr(cfg, "extra", {}).get("silence_windows", [])
    reset_silencer()
    windows = windows_from_config(raw)
    for w in windows:
        add_window(w)
    return windows


def should_suppress_alert(alert: Alert) -> bool:
    """Return True if *alert* should be suppressed due to an active silence window."""
    return is_silenced(alert.process_name)


def filter_alerts(alerts: List[Alert]) -> List[Alert]:
    """Return only the alerts that are *not* currently silenced."""
    return [a for a in alerts if not should_suppress_alert(a)]


def maybe_dispatch(
    alert: Alert,
    dispatch_fn,  # callable[[Alert], bool]
) -> Optional[bool]:
    """Dispatch *alert* unless it is silenced.

    Returns None when suppressed, otherwise the return value of *dispatch_fn*.
    """
    if should_suppress_alert(alert):
        return None
    return dispatch_fn(alert)
