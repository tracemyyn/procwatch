"""Tests for procwatch.silencer_integration."""

from __future__ import annotations

from datetime import datetime, time
from unittest.mock import MagicMock

import pytest

from procwatch.notifier import Alert
from procwatch.silencer import SilenceWindow, add_window, reset_silencer
from procwatch.silencer_integration import (
    filter_alerts,
    maybe_dispatch,
    should_suppress_alert,
)


@pytest.fixture(autouse=True)
def clean():
    reset_silencer()
    yield
    reset_silencer()


def _alert(name: str = "python") -> Alert:
    return Alert(
        pid=1,
        process_name=name,
        cpu=90.0,
        memory=50.0,
        message=f"{name} spike",
    )


def _add_window_for(name_glob: str = "*") -> None:
    add_window(
        SilenceWindow(
            name="test",
            start=time(0, 0),
            end=time(23, 59),
            name_glob=name_glob,
            days=list(range(7)),
        )
    )


def test_no_windows_does_not_suppress():
    assert should_suppress_alert(_alert("python")) is False


def test_matching_window_suppresses():
    _add_window_for("py*")
    assert should_suppress_alert(_alert("python")) is True


def test_non_matching_window_does_not_suppress():
    _add_window_for("java*")
    assert should_suppress_alert(_alert("python")) is False


def test_filter_alerts_removes_silenced():
    _add_window_for("py*")
    alerts = [_alert("python"), _alert("java")]
    result = filter_alerts(alerts)
    assert len(result) == 1
    assert result[0].process_name == "java"


def test_filter_alerts_keeps_all_when_no_windows():
    alerts = [_alert("python"), _alert("java")]
    assert len(filter_alerts(alerts)) == 2


def test_maybe_dispatch_calls_fn_when_not_silenced():
    fn = MagicMock(return_value=True)
    result = maybe_dispatch(_alert("python"), fn)
    fn.assert_called_once()
    assert result is True


def test_maybe_dispatch_skips_fn_when_silenced():
    _add_window_for("py*")
    fn = MagicMock()
    result = maybe_dispatch(_alert("python"), fn)
    fn.assert_not_called()
    assert result is None
