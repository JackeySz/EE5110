"""Run a deterministic threshold-sensitivity experiment on synthetic frames."""

import argparse
import csv
import time
from collections.abc import Sequence
from pathlib import Path
from typing import Optional

import numpy as np

from event_camera_simulator.config import NoiseConfig, SensorConfig
from event_camera_simulator.metrics import calculate_metrics
from event_camera_simulator.simulator import EventCameraSimulator


def build_parser() -> argparse.ArgumentParser:
    """Build the threshold sweep CLI."""

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=Path("outputs/figures/threshold_sweep.csv"))
    parser.add_argument("--thresholds", type=float, nargs="+", default=[0.1, 0.2, 0.3, 0.4])
    parser.add_argument("--frames", type=int, default=12)
    parser.add_argument("--width", type=int, default=8)
    parser.add_argument("--height", type=int, default=4)
    parser.add_argument("--duration", type=float, default=1.0)
    return parser


def make_ramp_frames(frame_count: int, height: int, width: int) -> np.ndarray:
    """Create a simple log-intensity ramp with opposite edge polarities."""

    if frame_count < 2 or height <= 0 or width <= 1:
        raise ValueError("frame_count >= 2, height > 0, and width > 1 are required")
    levels = np.linspace(0.0, 1.0, frame_count, dtype=np.float64)
    frames = np.zeros((frame_count, height, width), dtype=np.float64)
    midpoint = width // 2
    frames[:, :, :midpoint] = levels[:, None, None]
    frames[:, :, midpoint:] = (1.0 - levels)[:, None, None]
    return frames


def run_threshold_sweep(
    thresholds: Sequence[float],
    *,
    frame_count: int = 12,
    height: int = 4,
    width: int = 8,
    duration_seconds: float = 1.0,
) -> list[dict[str, float]]:
    """Simulate a fixed scene under several symmetric thresholds."""

    if duration_seconds <= 0:
        raise ValueError("duration_seconds must be positive")
    frames = make_ramp_frames(frame_count, height, width)
    timestamps = np.linspace(0.0, duration_seconds, frame_count, dtype=np.float64)
    rows: list[dict[str, float]] = []
    for threshold in thresholds:
        if threshold <= 0:
            raise ValueError("thresholds must be positive")
        sensor = SensorConfig(threshold_on=threshold, threshold_off=threshold)
        simulator = EventCameraSimulator(sensor, NoiseConfig(enabled=False))
        start = time.perf_counter()
        events = simulator.simulate(frames, timestamps)
        elapsed = time.perf_counter() - start
        metrics = calculate_metrics(
            events,
            duration_seconds=duration_seconds,
            processing_seconds=elapsed,
            frame_count=frame_count,
        )
        rows.append(
            {
                "threshold": threshold,
                "total_events": float(metrics.total_events),
                "on_events": float(metrics.on_events),
                "off_events": float(metrics.off_events),
                "event_rate": metrics.event_rate,
                "processing_seconds": metrics.processing_seconds,
                "processing_fps": metrics.processing_fps,
            }
        )
    return rows


def write_csv(path: Path, rows: Sequence[dict[str, float]]) -> None:
    """Write threshold sweep rows to CSV."""

    output = Path(path)
    output.parent.mkdir(parents=True, exist_ok=True)
    fieldnames = [
        "threshold",
        "total_events",
        "on_events",
        "off_events",
        "event_rate",
        "processing_seconds",
        "processing_fps",
    ]
    with output.open("w", encoding="utf-8", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def main(argv: Optional[Sequence[str]] = None) -> int:
    args = build_parser().parse_args(argv)
    rows = run_threshold_sweep(
        args.thresholds,
        frame_count=args.frames,
        height=args.height,
        width=args.width,
        duration_seconds=args.duration,
    )
    write_csv(args.output, rows)
    print(f"Wrote {len(rows)} threshold measurements to {args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
