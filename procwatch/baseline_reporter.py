"""Format baseline profiles for human-readable output."""

from __future__ import annotations

from typing import List

from procwatch.baseline import BaselineProfile, all_profiles

_HEADER = f"{'NAME':<20} {'SAMPLES':>7} {'AVG CPU %':>10} {'AVG MEM MB':>11}"
_SEP = "-" * len(_HEADER)


def _fmt_profile(profile: BaselineProfile) -> str:
    return (
        f"{profile.name:<20} "
        f"{profile.sample_count:>7} "
        f"{profile.avg_cpu:>10.1f} "
        f"{profile.avg_mem:>11.1f}"
    )


def format_baseline_table(profiles: List[BaselineProfile] | None = None) -> str:
    """Return a formatted table of baseline profiles.

    If *profiles* is None, all currently stored profiles are used.
    """
    if profiles is None:
        profiles = list(all_profiles().values())

    if not profiles:
        return "No baseline data collected yet."

    sorted_profiles = sorted(profiles, key=lambda p: p.name.lower())
    rows = [_HEADER, _SEP] + [_fmt_profile(p) for p in sorted_profiles]
    return "\n".join(rows)


def format_spike_line(name: str, kind: str, current: float, baseline: float) -> str:
    """Return a single-line spike notification string."""
    ratio = current / baseline if baseline > 0 else float("inf")
    unit = "%" if kind == "cpu" else "MB"
    return (
        f"[BASELINE SPIKE] {name}: {kind.upper()} {current:.1f}{unit} "
        f"is {ratio:.1f}x above baseline avg {baseline:.1f}{unit}"
    )
