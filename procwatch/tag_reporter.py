"""Formatting helpers for process tag reports."""

from __future__ import annotations

from typing import Dict, List

from procwatch.tag import tag_snapshot
from procwatch.monitor import ProcessSnapshot


def _fmt_tags(tags: List[str]) -> str:
    return ", ".join(tags) if tags else "(none)"


def format_tag_line(snap: ProcessSnapshot) -> str:
    """Return a single-line summary of a snapshot with its tags."""
    info = tag_snapshot(snap)
    tags_str = _fmt_tags(info["tags"])  # type: ignore[arg-type]
    return f"[{info['pid']}] {info['name']:<20}  tags: {tags_str}"


def format_tag_table(snaps: List[ProcessSnapshot]) -> str:
    """Return a formatted table of snapshots and their tags."""
    if not snaps:
        return "No processes to display."

    header = f"{'PID':>7}  {'NAME':<20}  {'CPU%':>6}  {'MEM%':>6}  TAGS"
    sep = "-" * len(header)
    rows = [header, sep]
    for snap in snaps:
        info = tag_snapshot(snap)
        tags_str = _fmt_tags(info["tags"])  # type: ignore[arg-type]
        rows.append(
            f"{info['pid']:>7}  {info['name']:<20}  {info['cpu']:>6.1f}  {info['mem']:>6.1f}  {tags_str}"
        )
    return "\n".join(rows)


def format_tag_summary(snaps: List[ProcessSnapshot]) -> str:
    """Return a summary grouped by tag."""
    grouped: Dict[str, List[str]] = {}
    for snap in snaps:
        info = tag_snapshot(snap)
        tags: List[str] = info["tags"]  # type: ignore[assignment]
        for tag in tags:
            grouped.setdefault(tag, []).append(snap.name)

    if not grouped:
        return "No tags assigned."

    lines = ["Tag summary:"]
    for tag, names in sorted(grouped.items()):
        lines.append(f"  {tag}: {', '.join(sorted(set(names)))}")
    return "\n".join(lines)
