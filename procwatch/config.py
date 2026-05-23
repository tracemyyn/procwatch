"""Configuration loader for procwatch."""

import os
import json
from dataclasses import dataclass, field
from typing import Optional


DEFAULT_CONFIG_PATH = os.path.expanduser("~/.config/procwatch/config.json")


@dataclass
class Config:
    cpu_threshold: float = 85.0        # percent
    memory_threshold: float = 80.0     # percent
    poll_interval: int = 5             # seconds
    webhook_url: Optional[str] = None
    desktop_notify: bool = True
    notify_cooldown: int = 60          # seconds between repeat alerts for same process
    watched_processes: list = field(default_factory=list)  # empty = watch all

    @classmethod
    def from_file(cls, path: str = DEFAULT_CONFIG_PATH) -> "Config":
        if not os.path.exists(path):
            return cls()
        with open(path, "r") as f:
            data = json.load(f)
        return cls(**{k: v for k, v in data.items() if k in cls.__dataclass_fields__})

    def to_file(self, path: str = DEFAULT_CONFIG_PATH) -> None:
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "w") as f:
            json.dump(self.__dict__, f, indent=2)

    def validate(self) -> None:
        if not (0 < self.cpu_threshold <= 100):
            raise ValueError(f"cpu_threshold must be between 0 and 100, got {self.cpu_threshold}")
        if not (0 < self.memory_threshold <= 100):
            raise ValueError(f"memory_threshold must be between 0 and 100, got {self.memory_threshold}")
        if self.poll_interval < 1:
            raise ValueError(f"poll_interval must be >= 1, got {self.poll_interval}")
        if self.notify_cooldown < 0:
            raise ValueError(f"notify_cooldown must be >= 0, got {self.notify_cooldown}")
