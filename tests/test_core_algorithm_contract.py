"""Independent acceptance tests for preprocessing and ideal event generation."""

import numpy as np
import pytest

from event_camera_simulator.pixel_model import (
    _detect_array_crossings,
    detect_pixel_crossings,
)
from event_camera_simulator.preprocessing import (
    normalize_intensity,
    to_grayscale,
    to_log_intensity,
)
from event_camera_simulator.types import EVENT_DTYPE, validate_events


def test_bgr_preprocessing_matches_documented_weights() -> None:
    color = np.array([[[[10, 20, 30]]]], dtype=np.uint8)
    grayscale = to_grayscale(color)
    assert grayscale.shape == (1, 1, 1)
    assert grayscale.dtype == np.float64
    assert grayscale[0, 0, 0] == pytest.approx(0.114 * 10 + 0.587 * 20 + 0.299 * 30)


def test_normalization_and_log_intensity_have_known_values() -> None:
    raw = np.array([[[0, 255]]], dtype=np.uint8)
    normalized = normalize_intensity(raw)
    log_values = to_log_intensity(normalized, epsilon=0.001)
    np.testing.assert_allclose(normalized, np.array([[[0.0, 1.0]]]))
    np.testing.assert_allclose(log_values, np.log(normalized + 0.001))


@pytest.mark.parametrize(
    "frames, message",
    [
        (np.array([[[-1.0]]]), "nonnegative"),
        (np.array([[[np.nan]]]), "finite"),
        (np.array([[[1.1]]]), "input_max"),
    ],
)
def test_normalization_rejects_invalid_values(frames: np.ndarray, message: str) -> None:
    with pytest.raises(ValueError, match=message):
        normalize_intensity(frames)


def test_constant_intensity_produces_no_events() -> None:
    result = detect_pixel_crossings(
        start_log_intensity=0.5,
        end_log_intensity=0.5,
        start_time=0.0,
        end_time=0.1,
        reference_log_intensity=0.5,
        threshold_on=0.2,
        threshold_off=0.2,
    )
    assert result.events == []
    assert result.reference_log_intensity == pytest.approx(0.5)


def test_bright_ramp_crosses_each_threshold_once() -> None:
    result = detect_pixel_crossings(
        start_log_intensity=0.0,
        end_log_intensity=0.65,
        start_time=0.0,
        end_time=1.0,
        reference_log_intensity=0.0,
        threshold_on=0.2,
        threshold_off=0.2,
    )
    expected_times = [0.2 / 0.65, 0.4 / 0.65, 0.6 / 0.65]
    assert [polarity for _, polarity in result.events] == [1, 1, 1]
    np.testing.assert_allclose(
        [time for time, _ in result.events],
        expected_times,
    )
    assert result.reference_log_intensity == pytest.approx(0.6)


def test_dark_ramp_crosses_each_threshold_once() -> None:
    result = detect_pixel_crossings(
        start_log_intensity=0.6,
        end_log_intensity=0.0,
        start_time=2.0,
        end_time=3.0,
        reference_log_intensity=0.6,
        threshold_on=0.2,
        threshold_off=0.2,
    )
    assert [polarity for _, polarity in result.events] == [-1, -1, -1]
    np.testing.assert_allclose(
        [time for time, _ in result.events],
        [2.0 + 1.0 / 3.0, 2.0 + 2.0 / 3.0, 3.0],
    )
    assert result.reference_log_intensity == pytest.approx(0.0)


def test_reference_state_survives_frame_boundaries() -> None:
    first = detect_pixel_crossings(0.0, 0.25, 0.0, 1.0, 0.0, 0.2, 0.2)
    second = detect_pixel_crossings(
        0.25,
        0.45,
        1.0,
        2.0,
        first.reference_log_intensity,
        0.2,
        0.2,
    )
    assert len(first.events) == 1
    assert len(second.events) == 1
    assert second.events[0][0] == pytest.approx(1.75)
    assert second.reference_log_intensity == pytest.approx(0.4)


def test_subthreshold_reversal_produces_no_false_off_event() -> None:
    first = detect_pixel_crossings(0.0, 0.25, 0.0, 1.0, 0.0, 0.2, 0.2)
    second = detect_pixel_crossings(
        0.25,
        0.05,
        1.0,
        2.0,
        first.reference_log_intensity,
        0.2,
        0.2,
    )
    assert second.events == []
    assert second.reference_log_intensity == pytest.approx(0.2)


def test_asymmetric_thresholds_apply_correct_polarities() -> None:
    bright = detect_pixel_crossings(0.0, 0.7, 0.0, 1.0, 0.0, 0.3, 0.2)
    dark = detect_pixel_crossings(0.7, 0.0, 1.0, 2.0, 0.6, 0.3, 0.2)
    assert [polarity for _, polarity in bright.events] == [1, 1]
    assert [polarity for _, polarity in dark.events] == [-1, -1, -1]


def test_array_kernel_preserves_coordinates_dtype_sorting_and_reference() -> None:
    start = np.zeros((2, 2), dtype=np.float64)
    end = np.array([[0.0, 0.45], [-0.45, 0.0]], dtype=np.float64)
    threshold = np.full((2, 2), 0.2, dtype=np.float64)
    events, reference = _detect_array_crossings(
        start,
        end,
        0.0,
        1.0,
        start.copy(),
        threshold,
        threshold,
        1,
    )

    assert events.dtype == EVENT_DTYPE
    assert events.size == 4
    validate_events(events)
    assert set(zip(events["x"], events["y"], events["p"])) == {
        (1, 0, 1),
        (0, 1, -1),
    }
    np.testing.assert_allclose(reference, np.array([[0.0, 0.4], [-0.4, 0.0]]))
