"""Tests for procwatch.checkpoint."""

from __future__ import annotations

import os
import time

import pytest

from procwatch.checkpoint import (
    CheckpointState,
    clear_checkpoint,
    load_checkpoint,
    reset_checkpoint_path,
    save_checkpoint,
    set_checkpoint_path,
    update_tick,
)


@pytest.fixture(autouse=True)
def tmp_checkpoint(tmp_path):
    path = str(tmp_path / "cp.json")
    set_checkpoint_path(path)
    yield path
    reset_checkpoint_path()


def test_load_returns_none_when_no_file():
    assert load_checkpoint() is None


def test_save_and_load_roundtrip():
    state = CheckpointState(
        started_at=1_000_000.0,
        last_tick_at=1_000_010.0,
        tick_count=5,
        alert_count=2,
        config_path="/etc/procwatch.toml",
    )
    assert save_checkpoint(state) is True
    loaded = load_checkpoint()
    assert loaded is not None
    assert loaded.tick_count == 5
    assert loaded.alert_count == 2
    assert loaded.config_path == "/etc/procwatch.toml"
    assert loaded.started_at == pytest.approx(1_000_000.0)


def test_save_returns_false_on_bad_path():
    set_checkpoint_path("/nonexistent_dir/no_way/cp.json")
    state = CheckpointState()
    assert save_checkpoint(state) is False


def test_clear_removes_file(tmp_checkpoint):
    save_checkpoint(CheckpointState())
    assert os.path.exists(tmp_checkpoint)
    assert clear_checkpoint() is True
    assert not os.path.exists(tmp_checkpoint)


def test_clear_returns_false_when_no_file():
    assert clear_checkpoint() is False


def test_load_returns_none_for_corrupt_file(tmp_checkpoint):
    with open(tmp_checkpoint, "w") as fh:
        fh.write("not json{{")
    assert load_checkpoint() is None


def test_update_tick_increments_count():
    state = CheckpointState(tick_count=3, alert_count=1)
    new_state = update_tick(state)
    assert new_state.tick_count == 4
    assert new_state.alert_count == 1


def test_update_tick_refreshes_last_tick_at():
    before = time.time()
    state = CheckpointState(last_tick_at=0.0)
    new_state = update_tick(state)
    assert new_state.last_tick_at >= before


def test_update_tick_preserves_started_at():
    state = CheckpointState(started_at=42.0)
    new_state = update_tick(state)
    assert new_state.started_at == pytest.approx(42.0)


def test_default_state_has_zero_ticks():
    state = CheckpointState()
    assert state.tick_count == 0
    assert state.alert_count == 0
