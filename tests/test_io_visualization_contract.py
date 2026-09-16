"""Integration and visualization acceptance tests."""

from pathlib import Path

import numpy as np

from event_camera_simulator.config import config_from_mapping
from event_camera_simulator.event_frames import accumulate_event_frame
from event_camera_simulator.event_io import load_events_npz, save_events_npz
from event_camera_simulator.simulator import EventCameraSimulator
from event_camera_simulator.types import EVENT_DTYPE, validate_events
from event_camera_simulator.visualization import overlay_events, render_event_frame


def test_simulator_process_interval_uses_algorithm_threshold_maps() -> None:
    config = config_from_mapping(
        {
            "sensor": {
                "threshold_on": 0.5,
                "threshold_off": 0.5,
                "timestamp_resolution_us": 1,
            }
        }
    )
    simulator = EventCameraSimulator(config.sensor, config.noise)
    first = np.zeros((1, 1), dtype=np.float64)
    second = np.array([[[1.2]]], dtype=np.float64)[0]

    simulator.reset(first)
    events = simulator.process_interval(first, second, 0.0, 1.0)

    validate_events(events)
    assert events.tolist() == [
        (416667, 0, 0, 1),
        (833333, 0, 0, 1),
    ]


def test_simulator_simulate_sorts_events_across_intervals() -> None:
    config = config_from_mapping(
        {
            "sensor": {
                "threshold_on": 0.5,
                "threshold_off": 0.5,
                "timestamp_resolution_us": 1,
            }
        }
    )
    simulator = EventCameraSimulator(config.sensor, config.noise)
    frames = np.array(
        [
            [[0.0, 0.0]],
            [[0.6, -0.6]],
            [[1.2, -1.2]],
        ],
        dtype=np.float64,
    )
    timestamps = np.array([0.0, 1.0, 2.0], dtype=np.float64)

    events = simulator.simulate(frames, timestamps)

    validate_events(events)
    assert events["t"].tolist() == sorted(events["t"].tolist())
    assert events["p"].tolist() == [1, -1, 1, -1]


def test_npz_round_trip_preserves_events(tmp_path: Path) -> None:
    path = tmp_path / "events.npz"
    events = np.array(
        [
            (10, 1, 2, -1),
            (20, 3, 4, 1),
        ],
        dtype=EVENT_DTYPE,
    )

    save_events_npz(path, events)
    loaded = load_events_npz(path)

    assert loaded.dtype == EVENT_DTYPE
    np.testing.assert_array_equal(loaded, events)


def test_accumulation_window_is_half_open() -> None:
    events = np.array(
        [
            (10, 1, 0, 1),
            (19, 1, 0, 1),
            (20, 1, 0, -1),
            (25, 0, 1, -1),
        ],
        dtype=EVENT_DTYPE,
    )

    event_frame = accumulate_event_frame(events, 10, 20, height=2, width=2)

    assert event_frame.start_time_us == 10
    assert event_frame.end_time_us == 20
    np.testing.assert_array_equal(event_frame.positive_counts, [[0, 2], [0, 0]])
    np.testing.assert_array_equal(event_frame.negative_counts, [[0, 0], [0, 0]])


def test_on_is_red_and_off_is_blue_in_bgr() -> None:
    events = np.array(
        [
            (0, 0, 0, 1),
            (0, 1, 0, -1),
            (0, 0, 1, -1),
            (0, 0, 1, 1),
        ],
        dtype=EVENT_DTYPE,
    )
    event_frame = accumulate_event_frame(events, 0, 1, height=2, width=2)

    image = render_event_frame(event_frame)

    assert image.dtype == np.uint8
    assert image.shape == (2, 2, 3)
    assert image[0, 0].tolist() == [0, 0, 255]
    assert image[0, 1].tolist() == [255, 0, 0]
    assert image[1, 0].tolist() == [255, 255, 255]


def test_overlay_events_preserves_shape_and_blends_only_event_pixels() -> None:
    frame = np.full((2, 2, 3), 100, dtype=np.uint8)
    event_image = np.zeros_like(frame)
    event_image[0, 1] = [0, 0, 255]

    result = overlay_events(frame, event_image, alpha=0.5)

    assert result.shape == frame.shape
    assert result.dtype == np.uint8
    assert result[0, 0].tolist() == [100, 100, 100]
    assert result[0, 1].tolist() == [50, 50, 178]
