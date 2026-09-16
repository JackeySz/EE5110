"""Tests for metrics and experiment helpers owned by the testing role."""

import csv
from pathlib import Path

import numpy as np
import pytest

from event_camera_simulator.metrics import calculate_metrics
from event_camera_simulator.types import EVENT_DTYPE
from scripts.analyze_thresholds import run_threshold_sweep, write_csv
from scripts.generate_test_video import generate_moving_bar_frames


def test_calculate_metrics_counts_rates_and_processing_fps() -> None:
    events = np.array(
        [
            (10, 0, 0, 1),
            (20, 1, 0, -1),
            (30, 2, 0, 1),
        ],
        dtype=EVENT_DTYPE,
    )

    metrics = calculate_metrics(
        events,
        duration_seconds=0.5,
        processing_seconds=0.25,
        frame_count=10,
    )

    assert metrics.total_events == 3
    assert metrics.on_events == 2
    assert metrics.off_events == 1
    assert metrics.event_rate == pytest.approx(6.0)
    assert metrics.processing_fps == pytest.approx(40.0)


@pytest.mark.parametrize(
    "duration_seconds, processing_seconds, frame_count, message",
    [
        (0.0, 0.1, 1, "duration"),
        (1.0, -0.1, 1, "processing"),
        (1.0, 0.1, -1, "frame_count"),
    ],
)
def test_calculate_metrics_rejects_invalid_inputs(
    duration_seconds: float,
    processing_seconds: float,
    frame_count: int,
    message: str,
) -> None:
    events = np.empty(0, dtype=EVENT_DTYPE)
    with pytest.raises(ValueError, match=message):
        calculate_metrics(events, duration_seconds, processing_seconds, frame_count)


def test_generate_moving_bar_frames_is_deterministic_bgr_uint8() -> None:
    frames = generate_moving_bar_frames(width=8, height=3, frame_count=4, bar_width=2)
    repeated = generate_moving_bar_frames(width=8, height=3, frame_count=4, bar_width=2)

    assert frames.shape == (4, 3, 8, 3)
    assert frames.dtype == np.uint8
    np.testing.assert_array_equal(frames, repeated)
    assert np.all(frames[0, :, :2, :] == 255)
    assert np.all(frames[0, :, 2:, :] == 0)
    assert np.all(frames[-1, :, -2:, :] == 255)
    assert np.all(frames[-1, :, :-2, :] == 0)


def test_threshold_sweep_event_counts_drop_as_threshold_increases() -> None:
    rows = run_threshold_sweep([0.25, 0.5], frame_count=3, height=2, width=4, duration_seconds=1.0)

    assert [row["threshold"] for row in rows] == [0.25, 0.5]
    assert rows[0]["total_events"] > rows[1]["total_events"]
    assert rows[0]["on_events"] == rows[0]["off_events"]
    assert rows[1]["on_events"] == rows[1]["off_events"]


def test_threshold_sweep_csv_writer(tmp_path: Path) -> None:
    output = tmp_path / "sweep.csv"
    rows = [{"threshold": 0.5, "total_events": 4.0, "on_events": 2.0, "off_events": 2.0}]

    write_csv(output, rows)

    with output.open("r", encoding="utf-8", newline="") as stream:
        loaded = list(csv.DictReader(stream))
    assert loaded[0]["threshold"] == "0.5"
    assert loaded[0]["total_events"] == "4.0"
