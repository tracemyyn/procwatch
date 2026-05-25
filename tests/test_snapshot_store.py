"""Tests for procwatch.snapshot_store."""

from __future__ import annotations

import time
from pathlib import Path

import pytest

from procwatch.monitor import ProcessSnapshot
from procwatch.snapshot_store import (
    clear_snapshots,
    load_for_pid,
    load_snapshots,
    reset_store_path,
    save_snapshots,
    set_store_path,
)


@pytest.fixture(autouse=True)
def tmp_store(tmp_path):
    store_file = tmp_path / "test_snapshots.json"
    set_store_path(store_file)
    yield store_file
    reset_store_path()


def _snap(pid: int = 1, name: str = "proc", cpu: float = 1.0, mem: float = 10.0) -> ProcessSnapshot:
    return ProcessSnapshot(pid=pid, name=name, cpu_percent=cpu, memory_mb=mem, timestamp=time.time())


def test_load_returns_empty_when_no_file(tmp_store):
    assert not tmp_store.exists()
    assert load_snapshots() == []


def test_save_and_load_roundtrip():
    snaps = [_snap(pid=1, name="alpha"), _snap(pid=2, name="beta")]
    save_snapshots(snaps)
    loaded = load_snapshots()
    assert len(loaded) == 2
    assert loaded[0].pid == 1
    assert loaded[0].name == "alpha"
    assert loaded[1].pid == 2


def test_save_appends_to_existing():
    save_snapshots([_snap(pid=1)])
    save_snapshots([_snap(pid=2)])
    loaded = load_snapshots()
    assert len(loaded) == 2


def test_clear_removes_file(tmp_store):
    save_snapshots([_snap()])
    assert tmp_store.exists()
    clear_snapshots()
    assert not tmp_store.exists()


def test_clear_on_missing_file_does_not_raise(tmp_store):
    assert not tmp_store.exists()
    clear_snapshots()  # should not raise


def test_load_for_pid_filters_correctly():
    save_snapshots([_snap(pid=10), _snap(pid=20), _snap(pid=10)])
    result = load_for_pid(10)
    assert len(result) == 2
    assert all(s.pid == 10 for s in result)


def test_load_for_pid_returns_empty_when_not_found():
    save_snapshots([_snap(pid=5)])
    assert load_for_pid(999) == []


def test_snapshot_fields_preserved():
    original = _snap(pid=42, name="myproc", cpu=55.5, mem=128.0)
    save_snapshots([original])
    loaded = load_snapshots()[0]
    assert loaded.pid == 42
    assert loaded.name == "myproc"
    assert abs(loaded.cpu_percent - 55.5) < 0.001
    assert abs(loaded.memory_mb - 128.0) < 0.001


def test_timestamp_preserved():
    original = _snap()
    save_snapshots([original])
    loaded = load_snapshots()[0]
    assert abs(loaded.timestamp - original.timestamp) < 0.001
