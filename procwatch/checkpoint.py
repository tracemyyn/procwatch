"""Checkpoint module — persists and restores monitor run state across restarts."""

from __future__ import annotations

import json
import os
import time
from dataclasses import asdict, dataclass, field
from typing import Optional

_DEFAULT_PATH = ".procwatch_checkpoint.json"
_store_path: str = _DEFAULT_PATH


@dataclass
class CheckpointState:
    started_at: float = field(default_factory=time.time)
    last_tick_at: float = 0.0
    tick_count: int = 0
    alert_count: int = 0
    config_path: str = ""


def set_checkpoint_path(path: str) -> None:
    global _store_path
    _store_path = path


def reset_checkpoint_path() -> None:
    global _store_path
    _store_path = _DEFAULT_PATH


def save_checkpoint(state: CheckpointState) -> bool:
    """Persist *state* to disk. Returns True on success."""
    try:
        with open(_store_path, "w", encoding="utf-8") as fh:
            json.dump(asdict(state), fh, indent=2)
        return True
    except OSError:
        return False


def load_checkpoint() -> Optional[CheckpointState]:
    """Load a previously saved checkpoint. Returns None if not found or corrupt."""
    if not os.path.exists(_store_path):
        return None
    try:
        with open(_store_path, "r", encoding="utf-8") as fh:
            data = json.load(fh)
        return CheckpointState(
            started_at=float(data.get("started_at", time.time())),
            last_tick_at=float(data.get("last_tick_at", 0.0)),
            tick_count=int(data.get("tick_count", 0)),
            alert_count=int(data.get("alert_count", 0)),
            config_path=str(data.get("config_path", "")),
        )
    except (OSError, json.JSONDecodeError, KeyError, ValueError):
        return None


def clear_checkpoint() -> bool:
    """Delete the checkpoint file. Returns True if deleted, False if absent."""
    try:
        os.remove(_store_path)
        return True
    except FileNotFoundError:
        return False


def update_tick(state: CheckpointState) -> CheckpointState:
    """Return a new state with tick_count incremented and last_tick_at refreshed."""
    return CheckpointState(
        started_at=state.started_at,
        last_tick_at=time.time(),
        tick_count=state.tick_count + 1,
        alert_count=state.alert_count,
        config_path=state.config_path,
    )
