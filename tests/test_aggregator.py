"""Tests for procwatch.aggregator."""

import pytest

from procwatch.monitor import ProcessSnapshot
from procwatch.aggregator import (
    push_snapshot,
    get_stats,
    all_stats,
    reset_aggregator,
)


@pytest.fixture(autouse=True)
def clean():
    reset_aggregator()
    yield
    reset_aggregator()


def _snap(pid: int, cpu: float, mem: float, name: str = "proc") -> ProcessSnapshot:
    return ProcessSnapshot(pid=pid, name=name, cpu_percent=cpu, memory_mb=mem)


def test_get_stats_returns_none_for_unknown_pid():
    assert get_stats(9999) is None


def test_push_single_snapshot_creates_stats():
    push_snapshot(_snap(1, cpu=10.0, mem=50.0))
    stats = get_stats(1)
    assert stats is not None
    assert stats.pid == 1
    assert stats.count == 1


def test_avg_cpu_computed_correctly():
    push_snapshot(_snap(2, cpu=10.0, mem=100.0))
    push_snapshot(_snap(2, cpu=30.0, mem=100.0))
    stats = get_stats(2)
    assert stats.avg_cpu == pytest.approx(20.0)


def test_max_cpu_is_highest_value():
    for cpu in [5.0, 80.0, 40.0]:
        push_snapshot(_snap(3, cpu=cpu, mem=10.0))
    stats = get_stats(3)
    assert stats.max_cpu == pytest.approx(80.0)


def test_avg_mem_computed_correctly():
    push_snapshot(_snap(4, cpu=1.0, mem=200.0))
    push_snapshot(_snap(4, cpu=1.0, mem=400.0))
    stats = get_stats(4)
    assert stats.avg_mem == pytest.approx(300.0)


def test_peak_snapshot_has_highest_cpu():
    push_snapshot(_snap(5, cpu=5.0, mem=10.0))
    push_snapshot(_snap(5, cpu=95.0, mem=10.0))
    push_snapshot(_snap(5, cpu=20.0, mem=10.0))
    stats = get_stats(5)
    assert stats.peak_snapshot.cpu_percent == pytest.approx(95.0)


def test_window_limits_stored_snapshots():
    for i in range(15):
        push_snapshot(_snap(6, cpu=float(i), mem=10.0), window=10)
    stats = get_stats(6)
    assert stats.count == 10
    # oldest snapshots (cpu 0-4) should be evicted; max should be 14
    assert stats.max_cpu == pytest.approx(14.0)


def test_all_stats_returns_all_pids():
    push_snapshot(_snap(10, cpu=1.0, mem=1.0))
    push_snapshot(_snap(20, cpu=2.0, mem=2.0))
    result = all_stats()
    assert set(result.keys()) == {10, 20}


def test_different_pids_are_independent():
    push_snapshot(_snap(7, cpu=50.0, mem=10.0))
    push_snapshot(_snap(8, cpu=90.0, mem=10.0))
    assert get_stats(7).avg_cpu == pytest.approx(50.0)
    assert get_stats(8).avg_cpu == pytest.approx(90.0)


def test_name_reflects_latest_snapshot():
    push_snapshot(_snap(9, cpu=1.0, mem=1.0, name="old_name"))
    push_snapshot(_snap(9, cpu=1.0, mem=1.0, name="new_name"))
    assert get_stats(9).name == "new_name"
