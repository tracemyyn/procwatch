"""Time-window based alert silencing (maintenance windows)."""

from __future__ import annotations

import fnmatch
from dataclasses import dataclass, field
from datetime import datetime, time
from typing import List, Optional


@dataclass
class SilenceWindow:
    """A named time window during which matching processes are silenced."""

    name: str
    start: time          # e.g. time(2, 0)  -> 02:00
    end: time            # e.g. time(4, 0)  -> 04:00
    name_glob: str = "*"  # process name pattern
    days: List[int] = field(default_factory=lambda: list(range(7)))  # 0=Mon … 6=Sun


@dataclass
class SilencerState:
    windows: List[SilenceWindow] = field(default_factory=list)


_state: Optional[SilencerState] = None


def reset_silencer() -> None:
    """Clear all registered silence windows (useful in tests)."""
    global _state
    _state = SilencerState()


def _ensure_state() -> SilencerState:
    global _state
    if _state is None:
        _state = SilencerState()
    return _state


def add_window(window: SilenceWindow) -> None:
    """Register a silence window."""
    _ensure_state().windows.append(window)


def is_silenced(process_name: str, at: Optional[datetime] = None) -> bool:
    """Return True if *process_name* falls inside any active silence window."""
    state = _ensure_state()
    now = at or datetime.now()
    current_time = now.time()
    current_day = now.weekday()  # 0 = Monday

    for window in state.windows:
        if current_day not in window.days:
            continue
        if not fnmatch.fnmatch(process_name, window.name_glob):
            continue
        # Handle windows that wrap midnight (start > end)
        if window.start <= window.end:
            if window.start <= current_time <= window.end:
                return True
        else:
            if current_time >= window.start or current_time <= window.end:
                return True
    return False


def get_windows() -> List[SilenceWindow]:
    """Return a copy of all registered windows."""
    return list(_ensure_state().windows)


def windows_from_config(cfg_list: List[dict]) -> List[SilenceWindow]:
    """Build SilenceWindow objects from a list of config dicts."""
    windows: List[SilenceWindow] = []
    for entry in cfg_list:
        start_h, start_m = map(int, entry["start"].split(":"))
        end_h, end_m = map(int, entry["end"].split(":"))
        windows.append(
            SilenceWindow(
                name=entry.get("name", "unnamed"),
                start=time(start_h, start_m),
                end=time(end_h, end_m),
                name_glob=entry.get("name_glob", "*"),
                days=entry.get("days", list(range(7))),
            )
        )
    return windows
