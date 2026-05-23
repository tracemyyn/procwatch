"""Detect resource usage trends from rolling aggregator data."""

from __future__ import annotations

from dataclasses import dataclass
from typing import List, Optional

from procwatch.monitor import ProcessSnapshot


@dataclass
class TrendResult:
    pid: int
    name: str
    direction: str          # "rising", "falling", "stable"
    slope: float            # average change per sample
    samples: int


def _linear_slope(values: List[float]) -> float:
    """Return the mean first-difference (simple slope estimate)."""
    if len(values) < 2:
        return 0.0
    diffs = [values[i + 1] - values[i] for i in range(len(values) - 1)]
    return sum(diffs) / len(diffs)


def analyse_cpu_trend(
    snapshots: List[ProcessSnapshot],
    rising_threshold: float = 2.0,
    falling_threshold: float = -2.0,
) -> Optional[TrendResult]:
    """Analyse CPU trend from an ordered list of snapshots.

    Returns None when fewer than 2 snapshots are provided.
    """
    if len(snapshots) < 2:
        return None

    cpus = [s.cpu_percent for s in snapshots]
    slope = _linear_slope(cpus)

    if slope >= rising_threshold:
        direction = "rising"
    elif slope <= falling_threshold:
        direction = "falling"
    else:
        direction = "stable"

    return TrendResult(
        pid=snapshots[-1].pid,
        name=snapshots[-1].name,
        direction=direction,
        slope=round(slope, 4),
        samples=len(snapshots),
    )


def analyse_mem_trend(
    snapshots: List[ProcessSnapshot],
    rising_threshold: float = 5.0,
    falling_threshold: float = -5.0,
) -> Optional[TrendResult]:
    """Analyse memory trend from an ordered list of snapshots."""
    if len(snapshots) < 2:
        return None

    mems = [s.memory_mb for s in snapshots]
    slope = _linear_slope(mems)

    if slope >= rising_threshold:
        direction = "rising"
    elif slope <= falling_threshold:
        direction = "falling"
    else:
        direction = "stable"

    return TrendResult(
        pid=snapshots[-1].pid,
        name=snapshots[-1].name,
        direction=direction,
        slope=round(slope, 4),
        samples=len(snapshots),
    )
