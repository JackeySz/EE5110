"""Stateful orchestration boundary for event generation."""

from typing import Optional

import numpy as np

from .config import NoiseConfig, SensorConfig
from .noise import ConfiguredNoiseModel
from .pixel_model import _detect_array_crossings
from .types import empty_events, validate_events


class EventCameraSimulator:
    """Coordinate frame intervals, pixel state, timing, and optional noise."""

    def __init__(self, sensor_config: SensorConfig, noise_config: NoiseConfig) -> None:
        self.sensor_config = sensor_config
        self.noise_config = noise_config
        self._reference_log_frame: Optional[np.ndarray] = None
        self._noise_model = ConfiguredNoiseModel(sensor_config, noise_config)
        self._threshold_on_map: Optional[np.ndarray] = None
        self._threshold_off_map: Optional[np.ndarray] = None

    @property
    def is_initialized(self) -> bool:
        """Whether a reference frame has been installed."""

        return self._reference_log_frame is not None

    def reset(self, initial_log_frame: np.ndarray) -> None:
        """Validate and copy the initial reference log-intensity frame."""

        frame = np.asarray(initial_log_frame)
        if frame.ndim != 2:
            raise ValueError("initial_log_frame must have shape (H, W)")
        if frame.size == 0:
            raise ValueError("initial_log_frame cannot be empty")
        if not np.issubdtype(frame.dtype, np.floating):
            raise TypeError("initial_log_frame must have a floating-point dtype")
        if not np.all(np.isfinite(frame)):
            raise ValueError("initial_log_frame must contain only finite values")
        self._reference_log_frame = frame.astype(np.float64, copy=True)
        height, width = self._reference_log_frame.shape
        self._noise_model.initialize(height, width)
        self._threshold_on_map, self._threshold_off_map = self._noise_model.threshold_maps()

    def process_interval(
        self,
        previous_log_frame: np.ndarray,
        current_log_frame: np.ndarray,
        previous_time: float,
        current_time: float,
    ) -> np.ndarray:
        """Generate canonical events for one adjacent frame interval."""

        if (
            self._reference_log_frame is None
            or self._threshold_on_map is None
            or self._threshold_off_map is None
        ):
            raise RuntimeError("call reset() before process_interval()")
        previous = np.asarray(previous_log_frame)
        current = np.asarray(current_log_frame)
        if previous.shape != self._reference_log_frame.shape:
            raise ValueError("previous_log_frame must match the initialized frame shape")
        if current.shape != self._reference_log_frame.shape:
            raise ValueError("current_log_frame must match the initialized frame shape")

        ideal_events, updated_reference = _detect_array_crossings(
            previous,
            current,
            previous_time,
            current_time,
            self._reference_log_frame,
            self._threshold_on_map,
            self._threshold_off_map,
            self.sensor_config.timestamp_resolution_us,
        )
        self._reference_log_frame = updated_reference

        background_events = self._noise_model.generate_background_events(previous_time, current_time)
        if ideal_events.size == 0:
            events = background_events
        elif background_events.size == 0:
            events = ideal_events
        else:
            events = np.concatenate((ideal_events, background_events))
        if events.size == 0:
            return empty_events()
        order = np.lexsort((events["p"], events["x"], events["y"], events["t"]))
        sorted_events = events[order]
        validate_events(sorted_events)
        return sorted_events

    def simulate(self, log_frames: np.ndarray, timestamps: np.ndarray) -> np.ndarray:
        """Generate a complete event stream from timestamped log-intensity frames."""

        frames = np.asarray(log_frames)
        times = np.asarray(timestamps)
        if frames.ndim != 3:
            raise ValueError("log_frames must have shape (T, H, W)")
        if frames.shape[0] < 2:
            raise ValueError("at least two frames are required")
        if times.shape != (frames.shape[0],):
            raise ValueError("timestamps must have shape (T,)")
        if not np.all(np.isfinite(frames)) or not np.all(np.isfinite(times)):
            raise ValueError("frames and timestamps must be finite")
        if not np.all(np.diff(times) > 0):
            raise ValueError("timestamps must be strictly increasing")
        self.reset(frames[0])
        event_chunks = [
            self.process_interval(
                frames[index - 1],
                frames[index],
                float(times[index - 1]),
                float(times[index]),
            )
            for index in range(1, frames.shape[0])
        ]
        nonempty_chunks = [chunk for chunk in event_chunks if chunk.size > 0]
        if not nonempty_chunks:
            return empty_events()
        events = np.concatenate(nonempty_chunks)
        order = np.lexsort((events["p"], events["x"], events["y"], events["t"]))
        sorted_events = events[order]
        validate_events(sorted_events)
        return sorted_events
