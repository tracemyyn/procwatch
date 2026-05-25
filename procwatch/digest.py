"""Periodic digest: summarises recent alerts into a single report batch."""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from typing import List, Optional

from procwatch.history import HistoryEntry, all_entries
from procwatch.notifier import Alert

# Module-level digest state
_digest_entries: List[Alert] = []
_digest_start: float = time.time()


@dataclass
class DigestReport:
    period_start: float
    period_end: float
    total_alerts: int
    top_offenders: List[str]  # list of "pid:name" strings
    lines: List[str] = field(default_factory=list)


def reset_digest() -> None:
    """Clear accumulated alerts and reset the window start time."""
    global _digest_entries, _digest_start
    _digest_entries = []
    _digest_start = time.time()


def add_to_digest(alert: Alert) -> None:
    """Accumulate an alert into the current digest window."""
    _digest_entries.append(alert)


def build_digest(max_offenders: int = 5) -> DigestReport:
    """Build a DigestReport from all accumulated alerts."""
    now = time.time()
    counts: dict[str, int] = {}
    for alert in _digest_entries:
        key = f"{alert.pid}:{alert.name}"
        counts[key] = counts.get(key, 0) + 1

    sorted_offenders = sorted(counts, key=lambda k: counts[k], reverse=True)
    top = sorted_offenders[:max_offenders]

    lines = [f"  {k} — {counts[k]} alert(s)" for k in top]

    return DigestReport(
        period_start=_digest_start,
        period_end=now,
        total_alerts=len(_digest_entries),
        top_offenders=top,
        lines=lines,
    )


def format_digest(report: DigestReport) -> str:
    """Return a human-readable digest string."""
    duration = report.period_end - report.period_start
    header = (
        f"=== ProcWatch Digest ===\n"
        f"Window: {duration:.0f}s | Total alerts: {report.total_alerts}"
    )
    if not report.lines:
        return header + "\n  (no alerts in this window)"
    body = "\nTop offenders:\n" + "\n".join(report.lines)
    return header + body
