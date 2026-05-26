"""Formatting helpers for circuit-breaker state."""
from __future__ import annotations

import time
from typing import List

from procwatch.circuit_breaker import BreakerEntry, CircuitState, _breakers

_STATE_LABEL = {
    CircuitState.CLOSED: "CLOSED   ",
    CircuitState.OPEN: "OPEN     ",
    CircuitState.HALF_OPEN: "HALF-OPEN",
}


def _fmt_age(ts: float | None) -> str:
    if ts is None:
        return "—"
    secs = int(time.monotonic() - ts)
    return f"{secs}s ago"


def format_breaker_line(key: str, entry: BreakerEntry) -> str:
    state_label = _STATE_LABEL.get(entry.state, entry.state.value)
    age = _fmt_age(entry.opened_at) if entry.state != CircuitState.CLOSED else "—"
    return (
        f"{key:<30}  {state_label}  "
        f"failures={entry.failures:<3}  opened={age}"
    )


def format_breaker_table() -> str:
    if not _breakers:
        return "circuit-breakers: none recorded"

    header = f"{'endpoint':<30}  {'state':<9}  failures     opened"
    sep = "-" * len(header)
    rows: List[str] = [header, sep]
    for key, entry in sorted(_breakers.items()):
        rows.append(format_breaker_line(key, entry))
    return "\n".join(rows)


def format_breaker_summary() -> str:
    total = len(_breakers)
    open_count = sum(
        1 for e in _breakers.values() if e.state == CircuitState.OPEN
    )
    half_open = sum(
        1 for e in _breakers.values() if e.state == CircuitState.HALF_OPEN
    )
    return (
        f"circuit-breakers: {total} tracked, "
        f"{open_count} open, {half_open} half-open"
    )
