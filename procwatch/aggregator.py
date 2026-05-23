"""Aggregates per-process snapshots into rolling statistics."""

from __future__ import annotations

from collections import deque
from dataclasses import dataclass, field
from typing import Deque, Dict, Optional

from procwatch.monitor import ProcessSnapshot

_DEFAULT_WINDOW = 10  # number of snapshots to keep per process

# pid -> deque of snapshots
_buckets: Dict[int, Deque[ProcessSnapshot]] = {}


@dataclass
class RollingStats:
    pid: int
    name: str
    count: int
    avg_cpu: float
    max_cpu: float
    avg_mem: float
    max_mem: float
    peak_snapshot: Optional[ProcessSnapshot] = field(default=None)


def reset_aggregator() -> None:
    """Clear all rolling data (useful in tests)."""
    _buckets.clear()


def push_snapshot(snapshot: ProcessSnapshot, window: int = _DEFAULT_WINDOW) -> None:
    """Add a snapshot to the rolling window for its process."""
    pid = snapshot.pid
    if pid not in _buckets:
        _buckets[pid] = deque(maxlen=window)
    _buckets[pid].append(snapshot)


def get_stats(pid: int) -> Optional[RollingStats]:
    """Return rolling statistics for *pid*, or None if no data exists."""
    snaps = _buckets.get(pid)
    if not snaps:
        return None

    cpus = [s.cpu_percent for s in snaps]
    mems = [s.memory_mb for s in snaps]
    peak = max(snaps, key=lambda s: s.cpu_percent)

    return RollingStats(
        pid=pid,
        name=snaps[-1].name,
        count=len(snaps),
        avg_cpu=sum(cpus) / len(cpus),
        max_cpu=max(cpus),
        avg_mem=sum(mems) / len(mems),
        max_mem=max(mems),
        peak_snapshot=peak,
    )


def all_stats() -> Dict[int, RollingStats]:
    """Return rolling statistics for every tracked process."""
    return {pid: get_stats(pid) for pid in _buckets if get_stats(pid) is not None}  # type: ignore[misc]
