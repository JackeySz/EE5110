"""Run deterministic parameter sweeps for threshold, FPS, noise, and accumulation tests."""

import argparse
import csv
import time
from collections.abc import Sequence
from pathlib import Path
from typing import Optional

import numpy as np

from event_camera_simulator.config import NoiseConfig, SensorConfig
from event_camera_simulator.event_frames import accumulate_event_frame
from event_camera_simulator.metrics import calculate_metrics
from event_camera_simulator.preprocessing import normalize_intensity, to_grayscale, to_log_intensity
from event_camera_simulator.simulator import EventCameraSimulator
from event_camera_simulator.video_io import read_video
from event_camera_simulator.visualization import render_event_frame


def build_parser() -> argparse.ArgumentParser:
    """Build the experiment sweep CLI."""

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-dir", type=Path, default=Path("outputs/figures"))
    parser.add_argument("--thresholds", type=float, nargs="+", default=[0.1, 0.2, 0.3, 0.4, 0.5])
    parser.add_argument("--fps-values", type=float, nargs="+", default=[30.0, 60.0, 120.0])
    parser.add_argument("--frames", type=int, default=20)
    parser.add_argument("--width", type=int, default=24)
    parser.add_argument("--height", type=int, default=12)
    parser.add_argument("--duration", type=float, default=1.0)
    parser.add_argument("--accumulation-us", type=int, nargs="+", default=[10_000, 20_000, 50_000])
    parser.add_argument("--video", type=Path, default=Path("data/synthetic/moving_bar.mp4"))
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


def run_noise_comparison(
    fps_values: Sequence[float],
    *,
    frame_count: int = 20,
    height: int = 12,
    width: int = 24,
    duration_seconds: float = 1.0,
) -> list[dict[str, float]]:
    """Compare ideal and noisy results under a range of FPS values."""

    rows: list[dict[str, float]] = []
    for fps in fps_values:
        if fps <= 0:
            raise ValueError("fps values must be positive")
        timestamps = np.linspace(0.0, duration_seconds, frame_count, dtype=np.float64)
        frames = make_ramp_frames(frame_count, height, width)

        ideal_simulator = EventCameraSimulator(
            SensorConfig(threshold_on=0.3, threshold_off=0.3),
            NoiseConfig(enabled=False),
        )
        start = time.perf_counter()
        ideal_events = ideal_simulator.simulate(frames, timestamps)
        ideal_elapsed = time.perf_counter() - start
        ideal_metrics = calculate_metrics(
            ideal_events,
            duration_seconds=duration_seconds,
            processing_seconds=ideal_elapsed,
            frame_count=frame_count,
        )

        noisy_simulator = EventCameraSimulator(
            SensorConfig(threshold_on=0.3, threshold_off=0.3),
            NoiseConfig(
                enabled=True,
                threshold_std=0.04,
                leak_rate_hz=0.8,
                hot_pixel_ratio=0.005,
                hot_pixel_rate_hz=30.0,
                seed=7,
            ),
        )
        start = time.perf_counter()
        noisy_events = noisy_simulator.simulate(frames, timestamps)
        noisy_elapsed = time.perf_counter() - start
        noisy_metrics = calculate_metrics(
            noisy_events,
            duration_seconds=duration_seconds,
            processing_seconds=noisy_elapsed,
            frame_count=frame_count,
        )

        rows.append(
            {
                "fps": fps,
                "ideal_total_events": float(ideal_metrics.total_events),
                "noisy_total_events": float(noisy_metrics.total_events),
                "ideal_event_rate": ideal_metrics.event_rate,
                "noisy_event_rate": noisy_metrics.event_rate,
                "ideal_processing_fps": ideal_metrics.processing_fps,
                "noisy_processing_fps": noisy_metrics.processing_fps,
            }
        )
    return rows


def write_csv(path: Path, rows: Sequence[dict[str, float]]) -> None:
    """Write rows to CSV."""

    output = Path(path)
    output.parent.mkdir(parents=True, exist_ok=True)
    fieldnames = list(rows[0].keys()) if rows else []
    with output.open("w", encoding="utf-8", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def make_plots(
    output_dir: Path,
    threshold_rows: Sequence[dict[str, float]],
    fps_rows: Sequence[dict[str, float]],
) -> None:
    """Generate standard comparison plots for the reporting package."""

    import matplotlib.pyplot as plt

    output_dir.mkdir(parents=True, exist_ok=True)

    thresholds = [row["threshold"] for row in threshold_rows]
    totals = [row["total_events"] for row in threshold_rows]
    figure, axis = plt.subplots()
    axis.plot(thresholds, totals, marker="o")
    axis.set_xlabel("Threshold")
    axis.set_ylabel("Total event count")
    axis.set_title("Threshold vs Event Count")
    axis.set_ylim(bottom=0)
    axis.grid(True)
    figure.savefig(output_dir / "threshold_event_count.png", dpi=200)
    plt.close(figure)

    fps = [row["fps"] for row in fps_rows]
    ideal_total = [row["ideal_total_events"] for row in fps_rows]
    figure, axis = plt.subplots()
    axis.plot(fps, ideal_total, marker="o", label="Ideal")
    axis.set_xlabel("FPS")
    axis.set_ylabel("Total event count")
    axis.set_title("FPS vs Total Events (Ideal)")
    axis.set_ylim(bottom=0)
    axis.legend()
    axis.grid(True)
    figure.savefig(output_dir / "fps_event_count.png", dpi=200)
    plt.close(figure)

    ideal_value = fps_rows[0]["ideal_total_events"]
    noisy_value = fps_rows[0]["noisy_total_events"]
    figure, axis = plt.subplots()
    axis.bar(["Ideal", "Noisy"], [ideal_value, noisy_value])
    axis.set_ylabel("Total events")
    axis.set_title(f"Ideal vs Noisy Event Count (FPS {fps_rows[0]['fps']:.0f})")
    axis.set_ylim(bottom=0)
    axis.grid(axis="y")
    figure.savefig(output_dir / "ideal_vs_noisy.png", dpi=200)
    plt.close(figure)

    processing_fps = [row["ideal_processing_fps"] for row in fps_rows]
    figure, axis = plt.subplots()
    axis.plot(fps, processing_fps, marker="o")
    axis.set_xlabel("FPS")
    axis.set_ylabel("Processing FPS")
    axis.set_title("Processing Throughput")
    axis.set_ylim(bottom=0)
    axis.grid(True)
    figure.savefig(output_dir / "processing_performance.png", dpi=200)
    plt.close(figure)


def make_event_frame_example(output_dir: Path, video_path: Path, duration_seconds: float) -> None:
    """Render a red/blue polarity example from the moving-bar video."""

    import matplotlib.pyplot as plt

    video = read_video(video_path)
    grayscale = to_grayscale(video.frames)
    normalized = normalize_intensity(grayscale, input_max=255.0)
    log_frames = to_log_intensity(normalized, epsilon=1e-3)
    simulator = EventCameraSimulator(
        SensorConfig(threshold_on=0.3, threshold_off=0.3),
        NoiseConfig(enabled=False),
    )
    events = simulator.simulate(log_frames, video.timestamps)
    event_frame = accumulate_event_frame(
        events,
        0,
        int(round(duration_seconds * 1_000_000)),
        video.height,
        video.width,
    )
    image = render_event_frame(event_frame)
    figure, axis = plt.subplots()
    axis.imshow(image[..., ::-1])
    axis.set_title("Moving Bar Event Frame")
    axis.set_xlabel("ON: red   OFF: blue")
    axis.set_xticks([])
    axis.set_yticks([])
    figure.tight_layout()
    figure.savefig(output_dir / "event_frame_example.png", dpi=200)
    plt.close(figure)
    print(
        f"event_frame_example.png: total={events.size}, "
        f"on={np.count_nonzero(events['p'] == 1)}, "
        f"off={np.count_nonzero(events['p'] == -1)}"
    )


def main(argv: Optional[Sequence[str]] = None) -> int:
    args = build_parser().parse_args(argv)
    output_dir = Path(args.output_dir)
    video = read_video(args.video)
    video_duration = video.frames.shape[0] / video.fps
    threshold_rows = run_threshold_sweep(
        args.thresholds,
        frame_count=video.frames.shape[0],
        height=video.height,
        width=video.width,
        duration_seconds=video_duration,
    )
    fps_rows = run_noise_comparison(
        args.fps_values,
        frame_count=video.frames.shape[0],
        height=video.height,
        width=video.width,
        duration_seconds=video_duration,
    )
    write_csv(output_dir / "threshold_sweep.csv", threshold_rows)
    write_csv(output_dir / "fps_noise_comparison.csv", fps_rows)
    make_plots(output_dir, threshold_rows, fps_rows)
    make_event_frame_example(output_dir, args.video, video_duration)
    print(
        f"Video metadata: frames={video.frames.shape[0]}, "
        f"fps={video.fps}, duration={video_duration:.6f}s"
    )
    print("threshold_sweep.csv:")
    for row in threshold_rows:
        print(row)
    print("fps_noise_comparison.csv:")
    for row in fps_rows:
        print(row)
    print(f"Saved sweep data and figures under {output_dir}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
