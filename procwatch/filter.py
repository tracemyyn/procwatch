"""Process filtering utilities for procwatch.

Allows users to include or exclude processes by name, pid, or user.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from fnmatch import fnmatch
from typing import List, Optional

from procwatch.monitor import ProcessSnapshot


@dataclass
class FilterRules:
    """Rules that determine which processes are monitored."""

    include_names: List[str] = field(default_factory=list)  # glob patterns
    exclude_names: List[str] = field(default_factory=list)  # glob patterns
    include_users: List[str] = field(default_factory=list)
    exclude_pids: List[int] = field(default_factory=list)
    min_cpu: float = 0.0
    min_memory: float = 0.0


def _matches_any(value: str, patterns: List[str]) -> bool:
    """Return True if *value* matches at least one glob pattern."""
    return any(fnmatch(value, p) for p in patterns)


def should_include(snapshot: ProcessSnapshot, rules: FilterRules) -> bool:
    """Return True if *snapshot* passes all filter *rules*."""
    if snapshot.pid in rules.exclude_pids:
        return False

    if rules.include_names and not _matches_any(snapshot.name, rules.include_names):
        return False

    if rules.exclude_names and _matches_any(snapshot.name, rules.exclude_names):
        return False

    if rules.include_users and snapshot.username not in rules.include_users:
        return False

    if snapshot.cpu_percent < rules.min_cpu:
        return False

    if snapshot.memory_mb < rules.min_memory:
        return False

    return True


def apply_filters(
    snapshots: List[ProcessSnapshot],
    rules: Optional[FilterRules] = None,
) -> List[ProcessSnapshot]:
    """Return the subset of *snapshots* that satisfy *rules*.

    If *rules* is None an empty :class:`FilterRules` is used, which
    accepts every process.
    """
    if rules is None:
        rules = FilterRules()
    return [s for s in snapshots if should_include(s, rules)]


def rules_from_config(cfg_dict: dict) -> FilterRules:
    """Build a :class:`FilterRules` from the ``filter`` section of a config dict."""
    section = cfg_dict.get("filter", {})
    return FilterRules(
        include_names=section.get("include_names", []),
        exclude_names=section.get("exclude_names", []),
        include_users=section.get("include_users", []),
        exclude_pids=section.get("exclude_pids", []),
        min_cpu=float(section.get("min_cpu", 0.0)),
        min_memory=float(section.get("min_memory", 0.0)),
    )
