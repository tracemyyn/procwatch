"""Tests for procwatch.digest."""

import time
import pytest

from procwatch.digest import (
    reset_digest,
    add_to_digest,
    build_digest,
    format_digest,
    DigestReport,
)
from procwatch.notifier import Alert


@pytest.fixture(autouse=True)
def clean():
    reset_digest()
    yield
    reset_digest()


def _alert(pid: int = 1, name: str = "proc", cpu: float = 80.0) -> Alert:
    return Alert(pid=pid, name=name, cpu=cpu, mem=10.0, trigger="cpu")


def test_empty_digest_has_zero_alerts():
    report = build_digest()
    assert report.total_alerts == 0


def test_empty_digest_has_no_offenders():
    report = build_digest()
    assert report.top_offenders == []


def test_add_single_alert_increments_total():
    add_to_digest(_alert())
    report = build_digest()
    assert report.total_alerts == 1


def test_top_offenders_sorted_by_count():
    for _ in range(3):
        add_to_digest(_alert(pid=1, name="alpha"))
    for _ in range(5):
        add_to_digest(_alert(pid=2, name="beta"))
    report = build_digest()
    assert report.top_offenders[0] == "2:beta"
    assert report.top_offenders[1] == "1:alpha"


def test_max_offenders_respected():
    for i in range(10):
        add_to_digest(_alert(pid=i, name=f"p{i}"))
    report = build_digest(max_offenders=3)
    assert len(report.top_offenders) == 3


def test_period_start_before_end():
    add_to_digest(_alert())
    report = build_digest()
    assert report.period_start <= report.period_end


def test_format_digest_contains_total():
    add_to_digest(_alert())
    report = build_digest()
    text = format_digest(report)
    assert "Total alerts: 1" in text


def test_format_digest_empty_window_message():
    report = build_digest()
    text = format_digest(report)
    assert "no alerts" in text


def test_format_digest_shows_offender_name():
    add_to_digest(_alert(pid=42, name="myapp"))
    report = build_digest()
    text = format_digest(report)
    assert "42:myapp" in text


def test_reset_clears_accumulated_alerts():
    add_to_digest(_alert())
    reset_digest()
    report = build_digest()
    assert report.total_alerts == 0
