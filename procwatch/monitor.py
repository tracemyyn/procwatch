import psutil
import time
from dataclasses import dataclass, field
from typing import Optional

from procwatch.config import Config


@dataclass
class ProcessSnapshot:
    pid: int
    name: str
    cpu_percent: float
    memory_percent: float
    timestamp: float = field(default_factory=time.time)

    def exceeds_thresholds(self, config: Config) -> bool:
        return (
            self.cpu_percent > config.cpu_threshold
            or self.memory_percent > config.memory_threshold
        )


def get_snapshot(pid: int) -> Optional[ProcessSnapshot]:
    """Return a ProcessSnapshot for the given PID, or None if not found."""
    try:
        proc = psutil.Process(pid)
        cpu = proc.cpu_percent(interval=0.1)
        mem = proc.memory_percent()
        return ProcessSnapshot(
            pid=pid,
            name=proc.name(),
            cpu_percent=cpu,
            memory_percent=mem,
        )
    except (psutil.NoSuchProcess, psutil.AccessDenied):
        return None


def scan_all_processes(config: Config) -> list[ProcessSnapshot]:
    """Scan all running processes and return snapshots that exceed thresholds."""
    spikes = []
    for proc in psutil.process_iter(["pid", "name"]):
        try:
            snapshot = get_snapshot(proc.pid)
            if snapshot and snapshot.exceeds_thresholds(config):
                spikes.append(snapshot)
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            continue
    return spikes


def watch(config: Config, callback, interval: Optional[float] = None) -> None:
    """Continuously monitor processes and invoke callback on spikes."""
    poll_interval = interval if interval is not None else config.poll_interval
    while True:
        spikes = scan_all_processes(config)
        for snapshot in spikes:
            callback(snapshot)
        time.sleep(poll_interval)
