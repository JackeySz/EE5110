"""Command-line entry point."""

import argparse
from collections.abc import Sequence
from pathlib import Path
from typing import Optional

from .config import ConfigError, load_config
from .event_io import save_events_npz
from .preprocessing import normalize_intensity, to_grayscale, to_log_intensity
from .simulator import EventCameraSimulator
from .video_io import VideoIOError, read_video


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
        try:
            video = read_video(args.input, config.input.fps_override)
            grayscale = to_grayscale(video.frames)
            normalized = normalize_intensity(grayscale)
            log_frames = to_log_intensity(normalized, config.sensor.log_epsilon)
            simulator = EventCameraSimulator(config.sensor, config.noise)
            events = simulator.simulate(log_frames, video.timestamps)
            save_events_npz(args.events, events)
        except (OSError, ValueError, TypeError, RuntimeError, VideoIOError) as exc:
            parser.error(str(exc))
        if args.video is not None:
            raise NotImplementedError(
                "overlay video output is assigned to the visualization task; "
                "events were saved successfully"
            )
        print(f"Saved {events.size} events to {args.events}")
        return 0

    parser.error(f"unknown command: {args.command}")
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
