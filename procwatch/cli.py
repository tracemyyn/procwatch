"""Command-line interface for procwatch."""

import argparse
import sys
import time

from procwatch.config import Config, from_file, to_file, validate
from procwatch.monitor import watch


DEFAULT_CONFIG_PATH = "procwatch.toml"


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="procwatch",
        description="Lightweight process monitor that alerts on resource spikes.",
    )
    subparsers = parser.add_subparsers(dest="command")

    # start command
    start_parser = subparsers.add_parser("start", help="Start monitoring processes.")
    start_parser.add_argument(
        "--config",
        default=DEFAULT_CONFIG_PATH,
        help="Path to config file (default: %(default)s).",
    )
    start_parser.add_argument(
        "--interval",
        type=float,
        default=None,
        help="Override poll interval in seconds.",
    )

    # init command
    init_parser = subparsers.add_parser(
        "init", help="Write a default config file and exit."
    )
    init_parser.add_argument(
        "--config",
        default=DEFAULT_CONFIG_PATH,
        help="Destination path for config file (default: %(default)s).",
    )

    return parser


def cmd_init(args: argparse.Namespace) -> int:
    cfg = Config()
    to_file(cfg, args.config)
    print(f"Default config written to {args.config}")
    return 0


def cmd_start(args: argparse.Namespace) -> int:
    cfg = from_file(args.config)
    errors = validate(cfg)
    if errors:
        for err in errors:
            print(f"[config error] {err}", file=sys.stderr)
        return 1

    if args.interval is not None:
        cfg = Config(
            **{**cfg.__dict__, "poll_interval": args.interval}
        )

    print(
        f"procwatch started — interval={cfg.poll_interval}s  "
        f"cpu>{cfg.cpu_threshold}%  mem>{cfg.memory_threshold}MB"
    )
    try:
        watch(cfg)
    except KeyboardInterrupt:
        print("\nprocwatch stopped.")
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    if args.command == "init":
        return cmd_init(args)
    if args.command == "start":
        return cmd_start(args)

    parser.print_help()
    return 0


if __name__ == "__main__":
    sys.exit(main())
