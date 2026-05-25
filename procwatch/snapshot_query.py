"""Query helpers for the snapshot store: filter, window, and summarise stored snapshots."""

from __future__ import annotations

import time
from dataclasses import dataclass
from typing import List, Optional

from procwatch.monitor import ProcessSnapshot
from procwatch.snapshot_store import load_snapshots


@dataclass
class SnapshotSummary:
    pid: int
    name: str
    count: int
    avg_cpu: float
    max_cpu: float
    avg_mem: float
    max_mem: float


def snapshots_in_window(
    seconds: float,
    pid: Optional[int] = None,
    snapshots: Optional[List[ProcessSnapshot]] = None,
) -> List[ProcessSnapshot]:
    """Return snapshots recorded within the last *seconds* seconds."""
    cutoff = time.time() - seconds
    source = snapshots if snapshots is not None else load_snapshots()
    result = [s for s in source if s.timestamp >= cutoff]
    if pid is not None:
        result = [s for s in result if s.pid == pid]
    return result


def summarise(snapshots: List[ProcessSnapshot]) -> Optional[SnapshotSummary]:
    """Compute a summary over a list of snapshots for a single PID.

    Returns None if the list is empty.
    """
    if not snapshots:
        return None
    pid = snapshots[0].pid
    name = snapshots[0].name
    cpu_values = [s.cpu_percent for s in snapshots]
    mem_values = [s.memory_mb for s in snapshots]
    return SnapshotSummary(
        pid=pid,
        name=name,
        count=len(snapshots),
        avg_cpu=sum(cpu_values) / len(cpu_values),
        max_cpu=max(cpu_values),
        avg_mem=sum(mem_values) / len(mem_values),
        max_mem=max(mem_values),
    )


def top_by_cpu(n: int = 5, snapshots: Optional[List[ProcessSnapshot]] = None) -> List[ProcessSnapshot]:
    """Return the *n* snapshots with the highest CPU usage."""
    source = snapshots if snapshots is not None else load_snapshots()
    return sorted(source, key=lambda s: s.cpu_percent, reverse=True)[:n]


def top_by_mem(n: int = 5, snapshots: Optional[List[ProcessSnapshot]] = None) -> List[ProcessSnapshot]:
    """Return the *n* snapshots with the highest memory usage."""
    source = snapshots if snapshots is not None else load_snapshots()
    return sorted(source, key=lambda s: s.memory_mb, reverse=True)[:n]
