"""Anomaly detection: flag processes whose current metrics deviate
from their established baseline by more than a configurable number
of standard deviations."""

from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Optional

from procwatch.baseline import get_profile
from procwatch.monitor import ProcessSnapshot


@dataclass
class AnomalyResult:
    pid: int
    name: str
    cpu_z: Optional[float]   # z-score for CPU, None if insufficient data
    mem_z: Optional[float]   # z-score for memory
    cpu_anomaly: bool
    mem_anomaly: bool


def _z_score(value: float, mean: float, stddev: float) -> Optional[float]:
    """Return z-score, or None when stddev is effectively zero."""
    if stddev < 1e-9:
        return None
    return (value - mean) / stddev


def _stddev(profile) -> tuple[float, float]:
    """Compute (cpu_stddev, mem_stddev) from a BaselineProfile."""
    cpu_var = (profile.cpu_m2 / profile.count) if profile.count > 1 else 0.0
    mem_var = (profile.mem_m2 / profile.count) if profile.count > 1 else 0.0
    return math.sqrt(cpu_var), math.sqrt(mem_var)


def analyse_anomaly(
    snap: ProcessSnapshot,
    z_threshold: float = 3.0,
    min_samples: int = 10,
) -> Optional[AnomalyResult]:
    """Return an AnomalyResult if a baseline profile exists and has
    enough samples, otherwise return None."""
    profile = get_profile(snap.pid)
    if profile is None or profile.count < min_samples:
        return None

    cpu_std, mem_std = _stddev(profile)
    cpu_z = _z_score(snap.cpu_percent, profile.avg_cpu, cpu_std)
    mem_z = _z_score(snap.memory_mb, profile.avg_mem, mem_std)

    cpu_anomaly = cpu_z is not None and abs(cpu_z) >= z_threshold
    mem_anomaly = mem_z is not None and abs(mem_z) >= z_threshold

    return AnomalyResult(
        pid=snap.pid,
        name=snap.name,
        cpu_z=cpu_z,
        mem_z=mem_z,
        cpu_anomaly=cpu_anomaly,
        mem_anomaly=mem_anomaly,
    )


def analyse_all(
    snapshots: list[ProcessSnapshot],
    z_threshold: float = 3.0,
    min_samples: int = 10,
) -> list[AnomalyResult]:
    """Run anomaly detection over a list of snapshots; returns only
    results where at least one metric is anomalous."""
    results = []
    for snap in snapshots:
        result = analyse_anomaly(snap, z_threshold, min_samples)
        if result and (result.cpu_anomaly or result.mem_anomaly):
            results.append(result)
    return results
