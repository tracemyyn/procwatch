"""Tests for procwatch.silencer."""

from __future__ import annotations

from datetime import datetime, time

import pytest

from procwatch.silencer import (
    SilenceWindow,
    add_window,
    get_windows,
    is_silenced,
    reset_silencer,
    windows_from_config,
)


@pytest.fixture(autouse=True)
def clean():
    reset_silencer()
    yield
    reset_silencer()


def _window(
    name="maint",
    start="02:00",
    end="04:00",
    name_glob="*",
    days=None,
):
    sh, sm = map(int, start.split(":"))
    eh, em = map(int, end.split(":"))
    return SilenceWindow(
        name=name,
        start=time(sh, sm),
        end=time(eh, em),
        name_glob=name_glob,
        days=days if days is not None else list(range(7)),
    )


def _at(hour: int, minute: int = 0, weekday: int = 0) -> datetime:
    # weekday 0 = Monday
    # Use a known Monday: 2024-01-01 is a Monday
    from datetime import date
    base = date(2024, 1, 1 + weekday)
    return datetime(base.year, base.month, base.day, hour, minute)


def test_no_windows_never_silenced():
    assert is_silenced("python", at=_at(3)) is False


def test_process_inside_window_is_silenced():
    add_window(_window(start="02:00", end="04:00"))
    assert is_silenced("python", at=_at(3)) is True


def test_process_outside_window_not_silenced():
    add_window(_window(start="02:00", end="04:00"))
    assert is_silenced("python", at=_at(5)) is False


def test_glob_match_silences():
    add_window(_window(start="01:00", end="03:00", name_glob="py*"))
    assert is_silenced("python", at=_at(2)) is True


def test_glob_no_match_not_silenced():
    add_window(_window(start="01:00", end="03:00", name_glob="java*"))
    assert is_silenced("python", at=_at(2)) is False


def test_day_restriction_blocks_other_days():
    # Window only on Monday (0)
    add_window(_window(start="01:00", end="03:00", days=[0]))
    # Tuesday = weekday 1
    assert is_silenced("python", at=_at(2, weekday=1)) is False


def test_day_restriction_allows_correct_day():
    add_window(_window(start="01:00", end="03:00", days=[0]))
    assert is_silenced("python", at=_at(2, weekday=0)) is True


def test_midnight_wrapping_window():
    # 23:00 – 01:00 wraps midnight
    add_window(_window(start="23:00", end="01:00"))
    assert is_silenced("svc", at=_at(23, 30)) is True
    assert is_silenced("svc", at=_at(0, 30)) is True
    assert is_silenced("svc", at=_at(2)) is False


def test_get_windows_returns_all_added():
    w1 = _window(name="a")
    w2 = _window(name="b")
    add_window(w1)
    add_window(w2)
    names = [w.name for w in get_windows()]
    assert "a" in names and "b" in names


def test_windows_from_config_parses_correctly():
    cfg = [
        {"name": "nightly", "start": "02:00", "end": "04:00",
         "name_glob": "db*", "days": [0, 1, 2, 3, 4]}
    ]
    windows = windows_from_config(cfg)
    assert len(windows) == 1
    w = windows[0]
    assert w.name == "nightly"
    assert w.start == time(2, 0)
    assert w.end == time(4, 0)
    assert w.name_glob == "db*"
    assert w.days == [0, 1, 2, 3, 4]
