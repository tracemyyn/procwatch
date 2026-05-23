"""Tests for procwatch.scheduler."""

from __future__ import annotations

import threading
import time

import pytest

from procwatch import scheduler
from procwatch.scheduler import get_state, is_running, reset_scheduler, run, stop


@pytest.fixture(autouse=True)
def clean():
    reset_scheduler()
    yield
    stop()
    reset_scheduler()


# ---------------------------------------------------------------------------
# Basic tick counting
# ---------------------------------------------------------------------------

def test_run_executes_callback_max_ticks():
    calls = []
    run(lambda: calls.append(1), interval=0.01, max_ticks=3)
    assert len(calls) == 3


def test_tick_count_matches_max_ticks():
    run(lambda: None, interval=0.01, max_ticks=5)
    assert get_state().tick_count == 5


def test_last_tick_at_is_set_after_run():
    run(lambda: None, interval=0.01, max_ticks=1)
    assert get_state().last_tick_at is not None


# ---------------------------------------------------------------------------
# Graceful stop
# ---------------------------------------------------------------------------

def test_stop_halts_loop_early():
    calls = []

    def _cb():
        calls.append(1)
        if len(calls) >= 2:
            stop()

    run(_cb, interval=0.01)
    assert len(calls) == 2
    assert not is_running()


def test_stop_from_another_thread():
    calls = []

    def _cb():
        calls.append(1)

    t = threading.Thread(target=run, kwargs={"callback": _cb, "interval": 0.05})
    t.start()
    time.sleep(0.12)
    stop()
    t.join(timeout=1.0)
    assert not t.is_alive()
    assert len(calls) >= 2


# ---------------------------------------------------------------------------
# Error handling
# ---------------------------------------------------------------------------

def test_errors_stored_when_no_handler():
    def _bad():
        raise RuntimeError("boom")

    run(_bad, interval=0.01, max_ticks=3)
    state = get_state()
    assert len(state.errors) == 3
    assert all("boom" in e for e in state.errors)


def test_on_error_callback_called():
    caught: list[Exception] = []

    def _bad():
        raise ValueError("oops")

    run(_bad, interval=0.01, max_ticks=2, on_error=caught.append)
    assert len(caught) == 2
    assert isinstance(caught[0], ValueError)
    # Errors list should remain empty when custom handler is provided
    assert get_state().errors == []


# ---------------------------------------------------------------------------
# Validation
# ---------------------------------------------------------------------------

def test_invalid_interval_raises():
    with pytest.raises(ValueError, match="interval must be positive"):
        run(lambda: None, interval=0)


def test_negative_interval_raises():
    with pytest.raises(ValueError):
        run(lambda: None, interval=-1)


# ---------------------------------------------------------------------------
# State after run
# ---------------------------------------------------------------------------

def test_is_running_false_after_completion():
    run(lambda: None, interval=0.01, max_ticks=1)
    assert not is_running()


def test_reset_clears_tick_count():
    run(lambda: None, interval=0.01, max_ticks=4)
    reset_scheduler()
    assert get_state().tick_count == 0
    assert get_state().errors == []
