"""correlator.py — correlate alerts across processes to detect system-wide resource pressure."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional
import time

from procwatch.notifier import Alert


@dataclass
class CorrelationWindow:
    alerts: List[Alert] = field(default_factory=list)
    started_at: float = field(default_factory=time.monotonic)


@dataclass
class CorrelationResult:
    triggered: bool
    alert_count: int
    unique_pids: int
    pressure_type: str  # 'cpu', 'mem', 'mixed', or 'none'
    window_seconds: float


_state: Optional[CorrelationWindow] = None
_window_seconds: float = 30.0
_min_alerts: int = 3


def reset_correlator(window_seconds: float = 30.0, min_alerts: int = 3) -> None:
    """Reset correlator state; call between tests or on startup."""
    global _state, _window_seconds, _min_alerts
    _state = CorrelationWindow()
    _window_seconds = window_seconds
    _min_alerts = min_alerts


def _ensure_state() -> CorrelationWindow:
    global _state
    if _state is None:
        _state = CorrelationWindow()
    return _state


def _evict_stale(win: CorrelationWindow) -> None:
    cutoff = time.monotonic() - _window_seconds
    win.alerts = [a for a in win.alerts if a.timestamp >= cutoff]


def record_alert(alert: Alert) -> None:
    """Add an alert to the rolling correlation window."""
    win = _ensure_state()
    win.alerts.append(alert)
    _evict_stale(win)


def analyse() -> CorrelationResult:
    """Return a CorrelationResult describing current system-wide pressure."""
    win = _ensure_state()
    _evict_stale(win)

    alerts = win.alerts
    count = len(alerts)
    unique_pids = len({a.pid for a in alerts})

    if count < _min_alerts:
        return CorrelationResult(
            triggered=False,
            alert_count=count,
            unique_pids=unique_pids,
            pressure_type="none",
            window_seconds=_window_seconds,
        )

    cpu_alerts = sum(1 for a in alerts if a.cpu_percent is not None and a.cpu_percent > 0)
    mem_alerts = sum(1 for a in alerts if a.mem_percent is not None and a.mem_percent > 0)

    if cpu_alerts > 0 and mem_alerts > 0:
        pressure_type = "mixed"
    elif cpu_alerts > 0:
        pressure_type = "cpu"
    else:
        pressure_type = "mem"

    return CorrelationResult(
        triggered=True,
        alert_count=count,
        unique_pids=unique_pids,
        pressure_type=pressure_type,
        window_seconds=_window_seconds,
    )


def format_correlation_line(result: CorrelationResult) -> str:
    """Return a human-readable summary of a CorrelationResult."""
    if not result.triggered:
        return f"[correlator] no system pressure detected ({result.alert_count} alerts in window)"
    return (
        f"[correlator] SYSTEM PRESSURE detected: {result.alert_count} alerts across "
        f"{result.unique_pids} processes ({result.pressure_type}) "
        f"in last {result.window_seconds:.0f}s"
    )
