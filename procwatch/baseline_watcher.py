"""Integrate baseline spike detection into the main watch loop."""

from __future__ import annotations

from typing import Callable, List, Optional

from procwatch.baseline import is_cpu_spike, is_mem_spike, record_snapshot
from procwatch.baseline_reporter import format_spike_line
from procwatch.config import Config
from procwatch.monitor import ProcessSnapshot

AlertCallback = Callable[[str], None]


def process_snapshot(
    snap: ProcessSnapshot,
    config: Config,
    *,
    cpu_multiplier: float = 2.0,
    mem_multiplier: float = 2.0,
    min_samples: int = 5,
    on_spike: Optional[AlertCallback] = None,
    max_samples: int = 60,
) -> List[str]:
    """Record *snap* into the baseline and return any spike messages.

    Spikes are only reported once the profile has at least *min_samples*
    observations so that the baseline is meaningful.
    """
    profile = record_snapshot(snap, max_samples=max_samples)
    messages: List[str] = []

    if profile.sample_count < min_samples:
        return messages

    if is_cpu_spike(snap, multiplier=cpu_multiplier):
        msg = format_spike_line(snap.name, "cpu", snap.cpu_percent, profile.avg_cpu)
        messages.append(msg)
        if on_spike is not None:
            on_spike(msg)

    if is_mem_spike(snap, multiplier=mem_multiplier):
        msg = format_spike_line(snap.name, "mem", snap.memory_mb, profile.avg_mem)
        messages.append(msg)
        if on_spike is not None:
            on_spike(msg)

    return messages


def process_all(
    snapshots: List[ProcessSnapshot],
    config: Config,
    **kwargs,
) -> List[str]:
    """Run :func:`process_snapshot` for every snapshot and aggregate results."""
    all_messages: List[str] = []
    for snap in snapshots:
        all_messages.extend(process_snapshot(snap, config, **kwargs))
    return all_messages
