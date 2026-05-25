"""Tests for procwatch.correlator."""

from __future__ import annotations

import time
import pytest

from procwatch.notifier import Alert
from procwatch.correlator import (
    reset_correlator,
    record_alert,
    analyse,
    format_correlation_line,
)


def _alert(pid: int = 1, cpu: float = 80.0, mem: float = 0.0) -> Alert:
    return Alert(
        pid=pid,
        name="proc",
        cpu_percent=cpu,
        mem_percent=mem,
        timestamp=time.monotonic(),
    )


@pytest.fixture(autouse=True)
def clean():
    reset_correlator(window_seconds=30.0, min_alerts=3)
    yield
    reset_correlator()


def test_no_alerts_not_triggered():
    result = analyse()
    assert result.triggered is False
    assert result.alert_count == 0
    assert result.pressure_type == "none"


def test_below_min_alerts_not_triggered():
    record_alert(_alert(pid=1))
    record_alert(_alert(pid=2))
    result = analyse()
    assert result.triggered is False
    assert result.alert_count == 2


def test_min_alerts_triggers_correlation():
    for pid in (1, 2, 3):
        record_alert(_alert(pid=pid))
    result = analyse()
    assert result.triggered is True
    assert result.alert_count == 3
    assert result.unique_pids == 3


def test_pressure_type_cpu_only():
    for pid in (1, 2, 3):
        record_alert(_alert(pid=pid, cpu=90.0, mem=0.0))
    result = analyse()
    assert result.pressure_type == "cpu"


def test_pressure_type_mem_only():
    for pid in (1, 2, 3):
        record_alert(_alert(pid=pid, cpu=0.0, mem=75.0))
    result = analyse()
    assert result.pressure_type == "mem"


def test_pressure_type_mixed():
    record_alert(_alert(pid=1, cpu=80.0, mem=0.0))
    record_alert(_alert(pid=2, cpu=0.0, mem=70.0))
    record_alert(_alert(pid=3, cpu=60.0, mem=50.0))
    result = analyse()
    assert result.pressure_type == "mixed"


def test_stale_alerts_evicted():
    reset_correlator(window_seconds=0.05, min_alerts=2)
    record_alert(_alert(pid=1))
    record_alert(_alert(pid=2))
    time.sleep(0.1)
    # add one fresh alert — stale ones should be evicted
    record_alert(_alert(pid=3))
    result = analyse()
    assert result.alert_count == 1
    assert result.triggered is False


def test_unique_pids_counted_correctly():
    record_alert(_alert(pid=1))
    record_alert(_alert(pid=1))
    record_alert(_alert(pid=1))
    result = analyse()
    assert result.triggered is True
    assert result.unique_pids == 1


def test_format_line_not_triggered():
    result = analyse()
    line = format_correlation_line(result)
    assert "no system pressure" in line


def test_format_line_triggered():
    for pid in (1, 2, 3):
        record_alert(_alert(pid=pid))
    result = analyse()
    line = format_correlation_line(result)
    assert "SYSTEM PRESSURE" in line
    assert "cpu" in line
