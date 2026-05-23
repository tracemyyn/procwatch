"""Tests for the procwatch CLI."""

import pytest
from unittest.mock import MagicMock, patch

from procwatch.cli import build_parser, cmd_init, cmd_start, main
from procwatch.config import Config


# ---------------------------------------------------------------------------
# build_parser
# ---------------------------------------------------------------------------

def test_parser_start_defaults():
    parser = build_parser()
    args = parser.parse_args(["start"])
    assert args.command == "start"
    assert args.config == "procwatch.toml"
    assert args.interval is None


def test_parser_start_custom_flags():
    parser = build_parser()
    args = parser.parse_args(["start", "--config", "my.toml", "--interval", "5"])
    assert args.config == "my.toml"
    assert args.interval == 5.0


def test_parser_init_defaults():
    parser = build_parser()
    args = parser.parse_args(["init"])
    assert args.command == "init"
    assert args.config == "procwatch.toml"


def test_parser_no_command_returns_zero(capsys):
    result = main([])
    assert result == 0
    captured = capsys.readouterr()
    assert "usage" in captured.out.lower() or "procwatch" in captured.out.lower()


# ---------------------------------------------------------------------------
# cmd_init
# ---------------------------------------------------------------------------

def test_cmd_init_writes_file(tmp_path):
    dest = tmp_path / "test.toml"
    args = MagicMock(config=str(dest))
    with patch("procwatch.cli.to_file") as mock_to_file:
        result = cmd_init(args)
    mock_to_file.assert_called_once()
    assert result == 0


# ---------------------------------------------------------------------------
# cmd_start
# ---------------------------------------------------------------------------

def test_cmd_start_returns_1_on_invalid_config():
    args = MagicMock(config="missing.toml", interval=None)
    fake_cfg = Config(cpu_threshold=-1)  # triggers validation error
    with patch("procwatch.cli.from_file", return_value=fake_cfg), \
         patch("procwatch.cli.validate", return_value=["cpu_threshold must be > 0"]):
        result = cmd_start(args)
    assert result == 1


def test_cmd_start_calls_watch():
    args = MagicMock(config="procwatch.toml", interval=None)
    fake_cfg = Config()
    with patch("procwatch.cli.from_file", return_value=fake_cfg), \
         patch("procwatch.cli.validate", return_value=[]), \
         patch("procwatch.cli.watch", side_effect=KeyboardInterrupt) as mock_watch:
        result = cmd_start(args)
    mock_watch.assert_called_once_with(fake_cfg)
    assert result == 0


def test_cmd_start_overrides_interval():
    args = MagicMock(config="procwatch.toml", interval=2.5)
    fake_cfg = Config(poll_interval=10.0)
    captured_cfg = {}

    def fake_watch(cfg):
        captured_cfg["cfg"] = cfg
        raise KeyboardInterrupt

    with patch("procwatch.cli.from_file", return_value=fake_cfg), \
         patch("procwatch.cli.validate", return_value=[]), \
         patch("procwatch.cli.watch", side_effect=fake_watch):
        cmd_start(args)

    assert captured_cfg["cfg"].poll_interval == 2.5


def test_main_init_integration(tmp_path):
    dest = str(tmp_path / "out.toml")
    with patch("procwatch.cli.to_file") as mock_to_file:
        result = main(["init", "--config", dest])
    assert result == 0
    mock_to_file.assert_called_once()
