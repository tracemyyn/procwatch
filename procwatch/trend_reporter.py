"""Formats trend analysis results for display and logging."""

from __future__ import annotations

from typing import Dict, List

from procwatch.aggregator import all_stats, RollingStats
from procwatch.monitor import ProcessSnapshot
from procwatch.trend import TrendResult, analyse_cpu_trend, analyse_mem_trend

_DIRECTION_ICON: Dict[str, str] = {
    "rising": "↑",
    "falling": "↓",
    "stable": "→",
}


def _snapshots_from_stats(stats: RollingStats) -> List[ProcessSnapshot]:
    """Reconstruct a minimal snapshot list from aggregator stats.

    Because the aggregator stores only summary data we synthesise two
    boundary snapshots (avg and max) so trend functions have something
    to work with when the raw deque is unavailable.
    """
    low = ProcessSnapshot(
        pid=stats.pid, name=stats.name,
        cpu_percent=stats.avg_cpu, memory_mb=stats.avg_mem,
    )
    high = ProcessSnapshot(
        pid=stats.pid, name=stats.name,
        cpu_percent=stats.max_cpu, memory_mb=stats.max_mem,
    )
    return [low, high]


def format_trend_line(cpu_trend: TrendResult, mem_trend: TrendResult) -> str:
    """Return a single-line summary for a process's CPU and memory trends."""
    cpu_icon = _DIRECTION_ICON.get(cpu_trend.direction, "?")
    mem_icon = _DIRECTION_ICON.get(mem_trend.direction, "?")
    return (
        f"[{cpu_trend.pid}] {cpu_trend.name:<20s} "
        f"CPU {cpu_icon} {cpu_trend.slope:+.2f}%/sample  "
        f"MEM {mem_icon} {mem_trend.slope:+.2f} MB/sample"
    )


def build_trend_report() -> str:
    """Build a multi-line trend report for all tracked processes."""
    stats_map = all_stats()
    if not stats_map:
        return "No process data available."

    lines: List[str] = ["=== Trend Report ==="]
    for stats in stats_map.values():
        snaps = _snapshots_from_stats(stats)
        cpu_trend = analyse_cpu_trend(snaps)
        mem_trend = analyse_mem_trend(snaps)
        if cpu_trend and mem_trend:
            lines.append(format_trend_line(cpu_trend, mem_trend))

    return "\n".join(lines) if len(lines) > 1 else "No trends computed."
