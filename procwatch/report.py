"""Snapshot reporting: format and summarise process alert data."""

from __future__ import annotations

from datetime import datetime
from typing import List, Optional

from procwatch.history import HistoryEntry, get_entry
from procwatch.monitor import ProcessSnapshot


def _fmt_row(snap: ProcessSnapshot, entry: Optional[HistoryEntry]) -> str:
    """Return a single-line summary string for *snap*."""
    alert_count = entry.alert_count if entry else 0
    last_seen = (
        datetime.fromtimestamp(entry.last_alert_ts).strftime("%H:%M:%S")
        if entry
        else "never"
    )
    return (
        f"  [{snap.pid:>6}] {snap.name:<20} "
        f"cpu={snap.cpu_percent:5.1f}%  mem={snap.memory_mb:7.1f} MB  "
        f"alerts={alert_count}  last={last_seen}"
    )


def format_snapshot_table(snapshots: List[ProcessSnapshot]) -> str:
    """Return a human-readable table of *snapshots* with history context."""
    if not snapshots:
        return "No processes matched."

    lines = [
        f"{'PID':>8}  {'NAME':<20} {'CPU':>7}  {'MEM':>10}  {'ALERTS':>6}  LAST ALERT",
        "-" * 70,
    ]
    for snap in snapshots:
        entry = get_entry(snap.name, snap.pid)
        lines.append(_fmt_row(snap, entry))
    return "\n".join(lines)


def format_summary(snapshots: List[ProcessSnapshot]) -> str:
    """Return a one-line summary suitable for a notification body."""
    if not snapshots:
        return "No spikes detected."
    names = ", ".join(sorted({s.name for s in snapshots}))
    max_cpu = max(s.cpu_percent for s in snapshots)
    max_mem = max(s.memory_mb for s in snapshots)
    return (
        f"{len(snapshots)} process(es) spiking — {names} "
        f"| peak cpu={max_cpu:.1f}% mem={max_mem:.1f} MB"
    )


def format_alert_line(snap: ProcessSnapshot) -> str:
    """Return a compact single-line alert string for *snap*."""
    return (
        f"ALERT pid={snap.pid} name={snap.name!r} "
        f"cpu={snap.cpu_percent:.1f}% mem={snap.memory_mb:.1f} MB"
    )
