"""Tests for procwatch.history module."""

import time
import pytest

from procwatch import history
from procwatch.history import (
    record_alert,
    is_in_cooldown,
    get_entry,
    clear_history,
    prune_old_entries,
)


@pytest.fixture(autouse=True)
def reset_history():
    """Ensure history is clean before each test."""
    clear_history()
    yield
    clear_history()


def test_record_alert_creates_entry():
    record_alert(pid=100, process_name="myapp")
    entry = get_entry(100, "myapp")
    assert entry is not None
    assert entry.pid == 100
    assert entry.process_name == "myapp"
    assert entry.alert_count == 1


def test_record_alert_increments_count():
    record_alert(pid=100, process_name="myapp")
    record_alert(pid=100, process_name="myapp")
    entry = get_entry(100, "myapp")
    assert entry.alert_count == 2


def test_is_in_cooldown_true_when_recent():
    record_alert(pid=200, process_name="worker")
    assert is_in_cooldown(200, "worker", cooldown_seconds=60) is True


def test_is_in_cooldown_false_when_no_entry():
    assert is_in_cooldown(999, "ghost", cooldown_seconds=60) is False


def test_is_in_cooldown_false_after_window(monkeypatch):
    record_alert(pid=300, process_name="old_proc")
    # Simulate time passing beyond cooldown
    entry = get_entry(300, "old_proc")
    entry.last_alerted_at = time.time() - 120
    assert is_in_cooldown(300, "old_proc", cooldown_seconds=60) is False


def test_get_entry_returns_none_for_unknown():
    assert get_entry(404, "notfound") is None


def test_different_pids_tracked_separately():
    record_alert(pid=1, process_name="app")
    record_alert(pid=2, process_name="app")
    assert get_entry(1, "app").alert_count == 1
    assert get_entry(2, "app").alert_count == 1


def test_prune_old_entries_removes_stale():
    record_alert(pid=10, process_name="stale")
    record_alert(pid=11, process_name="fresh")
    # Make first entry old
    get_entry(10, "stale").last_alerted_at = time.time() - 500
    removed = prune_old_entries(max_age_seconds=300)
    assert removed == 1
    assert get_entry(10, "stale") is None
    assert get_entry(11, "fresh") is not None


def test_prune_removes_nothing_when_all_recent():
    record_alert(pid=20, process_name="proc")
    removed = prune_old_entries(max_age_seconds=3600)
    assert removed == 0


def test_clear_history_empties_all():
    record_alert(pid=1, process_name="a")
    record_alert(pid=2, process_name="b")
    clear_history()
    assert get_entry(1, "a") is None
    assert get_entry(2, "b") is None
