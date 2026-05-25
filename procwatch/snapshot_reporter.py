"""Format stored snapshot data into human-readable reports."""

from __future__ import annotations

from typing import List, Optional

from procwatch.monitor import ProcessSnapshot
from procwatch.snapshot_query import SnapshotSummary, summarise, top_by_cpu, top_by_mem
from procwatch.snapshot_store import load_for_pid, load_snapshots

_COL = "{:<8} {:<20} {:>10} {:>12}"
_HEADER = _COL.format("PID", "NAME", "CPU %", "MEM MB")
_SEP = "-" * 54


def _fmt_snap(s: ProcessSnapshot) -> str:
    return _COL.format(s.pid, s.name[:20], f"{s.cpu_percent:.1f}", f"{s.memory_mb:.1f}")


def format_top_cpu_report(n: int = 5, snapshots: Optional[List[ProcessSnapshot]] = None) -> str:
    """Return a formatted table of the top-N CPU-consuming snapshots."""
    source = snapshots if snapshots is not None else load_snapshots()
    top = top_by_cpu(n=n, snapshots=source)
    lines = [f"Top {n} by CPU", _SEP, _HEADER, _SEP]
    if not top:
        lines.append("  (no data)")
    else:
        lines.extend(_fmt_snap(s) for s in top)
    lines.append(_SEP)
    return "\n".join(lines)


def format_top_mem_report(n: int = 5, snapshots: Optional[List[ProcessSnapshot]] = None) -> str:
    """Return a formatted table of the top-N memory-consuming snapshots."""
    source = snapshots if snapshots is not None else load_snapshots()
    top = top_by_mem(n=n, snapshots=source)
    lines = [f"Top {n} by Memory", _SEP, _HEADER, _SEP]
    if not top:
        lines.append("  (no data)")
    else:
        lines.extend(_fmt_snap(s) for s in top)
    lines.append(_SEP)
    return "\n".join(lines)


def format_pid_summary(pid: int) -> str:
    """Return a text summary of stored snapshots for *pid*."""
    snaps = load_for_pid(pid)
    summary: Optional[SnapshotSummary] = summarise(snaps)
    if summary is None:
        return f"No stored snapshots for PID {pid}."
    lines = [
        f"Summary for PID {pid} ({summary.name})",
        _SEP,
        f"  Samples  : {summary.count}",
        f"  Avg CPU  : {summary.avg_cpu:.2f} %",
        f"  Max CPU  : {summary.max_cpu:.2f} %",
        f"  Avg Mem  : {summary.avg_mem:.2f} MB",
        f"  Max Mem  : {summary.max_mem:.2f} MB",
        _SEP,
    ]
    return "\n".join(lines)
