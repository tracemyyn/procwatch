"""Tests for procwatch.baseline module."""

import pytest

from procwatch.baseline import (
    BaselineProfile,
    all_profiles,
    get_profile,
    is_cpu_spike,
    is_mem_spike,
    record_snapshot,
    reset_baselines,
)
from procwatch.monitor import ProcessSnapshot


def _snap(name: str, cpu: float, mem: float, pid: int = 1) -> ProcessSnapshot:
    return ProcessSnapshot(pid=pid, name=name, cpu_percent=cpu, memory_mb=mem)


@pytest.fixture(autouse=True)
def clean():
    reset_baselines()
    yield
    reset_baselines()


def test_get_profile_returns_none_before_any_record():
    assert get_profile("unknown") is None


def test_record_snapshot_creates_profile():
    snap = _snap("myapp", cpu=10.0, mem=100.0)
    profile = record_snapshot(snap)
    assert profile.name == "myapp"
    assert profile.sample_count == 1


def test_record_snapshot_accumulates_samples():
    for i in range(5):
        record_snapshot(_snap("myapp", cpu=float(i), mem=float(i * 10)))
    profile = get_profile("myapp")
    assert profile is not None
    assert profile.sample_count == 5


def test_avg_cpu_computed_correctly():
    for cpu in [10.0, 20.0, 30.0]:
        record_snapshot(_snap("proc", cpu=cpu, mem=50.0))
    profile = get_profile("proc")
    assert profile.avg_cpu == pytest.approx(20.0)


def test_avg_mem_computed_correctly():
    for mem in [100.0, 200.0, 300.0]:
        record_snapshot(_snap("proc", cpu=5.0, mem=mem))
    profile = get_profile("proc")
    assert profile.avg_mem == pytest.approx(200.0)


def test_max_samples_cap_is_respected():
    for i in range(80):
        record_snapshot(_snap("capped", cpu=float(i), mem=1.0), max_samples=60)
    profile = get_profile("capped")
    assert profile.sample_count == 60


def test_is_cpu_spike_false_when_insufficient_samples():
    for _ in range(4):
        record_snapshot(_snap("few", cpu=5.0, mem=50.0))
    snap = _snap("few", cpu=100.0, mem=50.0)
    assert is_cpu_spike(snap) is False


def test_is_cpu_spike_false_within_normal_range():
    for _ in range(10):
        record_snapshot(_snap("normal", cpu=20.0, mem=50.0))
    snap = _snap("normal", cpu=25.0, mem=50.0)
    assert is_cpu_spike(snap) is False


def test_is_cpu_spike_true_when_exceeds_multiplier():
    for _ in range(10):
        record_snapshot(_snap("spikey", cpu=10.0, mem=50.0))
    snap = _snap("spikey", cpu=25.0, mem=50.0)
    assert is_cpu_spike(snap, multiplier=2.0) is True


def test_is_mem_spike_true_when_exceeds_multiplier():
    for _ in range(10):
        record_snapshot(_snap("memhog", cpu=5.0, mem=100.0))
    snap = _snap("memhog", cpu=5.0, mem=250.0)
    assert is_mem_spike(snap, multiplier=2.0) is True


def test_all_profiles_returns_all_names():
    record_snapshot(_snap("a", cpu=1.0, mem=1.0))
    record_snapshot(_snap("b", cpu=2.0, mem=2.0))
    profiles = all_profiles()
    assert "a" in profiles
    assert "b" in profiles


def test_all_profiles_is_copy():
    record_snapshot(_snap("x", cpu=1.0, mem=1.0))
    copy = all_profiles()
    copy["injected"] = BaselineProfile(name="injected")
    assert "injected" not in all_profiles()
