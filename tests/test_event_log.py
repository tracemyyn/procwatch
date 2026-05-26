"""Tests for procwatch.event_log and procwatch.event_log_reporter."""

import time
import pytest

from procwatch.event_log import (
    reset_event_log,
    record_event,
    get_events,
    all_events,
    set_max_entries,
)
from procwatch.event_log_reporter import (
    format_event_line,
    format_event_table,
    format_event_summary,
)


@pytest.fixture(autouse=True)
def clean():
    reset_event_log()
    set_max_entries(500)
    yield
    reset_event_log()


def test_all_events_empty_at_start():
    assert all_events() == []


def test_record_event_creates_entry():
    e = record_event(pid=1, name="proc", message="cpu spike")
    assert e.pid == 1
    assert e.name == "proc"
    assert e.message == "cpu spike"
    assert e.level == "info"


def test_record_event_appears_in_log():
    record_event(pid=2, name="daemon", message="mem spike", level="warning")
    events = all_events()
    assert len(events) == 1
    assert events[0].level == "warning"


def test_record_event_stores_tags():
    e = record_event(pid=3, name="app", message="ok", tags=["web", "prod"])
    assert "web" in e.tags
    assert "prod" in e.tags


def test_get_events_filter_by_pid():
    record_event(pid=10, name="a", message="x")
    record_event(pid=20, name="b", message="y")
    result = get_events(pid=10)
    assert len(result) == 1
    assert result[0].pid == 10


def test_get_events_filter_by_level():
    record_event(pid=1, name="a", message="x", level="info")
    record_event(pid=2, name="b", message="y", level="critical")
    result = get_events(level="critical")
    assert len(result) == 1
    assert result[0].level == "critical"


def test_get_events_filter_by_since():
    now = time.time()
    record_event(pid=1, name="old", message="x", ts=now - 100)
    record_event(pid=2, name="new", message="y", ts=now)
    result = get_events(since=now - 10)
    assert len(result) == 1
    assert result[0].name == "new"


def test_max_entries_evicts_oldest():
    set_max_entries(3)
    for i in range(5):
        record_event(pid=i, name=f"p{i}", message="m")
    events = all_events()
    assert len(events) == 3
    assert events[0].pid == 2  # oldest two evicted


def test_format_event_line_contains_pid_and_name():
    e = record_event(pid=42, name="myproc", message="spike detected")
    line = format_event_line(e)
    assert "42" in line
    assert "myproc" in line
    assert "spike detected" in line


def test_format_event_line_shows_tags():
    e = record_event(pid=1, name="svc", message="ok", tags=["prod"])
    line = format_event_line(e)
    assert "prod" in line


def test_format_event_table_empty():
    result = format_event_table([])
    assert "no events" in result


def test_format_event_table_has_header():
    record_event(pid=1, name="p", message="m")
    result = format_event_table(all_events())
    assert "PID" in result
    assert "NAME" in result


def test_format_event_summary_counts_levels():
    record_event(pid=1, name="a", message="x", level="info")
    record_event(pid=2, name="b", message="y", level="warning")
    record_event(pid=3, name="c", message="z", level="warning")
    summary = format_event_summary(all_events())
    assert "3 total" in summary
    assert "warning" in summary
    assert "info" in summary
