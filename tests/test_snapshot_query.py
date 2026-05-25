"""Tests for procwatch.snapshot_query."""

from __future__ import annotations

import time

import pytest

from procwatch.monitor import ProcessSnapshot
from procwatch.snapshot_query import (
    SnapshotSummary,
    snapshots_in_window,
    summarise,
    top_by_cpu,
    top_by_mem,
)


def _snap(
    pid: int = 1,
    name: str = "proc",
    cpu: float = 10.0,
    mem: float = 50.0,
    age: float = 0.0,
) -> ProcessSnapshot:
    return ProcessSnapshot(
        pid=pid, name=name, cpu_percent=cpu, memory_mb=mem, timestamp=time.time() - age
    )


def test_snapshots_in_window_includes_recent():
    snaps = [_snap(age=5), _snap(age=10)]
    result = snapshots_in_window(seconds=20, snapshots=snaps)
    assert len(result) == 2


def test_snapshots_in_window_excludes_old():
    snaps = [_snap(age=5), _snap(age=100)]
    result = snapshots_in_window(seconds=30, snapshots=snaps)
    assert len(result) == 1


def test_snapshots_in_window_filters_by_pid():
    snaps = [_snap(pid=1, age=1), _snap(pid=2, age=1)]
    result = snapshots_in_window(seconds=60, pid=1, snapshots=snaps)
    assert len(result) == 1
    assert result[0].pid == 1


def test_summarise_returns_none_for_empty():
    assert summarise([]) is None


def test_summarise_single_snapshot():
    snap = _snap(pid=7, name="test", cpu=40.0, mem=200.0)
    summary = summarise([snap])
    assert isinstance(summary, SnapshotSummary)
    assert summary.pid == 7
    assert summary.name == "test"
    assert summary.count == 1
    assert summary.avg_cpu == pytest.approx(40.0)
    assert summary.max_cpu == pytest.approx(40.0)
    assert summary.avg_mem == pytest.approx(200.0)
    assert summary.max_mem == pytest.approx(200.0)


def test_summarise_multiple_snapshots():
    snaps = [_snap(cpu=10.0, mem=100.0), _snap(cpu=30.0, mem=200.0)]
    summary = summarise(snaps)
    assert summary.avg_cpu == pytest.approx(20.0)
    assert summary.max_cpu == pytest.approx(30.0)
    assert summary.avg_mem == pytest.approx(150.0)
    assert summary.max_mem == pytest.approx(200.0)


def test_top_by_cpu_returns_n_items():
    snaps = [_snap(cpu=float(i)) for i in range(10)]
    result = top_by_cpu(n=3, snapshots=snaps)
    assert len(result) == 3
    assert result[0].cpu_percent == pytest.approx(9.0)


def test_top_by_mem_returns_n_items():
    snaps = [_snap(mem=float(i * 10)) for i in range(8)]
    result = top_by_mem(n=2, snapshots=snaps)
    assert len(result) == 2
    assert result[0].memory_mb == pytest.approx(70.0)


def test_top_by_cpu_fewer_than_n():
    snaps = [_snap(cpu=5.0)]
    result = top_by_cpu(n=10, snapshots=snaps)
    assert len(result) == 1
