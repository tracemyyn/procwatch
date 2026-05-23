"""Scheduler: run the watch loop at a fixed interval with graceful shutdown."""

from __future__ import annotations

import threading
import time
from dataclasses import dataclass, field
from typing import Callable, Optional


@dataclass
class SchedulerState:
    running: bool = False
    tick_count: int = 0
    last_tick_at: Optional[float] = None
    errors: list[str] = field(default_factory=list)


_state = SchedulerState()
_stop_event = threading.Event()


def reset_scheduler() -> None:
    """Reset scheduler state (useful for tests)."""
    global _state
    _state = SchedulerState()
    _stop_event.clear()


def stop() -> None:
    """Signal the scheduler to stop after the current tick."""
    _stop_event.set()
    _state.running = False


def is_running() -> bool:
    return _state.running


def get_state() -> SchedulerState:
    return _state


def run(
    callback: Callable[[], None],
    interval: float,
    max_ticks: Optional[int] = None,
    on_error: Optional[Callable[[Exception], None]] = None,
) -> None:
    """Block and call *callback* every *interval* seconds.

    Args:
        callback:  Function invoked on each tick.
        interval:  Seconds between ticks (must be > 0).
        max_ticks: Stop automatically after this many ticks (None = run forever).
        on_error:  Optional handler for exceptions raised by *callback*.
                   If omitted, the exception message is stored and the loop continues.
    """
    if interval <= 0:
        raise ValueError(f"interval must be positive, got {interval}")

    _stop_event.clear()
    _state.running = True
    _state.tick_count = 0

    try:
        while not _stop_event.is_set():
            tick_start = time.monotonic()
            _state.last_tick_at = tick_start

            try:
                callback()
            except Exception as exc:  # noqa: BLE001
                if on_error is not None:
                    on_error(exc)
                else:
                    _state.errors.append(str(exc))

            _state.tick_count += 1

            if max_ticks is not None and _state.tick_count >= max_ticks:
                break

            elapsed = time.monotonic() - tick_start
            sleep_for = max(0.0, interval - elapsed)
            _stop_event.wait(timeout=sleep_for)
    finally:
        _state.running = False
