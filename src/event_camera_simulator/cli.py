"""Command-line entry point."""

import argparse
from collections.abc import Sequence
from pathlib import Path
from typing import Optional

from .config import ConfigError, load_config


def build_parser() -> argparse.ArgumentParser:
    """Build the stable command-line interface."""

    parser = argparse.ArgumentParser(prog="event-sim")
    subparsers = parser.add_subparsers(dest="command", required=True)

    validate = subparsers.add_parser("validate-config", help="validate a YAML config")
    validate.add_argument("--config", type=Path, required=True)

    simulate = subparsers.add_parser("simulate", help="run video-to-events simulation")
    simulate.add_argument("--input", type=Path, required=True)
    simulate.add_argument("--config", type=Path, required=True)
    simulate.add_argument("--events", type=Path, required=True)
    simulate.add_argument("--video", type=Path)

    return parser


def main(argv: Optional[Sequence[str]] = None) -> int:
    """Execute the CLI and return a process status code."""

    parser = build_parser()
    args = parser.parse_args(argv)

    try:
        config = load_config(args.config)
    except ConfigError as exc:
        parser.error(str(exc))

    if args.command == "validate-config":
        print(f"Configuration is valid: {args.config}")
        return 0

    if args.command == "simulate":
        del config  # Loaded and validated; orchestration lands in the integration task.
        raise NotImplementedError(
            "simulation pipeline is intentionally unimplemented in the scaffold; "
            "see tasks/io_integration.md"
        )

    parser.error(f"unknown command: {args.command}")
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
