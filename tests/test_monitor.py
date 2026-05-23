import time
from unittest.mock import MagicMock, patch

import pytest

from procwatch.config import Config
from procwatch.monitor import ProcessSnapshot, get_snapshot, scan_all_processes, watch


@pytest.fixture
def default_config():
    return Config(cpu_threshold=80.0, memory_threshold=10.0, poll_interval=5.0)


def make_snapshot(cpu=50.0, mem=5.0):
    return ProcessSnapshot(pid=1234, name="test", cpu_percent=cpu, memory_percent=mem)


def test_snapshot_exceeds_cpu(default_config):
    snap = make_snapshot(cpu=90.0, mem=5.0)
    assert snap.exceeds_thresholds(default_config) is True


def test_snapshot_exceeds_memory(default_config):
    snap = make_snapshot(cpu=10.0, mem=15.0)
    assert snap.exceeds_thresholds(default_config) is True


def test_snapshot_within_limits(default_config):
    snap = make_snapshot(cpu=50.0, mem=5.0)
    assert snap.exceeds_thresholds(default_config) is False


def test_snapshot_has_timestamp():
    before = time.time()
    snap = make_snapshot()
    after = time.time()
    assert before <= snap.timestamp <= after


@patch("procwatch.monitor.psutil.Process")
def test_get_snapshot_returns_snapshot(mock_process_cls):
    mock_proc = MagicMock()
    mock_proc.name.return_value = "python"
    mock_proc.cpu_percent.return_value = 42.0
    mock_proc.memory_percent.return_value = 3.5
    mock_process_cls.return_value = mock_proc

    snap = get_snapshot(999)
    assert snap is not None
    assert snap.pid == 999
    assert snap.name == "python"
    assert snap.cpu_percent == 42.0
    assert snap.memory_percent == 3.5


@patch("procwatch.monitor.psutil.Process")
def test_get_snapshot_returns_none_on_missing(mock_process_cls):
    import psutil
    mock_process_cls.side_effect = psutil.NoSuchProcess(pid=0)
    snap = get_snapshot(0)
    assert snap is None


@patch("procwatch.monitor.psutil.process_iter")
@patch("procwatch.monitor.get_snapshot")
def test_scan_all_processes_returns_spikes(mock_get_snapshot, mock_iter, default_config):
    proc_mock = MagicMock()
    proc_mock.pid = 42
    mock_iter.return_value = [proc_mock]

    spike = make_snapshot(cpu=95.0, mem=5.0)
    mock_get_snapshot.return_value = spike

    spikes = scan_all_processes(default_config)
    assert len(spikes) == 1
    assert spikes[0].cpu_percent == 95.0


@patch("procwatch.monitor.psutil.process_iter")
@patch("procwatch.monitor.get_snapshot")
def test_scan_all_processes_skips_normal(mock_get_snapshot, mock_iter, default_config):
    proc_mock = MagicMock()
    proc_mock.pid = 42
    mock_iter.return_value = [proc_mock]

    mock_get_snapshot.return_value = make_snapshot(cpu=10.0, mem=1.0)
    spikes = scan_all_processes(default_config)
    assert spikes == []


@patch("procwatch.monitor.scan_all_processes")
@patch("procwatch.monitor.time.sleep", side_effect=StopIteration)
def test_watch_calls_callback_on_spike(mock_sleep, mock_scan, default_config):
    spike = make_snapshot(cpu=95.0)
    mock_scan.return_value = [spike]
    callback = MagicMock()

    with pytest.raises(StopIteration):
        watch(default_config, callback, interval=1.0)

    callback.assert_called_once_with(spike)
