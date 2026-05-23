"""Tests for procwatch.report."""

import time
from unittest.mock import patch

import pytest

from procwatch.monitor import ProcessSnapshot
from procwatch.history import HistoryEntry
from procwatch import report


def _snap(name="python", pid=42, cpu=80.0, mem=300.0, user="alice"):
    return ProcessSnapshot(
        pid=pid, name=name, cpu_percent=cpu, memory_mb=mem, username=user
    )


def _entry(count=3, ts=None):
    ts = ts or time.time()
    return HistoryEntry(alert_count=count, last_alert_ts=ts)


# ---------------------------------------------------------------------------
# format_snapshot_table
# ---------------------------------------------------------------------------

def test_format_snapshot_table_empty():
    assert report.format_snapshot_table([]) == "No processes matched."


def test_format_snapshot_table_contains_pid_and_name():
    with patch("procwatch.report.get_entry", return_value=None):
        out = report.format_snapshot_table([_snap()])
    assert "42" in out
    assert "python" in out


def test_format_snapshot_table_shows_alert_count():
    entry = _entry(count=7)
    with patch("procwatch.report.get_entry", return_value=entry):
        out = report.format_snapshot_table([_snap()])
    assert "7" in out


def test_format_snapshot_table_never_when_no_entry():
    with patch("procwatch.report.get_entry", return_value=None):
        out = report.format_snapshot_table([_snap()])
    assert "never" in out


# ---------------------------------------------------------------------------
# format_summary
# ---------------------------------------------------------------------------

def test_format_summary_empty():
    assert report.format_summary([]) == "No spikes detected."


def test_format_summary_single():
    out = report.format_summary([_snap(cpu=55.0, mem=128.0)])
    assert "python" in out
    assert "55.0" in out
    assert "128.0" in out


def test_format_summary_multiple_unique_names():
    snaps = [_snap(name="python", pid=1), _snap(name="node", pid=2)]
    out = report.format_summary(snaps)
    assert "2 process" in out
    assert "node" in out
    assert "python" in out


def test_format_summary_deduplicates_names():
    snaps = [_snap(name="python", pid=1), _snap(name="python", pid=2)]
    out = report.format_summary(snaps)
    # name should appear only once in the names section
    assert out.count("python") == 1


# ---------------------------------------------------------------------------
# format_alert_line
# ---------------------------------------------------------------------------

def test_format_alert_line_contains_key_fields():
    out = report.format_alert_line(_snap(pid=99, cpu=91.2, mem=512.0))
    assert "99" in out
    assert "91.2" in out
    assert "512.0" in out
    assert "ALERT" in out
