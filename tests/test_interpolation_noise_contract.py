"""Acceptance tests for analytical timing and reproducible sensor noise."""

import numpy as np
import pytest

from event_camera_simulator.config import NoiseConfig, SensorConfig
from event_camera_simulator.interpolation import (
    interpolate_crossing_time,
    quantize_timestamps_us,
)
from event_camera_simulator.noise import ConfiguredNoiseModel
from event_camera_simulator.types import EVENT_DTYPE, validate_events


def test_crossing_time_matches_closed_form_solution() -> None:
    actual = interpolate_crossing_time(0.1, 0.9, 0.3, 2.0, 4.0)
    assert actual == pytest.approx(2.5)


@pytest.mark.parametrize(
    "arguments, message",
    [
        ((0.1, 0.1, 0.1, 0.0, 1.0), "flat"),
        ((0.1, 0.9, 1.0, 0.0, 1.0), "closed intensity interval"),
        ((0.1, 0.9, 0.3, 1.0, 1.0), "greater"),
    ],
)
def test_crossing_time_rejects_invalid_intervals(
    arguments: tuple[float, float, float, float, float],
    message: str,
) -> None:
    with pytest.raises(ValueError, match=message):
        interpolate_crossing_time(*arguments)


def test_timestamp_quantization_returns_integer_microseconds() -> None:
    times = np.array([0.5e-6, 1.5e-6, 2.5e-6, 11.0e-6])
    result = quantize_timestamps_us(times, resolution_us=1)
    assert result.dtype == np.int64
    np.testing.assert_array_equal(result, np.array([0, 2, 2, 11], dtype=np.int64))


def test_timestamp_quantization_respects_resolution() -> None:
    times = np.array([4.0e-6, 6.0e-6, 14.0e-6, 16.0e-6])
    result = quantize_timestamps_us(times, resolution_us=10)
    np.testing.assert_array_equal(result, np.array([0, 10, 10, 20]))


def test_ideal_noise_model_returns_constant_thresholds_and_no_events() -> None:
    sensor = SensorConfig(threshold_on=0.3, threshold_off=0.2)
    model = ConfiguredNoiseModel(sensor, NoiseConfig(enabled=False))
    model.initialize(3, 4)
    threshold_on, threshold_off = model.threshold_maps()
    np.testing.assert_allclose(threshold_on, 0.3)
    np.testing.assert_allclose(threshold_off, 0.2)
    events = model.generate_background_events(0.0, 1.0)
    assert events.dtype == EVENT_DTYPE
    assert events.size == 0


def test_threshold_maps_are_positive_fixed_and_reproducible() -> None:
    sensor = SensorConfig(threshold_on=0.3, threshold_off=0.25)
    config = NoiseConfig(enabled=True, threshold_std=0.03, seed=123)
    first = ConfiguredNoiseModel(sensor, config)
    second = ConfiguredNoiseModel(sensor, config)
    first.initialize(100, 100)
    second.initialize(100, 100)

    first_on, first_off = first.threshold_maps()
    repeated_on, repeated_off = first.threshold_maps()
    second_on, second_off = second.threshold_maps()
    assert np.all(first_on > 0)
    assert np.all(first_off > 0)
    np.testing.assert_array_equal(first_on, repeated_on)
    np.testing.assert_array_equal(first_off, repeated_off)
    np.testing.assert_array_equal(first_on, second_on)
    np.testing.assert_array_equal(first_off, second_off)
    assert first_on.mean() == pytest.approx(0.3, abs=0.002)
    assert first_on.std() == pytest.approx(0.03, abs=0.002)


def test_same_noise_seed_produces_identical_background_events() -> None:
    sensor = SensorConfig(timestamp_resolution_us=10)
    config = NoiseConfig(
        enabled=True,
        threshold_std=0.0,
        leak_rate_hz=2.0,
        hot_pixel_ratio=0.2,
        hot_pixel_rate_hz=10.0,
        seed=99,
    )
    first = ConfiguredNoiseModel(sensor, config)
    second = ConfiguredNoiseModel(sensor, config)
    first.initialize(12, 10)
    second.initialize(12, 10)
    first_events = first.generate_background_events(0.1, 0.6)
    second_events = second.generate_background_events(0.1, 0.6)

    np.testing.assert_array_equal(first_events, second_events)
    assert first_events.dtype == EVENT_DTYPE
    assert np.all(first_events["t"] >= 100_000)
    assert np.all(first_events["t"] < 600_000)
    assert np.all(first_events["t"] % 10 == 0)
    assert np.all(first_events["p"] == 1)
    validate_events(first_events)
