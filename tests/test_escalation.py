"""Tests for procwatch.escalation."""

import pytest

from procwatch.escalation import (
    EscalationResult,
    clear_spike,
    get_severity,
    record_spike,
    reset_escalation,
)


@pytest.fixture(autouse=True)
def clean():
    reset_escalation()
    yield
    reset_escalation()


def test_first_spike_is_info():
    result = record_spike(pid=1, name="app")
    assert result.severity == "info"
    assert result.consecutive == 1


def test_second_spike_escalates_to_warning():
    record_spike(pid=1, name="app")
    result = record_spike(pid=1, name="app")
    assert result.severity == "warning"
    assert result.consecutive == 2


def test_fifth_spike_escalates_to_critical():
    for _ in range(4):
        record_spike(pid=1, name="app")
    result = record_spike(pid=1, name="app")
    assert result.severity == "critical"
    assert result.consecutive == 5


def test_beyond_five_stays_critical():
    for _ in range(10):
        result = record_spike(pid=1, name="app")
    assert result.severity == "critical"


def test_different_processes_are_independent():
    record_spike(pid=1, name="app")
    record_spike(pid=1, name="app")
    result_other = record_spike(pid=2, name="worker")
    assert result_other.severity == "info"
    assert result_other.consecutive == 1


def test_clear_spike_resets_counter():
    record_spike(pid=1, name="app")
    record_spike(pid=1, name="app")
    clear_spike(pid=1, name="app")
    result = record_spike(pid=1, name="app")
    assert result.severity == "info"
    assert result.consecutive == 1


def test_clear_spike_nonexistent_is_safe():
    clear_spike(pid=99, name="ghost")  # should not raise


def test_get_severity_none_before_any_spike():
    assert get_severity(pid=1, name="app") is None


def test_get_severity_reflects_current_level():
    record_spike(pid=1, name="app")
    record_spike(pid=1, name="app")
    assert get_severity(pid=1, name="app") == "warning"


def test_get_severity_after_clear_returns_none():
    record_spike(pid=1, name="app")
    clear_spike(pid=1, name="app")
    assert get_severity(pid=1, name="app") is None


def test_result_is_escalation_result_dataclass():
    result = record_spike(pid=42, name="svc")
    assert isinstance(result, EscalationResult)
    assert result.pid == 42
    assert result.name == "svc"
