"""Format anomaly detection results for human-readable output."""

from __future__ import annotations

from procwatch.anomaly import AnomalyResult

_HEADER = "{:<8} {:<20} {:>10} {:>10} {:>12} {:>12}".format(
    "PID", "NAME", "CPU z", "MEM z", "CPU spike", "MEM spike"
)
_SEP = "-" * 76


def _fmt_z(z) -> str:
    if z is None:
        return "   n/a"
    return f"{z:+.2f}"


def _fmt_flag(flag: bool) -> str:
    return "YES" if flag else "no"


def format_anomaly_line(result: AnomalyResult) -> str:
    """Single-line summary for one anomaly result."""
    return "{:<8} {:<20} {:>10} {:>10} {:>12} {:>12}".format(
        result.pid,
        result.name[:20],
        _fmt_z(result.cpu_z),
        _fmt_z(result.mem_z),
        _fmt_flag(result.cpu_anomaly),
        _fmt_flag(result.mem_anomaly),
    )


def format_anomaly_table(results: list[AnomalyResult]) -> str:
    """Return a formatted table of anomaly results."""
    if not results:
        return "No anomalies detected."

    lines = [_HEADER, _SEP]
    for r in results:
        lines.append(format_anomaly_line(r))
    return "\n".join(lines)


def format_anomaly_summary(results: list[AnomalyResult]) -> str:
    """One-line aggregate summary."""
    cpu_count = sum(1 for r in results if r.cpu_anomaly)
    mem_count = sum(1 for r in results if r.mem_anomaly)
    total = len(results)
    return (
        f"Anomaly scan: {total} process(es) flagged "
        f"(CPU spikes: {cpu_count}, MEM spikes: {mem_count})"
    )
