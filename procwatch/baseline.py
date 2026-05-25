"""Baseline profiling: establish normal resource usage per process name."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional

from procwatch.monitor import ProcessSnapshot

_baselines: Dict[str, "BaselineProfile"] = {}


@dataclass
class BaselineProfile:
    name: str
    cpu_samples: List[float] = field(default_factory=list)
    mem_samples: List[float] = field(default_factory=list)

    @property
    def avg_cpu(self) -> float:
        return sum(self.cpu_samples) / len(self.cpu_samples) if self.cpu_samples else 0.0

    @property
    def avg_mem(self) -> float:
        return sum(self.mem_samples) / len(self.mem_samples) if self.mem_samples else 0.0

    @property
    def sample_count(self) -> int:
        return len(self.cpu_samples)


def reset_baselines() -> None:
    """Clear all stored baseline profiles (useful in tests)."""
    _baselines.clear()


def record_snapshot(snap: ProcessSnapshot, max_samples: int = 60) -> BaselineProfile:
    """Add a snapshot's metrics to the baseline for its process name."""
    profile = _baselines.setdefault(snap.name, BaselineProfile(name=snap.name))
    profile.cpu_samples.append(snap.cpu_percent)
    profile.mem_samples.append(snap.memory_mb)
    if len(profile.cpu_samples) > max_samples:
        profile.cpu_samples = profile.cpu_samples[-max_samples:]
        profile.mem_samples = profile.mem_samples[-max_samples:]
    return profile


def get_profile(name: str) -> Optional[BaselineProfile]:
    """Return the baseline profile for a process name, or None."""
    return _baselines.get(name)


def is_cpu_spike(snap: ProcessSnapshot, multiplier: float = 2.0) -> bool:
    """Return True if the snapshot CPU exceeds multiplier * baseline average."""
    profile = get_profile(snap.name)
    if profile is None or profile.sample_count < 5:
        return False
    return snap.cpu_percent > profile.avg_cpu * multiplier


def is_mem_spike(snap: ProcessSnapshot, multiplier: float = 2.0) -> bool:
    """Return True if the snapshot memory exceeds multiplier * baseline average."""
    profile = get_profile(snap.name)
    if profile is None or profile.sample_count < 5:
        return False
    return snap.memory_mb > profile.avg_mem * multiplier


def all_profiles() -> Dict[str, BaselineProfile]:
    """Return a copy of all stored baseline profiles."""
    return dict(_baselines)
