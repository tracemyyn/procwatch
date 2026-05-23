"""Tests for procwatch.config module."""

import json
import os
import pytest
from procwatch.config import Config


def test_default_config_values():
    cfg = Config()
    assert cfg.cpu_threshold == 85.0
    assert cfg.memory_threshold == 80.0
    assert cfg.poll_interval == 5
    assert cfg.webhook_url is None
    assert cfg.desktop_notify is True
    assert cfg.notify_cooldown == 60
    assert cfg.watched_processes == []


def test_from_file_missing_returns_defaults(tmp_path):
    cfg = Config.from_file(str(tmp_path / "nonexistent.json"))
    assert cfg.cpu_threshold == 85.0


def test_from_file_loads_values(tmp_path):
    config_path = tmp_path / "config.json"
    data = {"cpu_threshold": 70.0, "memory_threshold": 60.0, "poll_interval": 10}
    config_path.write_text(json.dumps(data))

    cfg = Config.from_file(str(config_path))
    assert cfg.cpu_threshold == 70.0
    assert cfg.memory_threshold == 60.0
    assert cfg.poll_interval == 10


def test_from_file_ignores_unknown_keys(tmp_path):
    config_path = tmp_path / "config.json"
    data = {"cpu_threshold": 50.0, "unknown_key": "value"}
    config_path.write_text(json.dumps(data))

    cfg = Config.from_file(str(config_path))
    assert cfg.cpu_threshold == 50.0
    assert not hasattr(cfg, "unknown_key")


def test_to_file_roundtrip(tmp_path):
    config_path = str(tmp_path / "subdir" / "config.json")
    cfg = Config(cpu_threshold=75.0, webhook_url="https://example.com/hook")
    cfg.to_file(config_path)

    assert os.path.exists(config_path)
    loaded = Config.from_file(config_path)
    assert loaded.cpu_threshold == 75.0
    assert loaded.webhook_url == "https://example.com/hook"


def test_validate_passes_for_valid_config():
    cfg = Config()
    cfg.validate()  # should not raise


def test_validate_raises_on_bad_cpu_threshold():
    cfg = Config(cpu_threshold=110.0)
    with pytest.raises(ValueError, match="cpu_threshold"):
        cfg.validate()


def test_validate_raises_on_bad_memory_threshold():
    cfg = Config(memory_threshold=-5.0)
    with pytest.raises(ValueError, match="memory_threshold"):
        cfg.validate()


def test_validate_raises_on_bad_poll_interval():
    cfg = Config(poll_interval=0)
    with pytest.raises(ValueError, match="poll_interval"):
        cfg.validate()


def test_validate_raises_on_negative_cooldown():
    cfg = Config(notify_cooldown=-1)
    with pytest.raises(ValueError, match="notify_cooldown"):
        cfg.validate()
