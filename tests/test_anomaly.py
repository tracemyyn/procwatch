"""Tests for procwatch.anomaly and procwatch.anomaly_reporter."""

import pytest
from unittest.mock import patch

from procwatch.monitor import ProcessSnapshot
from procwatch.anomaly import AnomalyResult, analyse_anomaly, analyse_all
from procwatch.anomaly_reporter import (
    format_anomaly_line,
    format_anomaly_table,
    format_anomaly_summary,
)


def _snap(pid=1, name="proc", cpu=5.0, mem=100.0):
    return ProcessSnapshot(pid=pid, name=name, cpu_percent=cpu, memory_mb=mem)


# ---------------------------------------------------------------------------
# Helpers to build a fake BaselineProfile
# ---------------------------------------------------------------------------

class _FakeProfile:
    def __init__(self, count, avg_cpu, avg_mem, cpu_m2, mem_m2):
        self.count = count
        self.avg_cpu = avg_cpu
        self.avg_mem = avg_mem
        self.cpu_m2 = cpu_m2
        self.mem_m2 = mem_m2


# ---------------------------------------------------------------------------
# analyse_anomaly
# ---------------------------------------------------------------------------

def test_returns_none_when_no_profile():
    with patch("procwatch.anomaly.get_profile", return_value=None):
        assert analyse_anomaly(_snap()) is None


def test_returns_none_when_too_few_samples():
    profile = _FakeProfile(count=5, avg_cpu=10.0, avg_mem=200.0, cpu_m2=10.0, mem_m2=100.0)
    with patch("procwatch.anomaly.get_profile", return_value=profile):
        assert analyse_anomaly(_snap(), min_samples=10) is None


def test_no_anomaly_within_normal_range():
    # stddev ~1.0 for cpu, mean=10 → z for cpu=10.5 is 0.5 (below 3.0)
    profile = _FakeProfile(count=20, avg_cpu=10.0, avg_mem=200.0,
                           cpu_m2=20.0, mem_m2=2000.0)
    with patch("procwatch.anomaly.get_profile", return_value=profile):
        result = analyse_anomaly(_snap(cpu=10.5, mem=201.0))
    assert result is not None
    assert not result.cpu_anomaly
    assert not result.mem_anomaly


def test_cpu_anomaly_detected():
    # mean=10, stddev=1 → cpu=40 gives z=30 >> 3
    profile = _FakeProfile(count=20, avg_cpu=10.0, avg_mem=200.0,
                           cpu_m2=20.0, mem_m2=2000.0)
    with patch("procwatch.anomaly.get_profile", return_value=profile):
        result = analyse_anomaly(_snap(cpu=40.0, mem=200.0))
    assert result.cpu_anomaly
    assert not result.mem_anomaly


def test_mem_anomaly_detected():
    profile = _FakeProfile(count=20, avg_cpu=10.0, avg_mem=200.0,
                           cpu_m2=20.0, mem_m2=2000.0)
    with patch("procwatch.anomaly.get_profile", return_value=profile):
        result = analyse_anomaly(_snap(cpu=10.0, mem=500.0))
    assert result.mem_anomaly
    assert not result.cpu_anomaly


def test_z_none_when_zero_stddev():
    # cpu_m2=0 → stddev=0 → z should be None
    profile = _FakeProfile(count=20, avg_cpu=10.0, avg_mem=200.0,
                           cpu_m2=0.0, mem_m2=0.0)
    with patch("procwatch.anomaly.get_profile", return_value=profile):
        result = analyse_anomaly(_snap(cpu=999.0, mem=999.0))
    assert result.cpu_z is None
    assert result.mem_z is None
    assert not result.cpu_anomaly
    assert not result.mem_anomaly


# ---------------------------------------------------------------------------
# analyse_all
# ---------------------------------------------------------------------------

def test_analyse_all_filters_non_anomalous():
    normal = _FakeProfile(count=20, avg_cpu=10.0, avg_mem=200.0,
                          cpu_m2=20.0, mem_m2=2000.0)
    snaps = [_snap(pid=1, cpu=10.0, mem=200.0),
             _snap(pid=2, cpu=50.0, mem=200.0)]
    with patch("procwatch.anomaly.get_profile", return_value=normal):
        results = analyse_all(snaps)
    assert len(results) == 1
    assert results[0].pid == 2


# ---------------------------------------------------------------------------
# anomaly_reporter
# ---------------------------------------------------------------------------

def _result(pid=1, name="proc", cpu_z=1.0, mem_z=0.5,
            cpu_anomaly=False, mem_anomaly=False):
    return AnomalyResult(pid=pid, name=name, cpu_z=cpu_z, mem_z=mem_z,
                         cpu_anomaly=cpu_anomaly, mem_anomaly=mem_anomaly)


def test_format_anomaly_table_empty():
    assert format_anomaly_table([]) == "No anomalies detected."


def test_format_anomaly_table_contains_pid_and_name():
    r = _result(pid=42, name="myproc", cpu_anomaly=True)
    table = format_anomaly_table([r])
    assert "42" in table
    assert "myproc" in table
    assert "YES" in table


def test_format_anomaly_summary_counts():
    results = [
        _result(cpu_anomaly=True, mem_anomaly=False),
        _result(cpu_anomaly=False, mem_anomaly=True),
        _result(cpu_anomaly=True, mem_anomaly=True),
    ]
    summary = format_anomaly_summary(results)
    assert "3 process" in summary
    assert "CPU spikes: 2" in summary
    assert "MEM spikes: 2" in summary


def test_format_anomaly_line_none_z():
    r = _result(cpu_z=None, mem_z=None)
    line = format_anomaly_line(r)
    assert "n/a" in line
