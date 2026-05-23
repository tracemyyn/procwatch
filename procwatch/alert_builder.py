"""Builds Alert objects from process snapshots and dispatches them with cooldown awareness."""

from typing import Optional

from procwatch.config import Config
from procwatch.monitor import ProcessSnapshot, exceeds_thresholds
from procwatch.notifier import Alert, dispatch
from procwatch import history


def build_alert(snapshot: ProcessSnapshot, config: Config) -> Alert:
    """Construct an Alert from a process snapshot and current config."""
    reasons = []
    if snapshot.cpu_percent > config.cpu_threshold:
        reasons.append(
            f"CPU {snapshot.cpu_percent:.1f}% > threshold {config.cpu_threshold}%"
        )
    if snapshot.memory_mb > config.memory_threshold_mb:
        reasons.append(
            f"Memory {snapshot.memory_mb:.1f}MB > threshold {config.memory_threshold_mb}MB"
        )

    return Alert(
        pid=snapshot.pid,
        process_name=snapshot.name,
        cpu_percent=snapshot.cpu_percent,
        memory_mb=snapshot.memory_mb,
        reason="; ".join(reasons) if reasons else "Resource threshold exceeded",
    )


def maybe_alert(
    snapshot: ProcessSnapshot,
    config: Config,
    cooldown_seconds: Optional[float] = None,
) -> bool:
    """Dispatch an alert for a snapshot if thresholds are exceeded and not in cooldown.

    Returns True if an alert was dispatched, False otherwise.
    """
    if not exceeds_thresholds(snapshot, config):
        return False

    effective_cooldown = (
        cooldown_seconds if cooldown_seconds is not None else config.cooldown_seconds
    )

    if history.is_in_cooldown(snapshot.pid, snapshot.name, effective_cooldown):
        return False

    alert = build_alert(snapshot, config)
    dispatch(alert, config)
    history.record_alert(snapshot.pid, snapshot.name)
    return True
