"""Tests for procwatch.tag_reporter."""

import pytest
from procwatch.monitor import ProcessSnapshot
from procwatch.tag import reset_tagger, add_rule
from procwatch.tag_reporter import format_tag_line, format_tag_table, format_tag_summary


def _snap(pid: int = 1, name: str = "proc", cpu: float = 1.0, mem: float = 2.0) -> ProcessSnapshot:
    return ProcessSnapshot(pid=pid, name=name, cpu=cpu, mem=mem)


@pytest.fixture(autouse=True)
def clean():
    reset_tagger()
    yield
    reset_tagger()


def test_format_tag_line_shows_pid_and_name():
    line = format_tag_line(_snap(pid=123, name="myapp"))
    assert "123" in line
    assert "myapp" in line


def test_format_tag_line_shows_none_when_no_tags():
    line = format_tag_line(_snap())
    assert "(none)" in line


def test_format_tag_line_shows_tag_name():
    add_rule("backend", name_glob="proc")
    line = format_tag_line(_snap(name="proc"))
    assert "backend" in line


def test_format_tag_table_empty():
    result = format_tag_table([])
    assert "No processes" in result


def test_format_tag_table_contains_header():
    result = format_tag_table([_snap()])
    assert "PID" in result
    assert "NAME" in result
    assert "TAGS" in result


def test_format_tag_table_contains_process_row():
    add_rule("web", name_glob="nginx")
    result = format_tag_table([_snap(pid=55, name="nginx")])
    assert "55" in result
    assert "nginx" in result
    assert "web" in result


def test_format_tag_summary_no_tags():
    result = format_tag_summary([_snap()])
    assert "No tags" in result


def test_format_tag_summary_groups_by_tag():
    add_rule("db", name_glob="postgres*")
    snaps = [_snap(name="postgres"), _snap(pid=2, name="postgres-worker")]
    result = format_tag_summary(snaps)
    assert "db" in result
    assert "postgres" in result


def test_format_tag_summary_multiple_tags():
    add_rule("web", name_glob="nginx*")
    add_rule("monitored", name_glob="nginx*")
    result = format_tag_summary([_snap(name="nginx")])
    assert "web" in result
    assert "monitored" in result
