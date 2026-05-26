"""Tests for procwatch.retry."""

import pytest
from unittest.mock import MagicMock

from procwatch.retry import (
    RetryConfig,
    RetryResult,
    _compute_delay,
    with_retry,
    retry_config_from_dict,
)


# ---------------------------------------------------------------------------
# _compute_delay
# ---------------------------------------------------------------------------

def test_compute_delay_first_attempt():
    cfg = RetryConfig(base_delay=1.0, backoff_factor=2.0, max_delay=30.0)
    assert _compute_delay(0, cfg) == pytest.approx(1.0)


def test_compute_delay_second_attempt():
    cfg = RetryConfig(base_delay=1.0, backoff_factor=2.0, max_delay=30.0)
    assert _compute_delay(1, cfg) == pytest.approx(2.0)


def test_compute_delay_capped_at_max():
    cfg = RetryConfig(base_delay=1.0, backoff_factor=10.0, max_delay=5.0)
    assert _compute_delay(3, cfg) == pytest.approx(5.0)


# ---------------------------------------------------------------------------
# with_retry — success paths
# ---------------------------------------------------------------------------

def test_success_on_first_attempt():
    fn = MagicMock(return_value=42)
    result = with_retry(fn, _sleep=MagicMock())
    assert result.success is True
    assert result.attempts == 1
    assert result.value == 42
    fn.assert_called_once()


def test_success_on_second_attempt():
    sleep = MagicMock()
    fn = MagicMock(side_effect=[RuntimeError("boom"), "ok"])
    cfg = RetryConfig(max_attempts=3, base_delay=0.1)
    result = with_retry(fn, cfg, _sleep=sleep)
    assert result.success is True
    assert result.attempts == 2
    assert result.value == "ok"
    sleep.assert_called_once()


# ---------------------------------------------------------------------------
# with_retry — failure paths
# ---------------------------------------------------------------------------

def test_all_attempts_fail_returns_false():
    sleep = MagicMock()
    fn = MagicMock(side_effect=RuntimeError("always fails"))
    cfg = RetryConfig(max_attempts=3, base_delay=0.0)
    result = with_retry(fn, cfg, _sleep=sleep)
    assert result.success is False
    assert result.attempts == 3
    assert "always fails" in result.last_error


def test_sleep_called_between_attempts():
    sleep = MagicMock()
    fn = MagicMock(side_effect=ValueError("x"))
    cfg = RetryConfig(max_attempts=4, base_delay=1.0, backoff_factor=2.0)
    with_retry(fn, cfg, _sleep=sleep)
    # sleep should be called max_attempts-1 times
    assert sleep.call_count == 3


def test_no_sleep_after_last_attempt():
    sleep = MagicMock()
    fn = MagicMock(side_effect=ValueError("x"))
    cfg = RetryConfig(max_attempts=1)
    with_retry(fn, cfg, _sleep=sleep)
    sleep.assert_not_called()


# ---------------------------------------------------------------------------
# retry_config_from_dict
# ---------------------------------------------------------------------------

def test_retry_config_from_dict_defaults():
    cfg = retry_config_from_dict({})
    assert cfg.max_attempts == 3
    assert cfg.base_delay == pytest.approx(1.0)
    assert cfg.backoff_factor == pytest.approx(2.0)
    assert cfg.max_delay == pytest.approx(30.0)


def test_retry_config_from_dict_custom():
    cfg = retry_config_from_dict({"max_attempts": 5, "base_delay": 0.5, "max_delay": 10.0})
    assert cfg.max_attempts == 5
    assert cfg.base_delay == pytest.approx(0.5)
    assert cfg.max_delay == pytest.approx(10.0)
