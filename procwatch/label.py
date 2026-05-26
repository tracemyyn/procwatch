"""Label module: attach human-readable severity labels to alerts based on
escalation level and configurable thresholds."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, Optional

# Default mapping from escalation level string to label text
_DEFAULT_LABELS: Dict[str, str] = {
    "info": "INFO",
    "warning": "WARNING",
    "critical": "CRITICAL",
}


@dataclass
class LabelConfig:
    labels: Dict[str, str] = field(default_factory=lambda: dict(_DEFAULT_LABELS))
    unknown_label: str = "UNKNOWN"


_config: LabelConfig = LabelConfig()


def reset_label_config() -> None:
    """Reset label config to defaults (useful in tests)."""
    global _config
    _config = LabelConfig()


def configure_labels(labels: Dict[str, str], unknown_label: str = "UNKNOWN") -> None:
    """Override the label mappings at runtime."""
    global _config
    _config = LabelConfig(labels={**_DEFAULT_LABELS, **labels}, unknown_label=unknown_label)


def get_label(level: str) -> str:
    """Return the display label for a given escalation level string.

    Falls back to *unknown_label* if the level is not recognised.
    """
    return _config.labels.get(level.lower(), _config.unknown_label)


def label_for_cpu(cpu: float, warn_threshold: float = 70.0, crit_threshold: float = 90.0) -> str:
    """Derive a severity label purely from a CPU percentage value."""
    if cpu >= crit_threshold:
        return get_label("critical")
    if cpu >= warn_threshold:
        return get_label("warning")
    return get_label("info")


def label_for_mem(mem_mb: float, warn_threshold: float = 500.0, crit_threshold: float = 1500.0) -> str:
    """Derive a severity label purely from a memory value (MB)."""
    if mem_mb >= crit_threshold:
        return get_label("critical")
    if mem_mb >= warn_threshold:
        return get_label("warning")
    return get_label("info")


def annotate(data: Dict, level: Optional[str] = None) -> Dict:
    """Return a copy of *data* with a 'label' key added.

    If *level* is provided it is used directly; otherwise the key
    'level' inside *data* is consulted.
    """
    resolved = level or data.get("level", "")
    return {**data, "label": get_label(resolved)}
