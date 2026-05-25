"""Tests for procwatch.dedup."""

import time
import pytest

from procwatch.notifier import Alert
from procwatch.dedup import (
    reset_dedup,
    is_duplicate,
    record,
    maybe_dispatch,
    get_state,
)


@pytest.fixture(autouse=True)
def clean():
    reset_dedup(window_seconds=60.0)
    yield
    reset_dedup()


def _alert(pid: int = 1, cpu: float = 90.0, mem: float = None) -> Alert:
    return Alert(
        pid=pid,
        name="proc",
        cpu_percent=cpu,
        mem_mb=mem,
        timestamp=time.time(),
    )


def test_first_alert_is_not_duplicate():
    assert is_duplicate(_alert()) is False


def test_after_record_alert_is_duplicate():
    a = _alert()
    record(a)
    assert is_duplicate(a) is True


def test_duplicate_expires_after_window():
    a = _alert()
    past = time.time() - 120.0
    record(a, now=past)
    assert is_duplicate(a, now=time.time()) is False


def test_duplicate_within_window_returns_true():
    a = _alert()
    now = time.time()
    record(a, now=now - 30.0)
    assert is_duplicate(a, now=now) is True


def test_different_pids_are_independent():
    a1 = _alert(pid=1)
    a2 = _alert(pid=2)
    record(a1)
    assert is_duplicate(a2) is False


def test_cpu_and_mem_metrics_are_independent():
    cpu_alert = _alert(pid=1, cpu=90.0, mem=None)
    mem_alert = Alert(pid=1, name="proc", cpu_percent=None, mem_mb=500.0, timestamp=time.time())
    record(cpu_alert)
    assert is_duplicate(mem_alert) is False


def test_maybe_dispatch_returns_true_first_time():
    assert maybe_dispatch(_alert()) is True


def test_maybe_dispatch_returns_false_on_duplicate():
    a = _alert()
    maybe_dispatch(a)
    assert maybe_dispatch(a) is False


def test_maybe_dispatch_records_entry():
    a = _alert(pid=42)
    maybe_dispatch(a)
    state = get_state()
    assert (42, "cpu") in state.entries


def test_get_state_reflects_window():
    reset_dedup(window_seconds=120.0)
    state = get_state()
    assert state.window_seconds == 120.0


def test_reset_clears_entries():
    record(_alert())
    reset_dedup()
    state = get_state()
    assert state.entries == {}
