"""Build Alert objects from ProcessSnapshot + Config thresholds."""

from procwatch.config import Config
from procwatch.monitor import ProcessSnapshot
from procwatch.notifier import Alert


def build_alert(snapshot: ProcessSnapshot, config: Config) -> Alert:
    """Create an Alert describing which thresholds a snapshot exceeded."""
    parts = []
    if snapshot.cpu_percent >= config.cpu_threshold:
        parts.append(f"cpu={snapshot.cpu_percent:.1f}% (limit {config.cpu_threshold}%)")
    if snapshot.memory_mb >= config.memory_threshold:
        parts.append(
            f"mem={snapshot.memory_mb:.1f} MB (limit {config.memory_threshold} MB)"
        )

    detail = ", ".join(parts) if parts else "resource spike"
    message = f"{snapshot.name} (pid {snapshot.pid}) {detail}"

    return Alert(
        pid=snapshot.pid,
        name=snapshot.name,
        cpu_percent=snapshot.cpu_percent,
        memory_mb=snapshot.memory_mb,
        message=message,
    )


def maybe_alert(snapshot: ProcessSnapshot, config: Config) -> Alert | None:
    """Return an Alert if the snapshot exceeds any threshold, else None."""
    exceeds_cpu = snapshot.cpu_percent >= config.cpu_threshold
    exceeds_mem = snapshot.memory_mb >= config.memory_threshold
    if exceeds_cpu or exceeds_mem:
        return build_alert(snapshot, config)
    return None
