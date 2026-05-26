"""Format labelled alert information for display."""

from __future__ import annotations

from typing import List, Dict

from procwatch.label import get_label

# Column widths
_PID_W = 7
_NAME_W = 20
_LEVEL_W = 10
_LABEL_W = 10


def _pad(text: str, width: int) -> str:
    return text[:width].ljust(width)


def format_label_line(pid: int, name: str, level: str) -> str:
    """Return a single formatted line showing PID, name, level and label."""
    label = get_label(level)
    parts = [
        _pad(str(pid), _PID_W),
        _pad(name, _NAME_W),
        _pad(level.upper(), _LEVEL_W),
        _pad(label, _LABEL_W),
    ]
    return "  ".join(parts).rstrip()


def format_label_table(entries: List[Dict]) -> str:
    """Render a table of labelled alert entries.

    Each entry is expected to have keys: pid, name, level.
    """
    header = "  ".join([
        _pad("PID", _PID_W),
        _pad("NAME", _NAME_W),
        _pad("LEVEL", _LEVEL_W),
        _pad("LABEL", _LABEL_W),
    ])
    separator = "-" * len(header)
    lines = [header, separator]
    for e in entries:
        lines.append(format_label_line(e["pid"], e["name"], e["level"]))
    if not entries:
        lines.append("  (no entries)")
    return "\n".join(lines)


def format_label_summary(entries: List[Dict]) -> str:
    """Return a one-line summary counting entries by label."""
    counts: Dict[str, int] = {}
    for e in entries:
        lbl = get_label(e.get("level", ""))
        counts[lbl] = counts.get(lbl, 0) + 1
    if not counts:
        return "No labelled alerts."
    parts = [f"{lbl}: {n}" for lbl, n in sorted(counts.items())]
    return "Label summary — " + ", ".join(parts)
