"""Tests for procwatch.baseline_watcher module."""

import pytest

from procwatch.baseline import reset_baselines
from procwatch.baseline_watcher import process_all, process_snapshot
from procwatch.config import Config
from procwatch.monitor import ProcessSnapshot


def _snap(name: str, cpu: float, mem: float, pid: int = 1) -> ProcessSnapshot:
    return ProcessSnapshot(pid=pid, name=name, cpu_percent=cpu, memory_mb=mem)


@pytest.fixture(autouse=True)
def clean():
    reset_baselines()
    yield
    reset_baselines()


@pytest.fixture()
def cfg() -> Config:
    return Config()


def _prime(name: str, cpu: float, mem: float, n: int, cfg: Config):
    """Feed *n* identical snapshots to build up a baseline."""
    for _ in range(n):
        process_snapshot(_snap(name, cpu, mem), cfg, min_samples=5)


def test_no_spike_reported_before_min_samples(cfg):
    msgs = []
    for _ in range(4):
        result = process_snapshot(_snap("app", 100.0, 500.0), cfg, min_samples=5)
        msgs.extend(result)
    assert msgs == []


def test_no_spike_for_normal_value(cfg):
    _prime("app", 10.0, 100.0, 10, cfg)
    result = process_snapshot(_snap("app", 11.0, 105.0), cfg, min_samples=5)
    assert result == []


def test_cpu_spike_detected(cfg):
    _prime("app", 10.0, 100.0, 10, cfg)
    result = process_snapshot(
        _snap("app", 30.0, 100.0), cfg, cpu_multiplier=2.0, min_samples=5
    )
    assert len(result) == 1
    assert "CPU" in result[0]
    assert "app" in result[0]


def test_mem_spike_detected(cfg):
    _prime("app", 10.0, 100.0, 10, cfg)
    result = process_snapshot(
        _snap("app", 10.0, 250.0), cfg, mem_multiplier=2.0, min_samples=5
    )
    assert len(result) == 1
    assert "MEM" in result[0]


def test_both_spikes_detected(cfg):
    _prime("app", 10.0, 100.0, 10, cfg)
    result = process_snapshot(
        _snap("app", 30.0, 250.0), cfg, cpu_multiplier=2.0, mem_multiplier=2.0, min_samples=5
    )
    assert len(result) == 2


def test_on_spike_callback_called(cfg):
    _prime("app", 10.0, 100.0, 10, cfg)
    received = []
    process_snapshot(
        _snap("app", 30.0, 100.0), cfg, cpu_multiplier=2.0, min_samples=5, on_spike=received.append
    )
    assert len(received) == 1


def test_process_all_aggregates_across_snapshots(cfg):
    for name in ("a", "b"):
        _prime(name, 10.0, 100.0, 10, cfg)
    snaps = [_snap("a", 30.0, 100.0), _snap("b", 30.0, 100.0)]
    msgs = process_all(snaps, cfg, cpu_multiplier=2.0, min_samples=5)
    assert len(msgs) == 2


def test_process_all_empty_list(cfg):
    assert process_all([], cfg) == []
