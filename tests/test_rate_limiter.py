"""Tests for procwatch.rate_limiter."""

import time
import pytest

from procwatch import rate_limiter
from procwatch.rate_limiter import (
    reset_rate_limiter,
    is_allowed,
    get_state,
    remaining,
)


@pytest.fixture(autouse=True)
def clean():
    reset_rate_limiter(window_seconds=60, max_alerts=5)
    yield
    rate_limiter._state = None


def test_first_alert_is_allowed():
    assert is_allowed() is True


def test_counter_increments_on_allowed():
    is_allowed()
    is_allowed()
    state = get_state()
    assert state.alert_count == 2


def test_alert_blocked_when_limit_reached():
    for _ in range(5):
        is_allowed()
    assert is_allowed() is False


def test_remaining_decreases_with_each_call():
    assert remaining() == 5
    is_allowed()
    assert remaining() == 4


def test_remaining_never_negative():
    for _ in range(10):
        is_allowed()
    assert remaining() == 0


def test_window_roll_resets_counter(monkeypatch):
    for _ in range(5):
        is_allowed()
    assert is_allowed() is False

    state = get_state()
    # Simulate the window expiring
    monkeypatch.setattr(time, "monotonic", lambda: state.window_start + 61)
    assert is_allowed() is True
    assert get_state().alert_count == 1


def test_reset_restores_defaults():
    for _ in range(5):
        is_allowed()
    reset_rate_limiter(window_seconds=30, max_alerts=10)
    state = get_state()
    assert state.alert_count == 0
    assert state.max_alerts == 10
    assert state.window_seconds == 30


def test_get_state_none_before_any_call():
    rate_limiter._state = None
    # get_state should return None when not yet initialised
    assert get_state() is None


def test_is_allowed_initialises_state_lazily():
    rate_limiter._state = None
    result = is_allowed()
    assert result is True
    assert get_state() is not None


def test_independent_windows_do_not_share_state():
    reset_rate_limiter(window_seconds=60, max_alerts=3)
    is_allowed()
    is_allowed()
    reset_rate_limiter(window_seconds=60, max_alerts=3)
    assert remaining() == 3
