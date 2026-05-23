import json
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any


@dataclass
class Config:
    cpu_threshold: float = 80.0
    memory_threshold: float = 10.0
    poll_interval: float = 5.0
    webhook_url: str = ""
    notify_desktop: bool = True
    log_file: str = ""


_KNOWN_KEYS = set(Config.__dataclass_fields__.keys())


def from_file(path: str | Path) -> Config:
    """Load a Config from a JSON file; missing file returns defaults."""
    p = Path(path)
    if not p.exists():
        return Config()
    with p.open("r", encoding="utf-8") as fh:
        data: dict[str, Any] = json.load(fh)
    filtered = {k: v for k, v in data.items() if k in _KNOWN_KEYS}
    return Config(**filtered)


def to_file(config: Config, path: str | Path) -> None:
    """Persist a Config to a JSON file."""
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    with p.open("w", encoding="utf-8") as fh:
        json.dump(asdict(config), fh, indent=2)


def validate(config: Config) -> list[str]:
    """Return a list of validation error messages (empty if valid)."""
    errors = []
    if not (0 < config.cpu_threshold <= 100):
        errors.append("cpu_threshold must be between 0 and 100")
    if not (0 < config.memory_threshold <= 100):
        errors.append("memory_threshold must be between 0 and 100")
    if config.poll_interval <= 0:
        errors.append("poll_interval must be positive")
    return errors
