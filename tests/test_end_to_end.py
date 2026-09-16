"""End-to-end acceptance tests for the video-to-event pipeline."""

from pathlib import Path

import numpy as np
import pytest

from event_camera_simulator.config import config_from_mapping
from event_camera_simulator.event_frames import accumulate_event_frame
from event_camera_simulator.event_io import save_events_npz
from event_camera_simulator.preprocessing import normalize_intensity, to_grayscale, to_log_intensity
from event_camera_simulator.simulator import EventCameraSimulator
from event_camera_simulator.types import validate_events
from event_camera_simulator.video_io import read_video
from event_camera_simulator.visualization import create_demo_video


def _make_bar_video(width: int = 16, height: int = 8, frame_count: int = 6) -> np.ndarray:
    frames = np.zeros((frame_count, height, width, 3), dtype=np.uint8)
    for index in range(frame_count):
        start = min(index, width - 3)
        frames[index, :, start : start + 3, :] = 255
    return frames


def test_end_to_end_pipeline_from_video_to_event_frame(tmp_path: Path) -> None:
    cv2 = pytest.importorskip("cv2")
    output_dir = tmp_path / "pipeline"
    output_dir.mkdir(parents=True, exist_ok=True)
    video_path = output_dir / "bar.mp4"
    event_path = output_dir / "events.npz"
    overlay_path = output_dir / "demo.mp4"

    frames = _make_bar_video(width=16, height=8, frame_count=6)
    writer = cv2.VideoWriter(
        str(video_path),
        cv2.VideoWriter_fourcc(*"mp4v"),
        10.0,
        (16, 8),
    )
    try:
        for frame in frames:
            writer.write(frame)
    finally:
        writer.release()

    config = config_from_mapping(
        {
            "sensor": {
                "threshold_on": 0.2,
                "threshold_off": 0.2,
                "timestamp_resolution_us": 1,
            },
            "noise": {"enabled": False},
        }
    )
    video_data = read_video(video_path)
    gray = to_grayscale(video_data.frames)
    norm = normalize_intensity(gray, input_max=255.0)
    log_frames = to_log_intensity(norm, epsilon=config.sensor.log_epsilon)
    simulator = EventCameraSimulator(config.sensor, config.noise)
    events = simulator.simulate(log_frames, video_data.timestamps)
    validate_events(events)
    save_events_npz(event_path, events)

    event_frame = accumulate_event_frame(
        events,
        0,
        1_000_000,
        video_data.height,
        video_data.width,
    )
    assert event_frame.positive_counts.shape == (video_data.height, video_data.width)
    assert event_frame.negative_counts.shape == (video_data.height, video_data.width)

    create_demo_video(video_path, events, overlay_path, accumulation_us=100_000)

    assert event_path.exists()
    assert overlay_path.exists()
    assert np.any(events["p"] == 1) or np.any(events["p"] == -1)
