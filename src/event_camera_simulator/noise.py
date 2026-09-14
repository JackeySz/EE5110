"""Reproducible threshold mismatch and background-event noise models."""

import math
from typing import Optional, Protocol, cast

import numpy as np

from .config import NoiseConfig, SensorConfig
from .types import EVENT_DTYPE, empty_events


class NoiseModel(Protocol):
    """Structural protocol implemented by simulator noise models."""

    def initialize(self, height: int, width: int) -> None:
        """Initialize fixed per-sequence state."""

    def threshold_maps(self) -> tuple[np.ndarray, np.ndarray]:
        """Return fixed ON and OFF threshold maps."""

    def generate_background_events(self, start_time: float, end_time: float) -> np.ndarray:
        """Return canonical background events for a half-open time interval."""


class ConfiguredNoiseModel:
    """Configured pixel-threshold, leak-event, and hot-pixel model.

    Threshold maps and the hot-pixel mask are sampled once per call to
    initialize and remain fixed for the sequence. Leak events and hot-pixel
    events use positive polarity, matching the background-activity model in
    the course material.
    """

    def __init__(
        self,
        sensor_config: SensorConfig,
        noise_config: NoiseConfig,
    ) -> None:
        if sensor_config.threshold_on <= 0 or sensor_config.threshold_off <= 0:
            raise ValueError("sensor thresholds must be positive")
        if sensor_config.timestamp_resolution_us <= 0:
            raise ValueError("timestamp resolution must be positive")
        if noise_config.threshold_std < 0:
            raise ValueError("threshold_std cannot be negative")
        if noise_config.leak_rate_hz < 0 or noise_config.hot_pixel_rate_hz < 0:
            raise ValueError("background event rates cannot be negative")
        if not 0 <= noise_config.hot_pixel_ratio <= 1:
            raise ValueError("hot_pixel_ratio must be in [0, 1]")
        if isinstance(noise_config.seed, (bool, np.bool_)) or not isinstance(
            noise_config.seed, (int, np.integer)
        ):
            raise TypeError("noise seed must be an integer")

        self.sensor_config = sensor_config
        self.noise_config = noise_config
        self._rng = np.random.default_rng(int(noise_config.seed))
        self._height: Optional[int] = None
        self._width: Optional[int] = None
        self._threshold_on_map: Optional[np.ndarray] = None
        self._threshold_off_map: Optional[np.ndarray] = None
        self._hot_pixel_mask: Optional[np.ndarray] = None

    def _sample_positive_thresholds(
        self,
        mean: float,
        standard_deviation: float,
        shape: tuple[int, int],
    ) -> np.ndarray:
        """Sample a positive Gaussian threshold map by rejection sampling."""

        if standard_deviation == 0:
            return np.full(shape, mean, dtype=np.float64)
        result = self._rng.normal(mean, standard_deviation, size=shape)
        invalid = result <= 0
        while np.any(invalid):
            result[invalid] = self._rng.normal(
                mean,
                standard_deviation,
                size=int(np.count_nonzero(invalid)),
            )
            invalid = result <= 0
        return result.astype(np.float64, copy=False)

    def initialize(self, height: int, width: int) -> None:
        """Initialize deterministic per-sequence maps and reset the RNG."""

        if isinstance(height, (bool, np.bool_)) or not isinstance(height, (int, np.integer)):
            raise TypeError("height must be a positive integer")
        if isinstance(width, (bool, np.bool_)) or not isinstance(width, (int, np.integer)):
            raise TypeError("width must be a positive integer")
        height_value = int(height)
        width_value = int(width)
        if height_value <= 0 or width_value <= 0:
            raise ValueError("height and width must be positive")
        coordinate_limit = np.iinfo(np.uint16).max + 1
        if height_value > coordinate_limit or width_value > coordinate_limit:
            raise ValueError("height and width exceed the uint16 event coordinate range")

        self._rng = np.random.default_rng(int(self.noise_config.seed))
        self._height = height_value
        self._width = width_value
        shape = (height_value, width_value)
        standard_deviation = self.noise_config.threshold_std if self.noise_config.enabled else 0.0
        self._threshold_on_map = self._sample_positive_thresholds(
            self.sensor_config.threshold_on,
            standard_deviation,
            shape,
        )
        self._threshold_off_map = self._sample_positive_thresholds(
            self.sensor_config.threshold_off,
            standard_deviation,
            shape,
        )
        if self.noise_config.enabled and self.noise_config.hot_pixel_ratio > 0:
            self._hot_pixel_mask = self._rng.random(shape) < self.noise_config.hot_pixel_ratio
        else:
            self._hot_pixel_mask = np.zeros(shape, dtype=np.bool_)

    def _require_initialized(
        self,
    ) -> tuple[int, int, np.ndarray, np.ndarray, np.ndarray]:
        """Return initialized state or fail clearly at the public boundary."""

        if (
            self._height is None
            or self._width is None
            or self._threshold_on_map is None
            or self._threshold_off_map is None
            or self._hot_pixel_mask is None
        ):
            raise RuntimeError("call initialize() before using the noise model")
        return (
            self._height,
            self._width,
            self._threshold_on_map,
            self._threshold_off_map,
            self._hot_pixel_mask,
        )

    def threshold_maps(self) -> tuple[np.ndarray, np.ndarray]:
        """Return copies of the fixed positive ON and OFF threshold maps."""

        _, _, threshold_on, threshold_off, _ = self._require_initialized()
        return threshold_on.copy(), threshold_off.copy()

    def _sample_event_ticks(
        self,
        count: int,
        start_time: float,
        end_time: float,
    ) -> np.ndarray:
        """Sample representable timestamp ticks in a half-open interval."""

        resolution = self.sensor_config.timestamp_resolution_us
        first_tick = math.ceil(start_time * 1_000_000.0 / resolution)
        stop_tick = math.ceil(end_time * 1_000_000.0 / resolution)
        if count == 0 or stop_tick <= first_tick:
            return np.empty(0, dtype=np.int64)
        ticks = self._rng.integers(
            first_tick,
            stop_tick,
            size=count,
            dtype=np.int64,
        )
        return ticks * resolution

    def _build_events(
        self,
        count: int,
        start_time: float,
        end_time: float,
        height: int,
        width: int,
        hot_pixel_mask: Optional[np.ndarray] = None,
    ) -> np.ndarray:
        """Create positive-polarity canonical events at random valid pixels."""

        timestamps = self._sample_event_ticks(count, start_time, end_time)
        if timestamps.size == 0:
            return empty_events()

        events = np.empty(timestamps.size, dtype=EVENT_DTYPE)
        events["t"] = timestamps
        if hot_pixel_mask is None:
            events["x"] = self._rng.integers(0, width, size=timestamps.size, dtype=np.uint16)
            events["y"] = self._rng.integers(0, height, size=timestamps.size, dtype=np.uint16)
        else:
            hot_coordinates = np.argwhere(hot_pixel_mask)
            if hot_coordinates.size == 0:
                return empty_events()
            selected = self._rng.integers(0, hot_coordinates.shape[0], size=timestamps.size)
            events["y"] = hot_coordinates[selected, 0].astype(np.uint16)
            events["x"] = hot_coordinates[selected, 1].astype(np.uint16)
        events["p"] = 1
        return events

    def generate_background_events(self, start_time: float, end_time: float) -> np.ndarray:
        """Generate sorted canonical leak and hot-pixel events in [start, end)."""

        height, width, _, _, hot_pixel_mask = self._require_initialized()
        try:
            time_start = float(start_time)
            time_end = float(end_time)
        except (TypeError, ValueError, OverflowError) as exc:
            raise TypeError("start_time and end_time must be finite numbers") from exc
        if not np.isfinite(time_start) or not np.isfinite(time_end):
            raise ValueError("start_time and end_time must be finite")
        if time_end <= time_start:
            raise ValueError("end_time must be greater than start_time")
        if not self.noise_config.enabled:
            return empty_events()

        duration = time_end - time_start
        leak_expected = self.noise_config.leak_rate_hz * height * width * duration
        leak_count = int(self._rng.poisson(leak_expected))
        leak_events = self._build_events(
            leak_count,
            time_start,
            time_end,
            height,
            width,
        )

        hot_count = int(np.count_nonzero(hot_pixel_mask))
        hot_expected = self.noise_config.hot_pixel_rate_hz * hot_count * duration
        hot_event_count = int(self._rng.poisson(hot_expected))
        hot_events = self._build_events(
            hot_event_count,
            time_start,
            time_end,
            height,
            width,
            hot_pixel_mask,
        )

        if leak_events.size == 0:
            events = hot_events
        elif hot_events.size == 0:
            events = leak_events
        else:
            events = np.concatenate((leak_events, hot_events))
        if events.size == 0:
            return empty_events()
        order = np.lexsort((events["p"], events["x"], events["y"], events["t"]))
        return cast(np.ndarray, events[order])
