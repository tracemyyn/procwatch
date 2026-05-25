"""Tests for procwatch.digest_scheduler."""

import time
import pytest

from procwatch.digest import add_to_digest, reset_digest
from procwatch.digest_scheduler import (
    configure,
    reset_digest_scheduler,
    maybe_flush,
    seconds_until_next_flush,
)
from procwatch.notifier import Alert


@pytest.fixture(autouse=True)
def clean():
    reset_digest_scheduler()
    configure(300.0)
    yield
    reset_digest_scheduler()
    configure(300.0)


def _alert() -> Alert:
    return Alert(pid=1, name="proc", cpu=80.0, mem=10.0, trigger="cpu")


def test_no_flush_before_interval():
    fired = []
    configure(60.0)
    now = time.time()
    result = maybe_flush(lambda r, t: fired.append(t), now=now + 10)
    assert result is False
    assert fired == []


def test_flush_fires_after_interval():
    fired = []
    configure(60.0)
    now = time.time()
    result = maybe_flush(lambda r, t: fired.append(t), now=now + 61)
    assert result is True
    assert len(fired) == 1


def test_callback_receives_text_string():
    texts = []
    configure(1.0)
    now = time.time()
    maybe_flush(lambda r, t: texts.append(t), now=now + 2)
    assert isinstance(texts[0], str)


def test_digest_reset_after_flush():
    add_to_digest(_alert())
    configure(1.0)
    now = time.time()
    reports = []
    maybe_flush(lambda r, t: reports.append(r), now=now + 2)
    # after flush, a second flush should see 0 alerts
    reports2 = []
    maybe_flush(lambda r, t: reports2.append(r), now=now + 4)
    assert reports2[0].total_alerts == 0


def test_seconds_until_next_flush_decreases_over_time():
    configure(100.0)
    now = time.time()
    s1 = seconds_until_next_flush(now=now + 10)
    s2 = seconds_until_next_flush(now=now + 20)
    assert s1 > s2


def test_seconds_until_next_flush_not_negative():
    configure(10.0)
    now = time.time()
    val = seconds_until_next_flush(now=now + 9999)
    assert val == 0.0


def test_flush_updates_last_flush_time():
    configure(5.0)
    now = time.time()
    maybe_flush(lambda r, t: None, now=now + 6)
    # should not flush again immediately after
    fired = []
    maybe_flush(lambda r, t: fired.append(1), now=now + 7)
    assert fired == []
