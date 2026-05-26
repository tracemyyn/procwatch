"""Tests for procwatch.circuit_breaker."""
from __future__ import annotations

import time

import pytest

from procwatch.circuit_breaker import (
    CircuitState,
    configure,
    get_entry,
    is_allowed,
    record_failure,
    record_success,
    reset_breaker,
)


@pytest.fixture(autouse=True)
def clean():
    reset_breaker()
    configure(failure_threshold=3, recovery_timeout=60.0)
    yield
    reset_breaker()


def test_new_key_is_allowed():
    assert is_allowed("webhook") is True


def test_entry_created_on_first_call():
    is_allowed("webhook")
    assert get_entry("webhook") is not None


def test_failures_below_threshold_keep_circuit_closed():
    record_failure("webhook")
    record_failure("webhook")
    assert is_allowed("webhook") is True
    assert get_entry("webhook").state == CircuitState.CLOSED


def test_threshold_failures_open_circuit():
    for _ in range(3):
        record_failure("webhook")
    assert get_entry("webhook").state == CircuitState.OPEN


def test_open_circuit_blocks_calls():
    for _ in range(3):
        record_failure("webhook")
    assert is_allowed("webhook") is False


def test_success_closes_circuit():
    for _ in range(3):
        record_failure("webhook")
    record_success("webhook")
    entry = get_entry("webhook")
    assert entry.state == CircuitState.CLOSED
    assert entry.failures == 0


def test_success_resets_failure_count():
    record_failure("webhook")
    record_failure("webhook")
    record_success("webhook")
    assert get_entry("webhook").failures == 0


def test_different_keys_are_independent():
    for _ in range(3):
        record_failure("webhook")
    assert is_allowed("desktop") is True


def test_open_circuit_allows_after_recovery_timeout(monkeypatch):
    configure(failure_threshold=3, recovery_timeout=5.0)
    for _ in range(3):
        record_failure("webhook")

    # Simulate time passing beyond recovery_timeout
    original = time.monotonic
    monkeypatch.setattr(
        "procwatch.circuit_breaker.time.monotonic",
        lambda: original() + 10.0,
    )
    assert is_allowed("webhook") is True


def test_half_open_state_set_after_recovery_timeout(monkeypatch):
    configure(failure_threshold=3, recovery_timeout=5.0)
    for _ in range(3):
        record_failure("webhook")

    original = time.monotonic
    monkeypatch.setattr(
        "procwatch.circuit_breaker.time.monotonic",
        lambda: original() + 10.0,
    )
    is_allowed("webhook")
    assert get_entry("webhook").state == CircuitState.HALF_OPEN


def test_record_failure_returns_state():
    state = record_failure("webhook")
    assert state == CircuitState.CLOSED  # below threshold
    record_failure("webhook")
    state = record_failure("webhook")
    assert state == CircuitState.OPEN
