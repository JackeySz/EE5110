"""Stateful orchestration boundary for event generation."""

from typing import Optional

import numpy as np

from .config import NoiseConfig, SensorConfig


class EventCameraSimulator:
    """Coordinate frame intervals, pixel state, timing, and optional noise.

    Core event generation remains intentionally unimplemented in the scaffold.
    """

    def __init__(self, sensor_config: SensorConfig, noise_config: NoiseConfig) -> None:
        self.sensor_config = sensor_config
        self.noise_config = noise_config
        self._reference_log_frame: Optional[np.ndarray] = None

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

    def process_interval(
        self,
        previous_log_frame: np.ndarray,
        current_log_frame: np.ndarray,
        previous_time: float,
        current_time: float,
    ) -> np.ndarray:
        """Generate canonical events for one adjacent frame interval."""

        if not self.is_initialized:
            raise RuntimeError("call reset() before process_interval()")
        raise NotImplementedError(
            "integration owner: compose pixel, interpolation, and noise modules"
        )

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
        raise NotImplementedError(
            "integration owner: iterate process_interval() and return sorted events"
        )
