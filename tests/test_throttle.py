"""Tests for procwatch.throttle."""

import time
import pytest

from procwatch.throttle import (
    ThrottleConfig,
    is_allowed,
    reset_buckets,
    get_bucket,
)


@pytest.fixture(autouse=True)
def clean_buckets():
    """Ensure a fresh bucket state for every test."""
    reset_buckets()
    yield
    reset_buckets()


def test_first_alert_is_allowed():
    assert is_allowed("myapp", 1234) is True


def test_bucket_created_after_first_call():
    is_allowed("myapp", 1234)
    entry = get_bucket("myapp", 1234)
    assert entry is not None
    tokens, _ = entry
    # One token consumed from default max_tokens=5
    assert abs(tokens - 4.0) < 0.1


def test_burst_capacity_exhausts_and_blocks():
    cfg = ThrottleConfig(max_tokens=3.0, refill_rate=0.0, cost=1.0)
    for _ in range(3):
        assert is_allowed("proc", 99, cfg) is True
    # Bucket empty; refill_rate=0 so no new tokens
    assert is_allowed("proc", 99, cfg) is False


def test_different_pids_have_independent_buckets():
    cfg = ThrottleConfig(max_tokens=1.0, refill_rate=0.0, cost=1.0)
    assert is_allowed("proc", 1, cfg) is True
    assert is_allowed("proc", 2, cfg) is True  # separate bucket
    assert is_allowed("proc", 1, cfg) is False  # first bucket exhausted


def test_different_names_have_independent_buckets():
    cfg = ThrottleConfig(max_tokens=1.0, refill_rate=0.0, cost=1.0)
    assert is_allowed("alpha", 1, cfg) is True
    assert is_allowed("beta", 1, cfg) is True
    assert is_allowed("alpha", 1, cfg) is False


def test_refill_allows_after_wait():
    cfg = ThrottleConfig(max_tokens=1.0, refill_rate=10.0, cost=1.0)
    assert is_allowed("proc", 5, cfg) is True
    assert is_allowed("proc", 5, cfg) is False  # empty
    time.sleep(0.15)  # 0.15 s * 10 tokens/s = 1.5 tokens refilled
    assert is_allowed("proc", 5, cfg) is True


def test_tokens_capped_at_max():
    cfg = ThrottleConfig(max_tokens=2.0, refill_rate=100.0, cost=1.0)
    is_allowed("proc", 7, cfg)  # create bucket
    time.sleep(0.1)  # would add 10 tokens, but cap is 2
    is_allowed("proc", 7, cfg)  # consume one
    tokens, _ = get_bucket("proc", 7)
    assert tokens <= cfg.max_tokens


def test_reset_buckets_clears_state():
    is_allowed("proc", 1)
    reset_buckets()
    assert get_bucket("proc", 1) is None
