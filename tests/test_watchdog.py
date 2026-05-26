"""Tests for procwatch.watchdog."""
import time
import pytest

from procwatch.watchdog import (
    init_watchdog,
    reset_watchdog,
    check_stale,
    get_watchdog,
    stale_summary,
)
from procwatch.scheduler import reset_scheduler


@pytest.fixture(autouse=True)
def clean():
    reset_watchdog()
    reset_scheduler()
    yield
    reset_watchdog()
    reset_scheduler()


def test_get_watchdog_none_before_init():
    assert get_watchdog() is None


def test_init_watchdog_returns_state():
    wd = init_watchdog(interval_seconds=5.0)
    assert wd is not None
    assert wd.interval_seconds == 5.0


def test_stale_threshold_derived_from_factor():
    wd = init_watchdog(interval_seconds=10.0, stale_factor=2.0)
    assert wd.stale_seconds == 20.0


def test_default_stale_factor_is_three():
    wd = init_watchdog(interval_seconds=4.0)
    assert wd.stale_seconds == 12.0


def test_check_stale_false_when_not_initialised():
    # No init — should never raise, just return False
    assert check_stale() is False


def test_check_stale_false_immediately_after_init():
    init_watchdog(interval_seconds=5.0)
    assert check_stale() is False


def test_check_stale_true_when_now_far_in_future():
    wd = init_watchdog(interval_seconds=5.0, stale_factor=2.0)
    far_future = time.time() + 1000.0
    assert check_stale(now=far_future) is True


def test_stale_count_increments_on_each_stale_check():
    init_watchdog(interval_seconds=1.0, stale_factor=1.0)
    far_future = time.time() + 500.0
    check_stale(now=far_future)
    check_stale(now=far_future)
    wd = get_watchdog()
    assert wd.stale_count == 2


def test_stale_count_not_incremented_when_ok():
    init_watchdog(interval_seconds=60.0)
    check_stale()  # should be OK
    wd = get_watchdog()
    assert wd.stale_count == 0


def test_last_ok_at_updated_when_not_stale():
    wd = init_watchdog(interval_seconds=60.0)
    original = wd.last_ok_at
    time.sleep(0.05)
    check_stale()
    assert wd.last_ok_at >= original


def test_last_ok_at_not_updated_when_stale():
    """last_ok_at should remain unchanged when the watchdog is stale."""
    wd = init_watchdog(interval_seconds=1.0, stale_factor=1.0)
    original = wd.last_ok_at
    far_future = time.time() + 500.0
    check_stale(now=far_future)
    assert wd.last_ok_at == original


def test_stale_summary_not_initialised():
    summary = stale_summary()
    assert "not initialised" in summary


def test_stale_summary_ok_status():
    init_watchdog(interval_seconds=60.0)
    summary = stale_summary()
    assert "OK" in summary


def test_stale_summary_stale_status():
    init_watchdog(interval_seconds=1.0, stale_factor=1.0)
    # Force stale by overriding last_ok_at
    wd = get_watchdog()
    wd.last_ok_at = time.time() - 1000.0
    summary = stale_summary()
    assert "STALE" in summary


def test_reinit_resets_stale_count():
    init_watchdog(interval_seconds=1.0, stale_factor=1.0)
    far_future = time.time() + 500.0
    check_stale(now=far_future)
    init_watchdog(interval_seconds=1.0)
    wd = get_watchdog()
    assert wd.stale_count == 0
