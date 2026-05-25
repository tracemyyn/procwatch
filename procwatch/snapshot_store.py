"""Persistent snapshot store: saves and loads process snapshots to/from disk."""

from __future__ import annotations

import json
import os
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import List, Optional

from procwatch.monitor import ProcessSnapshot

DEFAULT_STORE_PATH = Path("procwatch_snapshots.json")

_store_path: Path = DEFAULT_STORE_PATH


def set_store_path(path: Path) -> None:
    """Override the default store file path (useful for testing)."""
    global _store_path
    _store_path = path


def reset_store_path() -> None:
    """Reset store path to default."""
    global _store_path
    _store_path = DEFAULT_STORE_PATH


def _snapshot_to_dict(snap: ProcessSnapshot) -> dict:
    return asdict(snap)


def _dict_to_snapshot(d: dict) -> ProcessSnapshot:
    return ProcessSnapshot(
        pid=d["pid"],
        name=d["name"],
        cpu_percent=d["cpu_percent"],
        memory_mb=d["memory_mb"],
        timestamp=d["timestamp"],
    )


def save_snapshots(snapshots: List[ProcessSnapshot]) -> None:
    """Append a batch of snapshots to the store file."""
    existing = load_snapshots()
    combined = existing + snapshots
    with open(_store_path, "w", encoding="utf-8") as fh:
        json.dump([_snapshot_to_dict(s) for s in combined], fh, indent=2)


def load_snapshots() -> List[ProcessSnapshot]:
    """Load all snapshots from the store file. Returns empty list if missing."""
    if not _store_path.exists():
        return []
    with open(_store_path, "r", encoding="utf-8") as fh:
        raw = json.load(fh)
    return [_dict_to_snapshot(d) for d in raw]


def clear_snapshots() -> None:
    """Delete the store file if it exists."""
    if _store_path.exists():
        _store_path.unlink()


def load_for_pid(pid: int) -> List[ProcessSnapshot]:
    """Return all stored snapshots for a specific PID."""
    return [s for s in load_snapshots() if s.pid == pid]
