"""Formatting helpers for suppression rule status."""

from __future__ import annotations

from typing import List

from procwatch.suppressor import SuppressionRule


def _fmt_rule(index: int, rule: SuppressionRule) -> str:
    parts: List[str] = [f"  [{index}]"]
    if rule.name_glob:
        parts.append(f"name={rule.name_glob}")
    if rule.pid is not None:
        parts.append(f"pid={rule.pid}")
    if rule.max_cpu is not None:
        parts.append(f"max_cpu<{rule.max_cpu:.1f}%")
    if rule.max_mem is not None:
        parts.append(f"max_mem<{rule.max_mem:.1f}MB")
    return " ".join(parts)


def format_suppression_table(rules: List[SuppressionRule]) -> str:
    """Return a human-readable table of active suppression rules."""
    if not rules:
        return "No suppression rules active."
    lines = ["Active suppression rules:", "-" * 40]
    for i, rule in enumerate(rules):
        lines.append(_fmt_rule(i, rule))
    return "\n".join(lines)


def format_suppressed_line(name: str, pid: int, reason: str) -> str:
    """Single-line message used when an alert is suppressed."""
    return f"[SUPPRESSED] pid={pid} name={name} reason={reason}"
