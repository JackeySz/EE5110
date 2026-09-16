"""Create a demonstration event-overlay video from an input video and NPZ events."""

import argparse
from collections.abc import Sequence
from pathlib import Path
from typing import Optional

from event_camera_simulator.event_io import load_events_npz
from event_camera_simulator.visualization import create_demo_video


def build_parser() -> argparse.ArgumentParser:
    """Build the demo-video CLI."""

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, required=True)
    parser.add_argument("--events", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--accumulation-us", type=int, default=10_000)
    return parser


def main(argv: Optional[Sequence[str]] = None) -> int:
    args = build_parser().parse_args(argv)
    events = load_events_npz(args.events)
    create_demo_video(
        args.input,
        events,
        args.output,
        args.accumulation_us,
    )
    print(f"Wrote demo video to {args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
