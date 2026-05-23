"""Tests for procwatch.trend."""

import pytest

from procwatch.monitor import ProcessSnapshot
from procwatch.trend import analyse_cpu_trend, analyse_mem_trend, _linear_slope


def _snap(cpu: float, mem: float, pid: int = 1, name: str = "p") -> ProcessSnapshot:
    return ProcessSnapshot(pid=pid, name=name, cpu_percent=cpu, memory_mb=mem)


# --- _linear_slope helpers ---

def test_slope_empty_returns_zero():
    assert _linear_slope([]) == 0.0


def test_slope_single_returns_zero():
    assert _linear_slope([42.0]) == 0.0


def test_slope_flat_series():
    assert _linear_slope([10.0, 10.0, 10.0]) == pytest.approx(0.0)


def test_slope_rising_series():
    assert _linear_slope([0.0, 5.0, 10.0]) == pytest.approx(5.0)


def test_slope_falling_series():
    assert _linear_slope([10.0, 5.0, 0.0]) == pytest.approx(-5.0)


# --- analyse_cpu_trend ---

def test_cpu_trend_none_for_single_snapshot():
    assert analyse_cpu_trend([_snap(50.0, 100.0)]) is None


def test_cpu_trend_rising():
    snaps = [_snap(cpu=float(i * 5), mem=100.0) for i in range(5)]
    result = analyse_cpu_trend(snaps, rising_threshold=2.0)
    assert result.direction == "rising"
    assert result.slope > 0


def test_cpu_trend_falling():
    snaps = [_snap(cpu=float(50 - i * 5), mem=100.0) for i in range(5)]
    result = analyse_cpu_trend(snaps, falling_threshold=-2.0)
    assert result.direction == "falling"
    assert result.slope < 0


def test_cpu_trend_stable():
    snaps = [_snap(cpu=10.0, mem=100.0) for _ in range(4)]
    result = analyse_cpu_trend(snaps, rising_threshold=2.0, falling_threshold=-2.0)
    assert result.direction == "stable"
    assert result.slope == pytest.approx(0.0)


def test_cpu_trend_pid_and_name_from_last_snapshot():
    snaps = [
        ProcessSnapshot(pid=42, name="worker", cpu_percent=10.0, memory_mb=50.0),
        ProcessSnapshot(pid=42, name="worker", cpu_percent=20.0, memory_mb=50.0),
    ]
    result = analyse_cpu_trend(snaps)
    assert result.pid == 42
    assert result.name == "worker"
    assert result.samples == 2


# --- analyse_mem_trend ---

def test_mem_trend_none_for_single_snapshot():
    assert analyse_mem_trend([_snap(10.0, 200.0)]) is None


def test_mem_trend_rising():
    snaps = [_snap(cpu=5.0, mem=float(100 + i * 20)) for i in range(5)]
    result = analyse_mem_trend(snaps, rising_threshold=5.0)
    assert result.direction == "rising"


def test_mem_trend_stable():
    snaps = [_snap(cpu=5.0, mem=256.0) for _ in range(4)]
    result = analyse_mem_trend(snaps)
    assert result.direction == "stable"
