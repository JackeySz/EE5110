"""Canonical shared data types.

Do not change these fields or units without updating docs/INTERFACES.md and
recording a cross-team decision.
"""

from dataclasses import dataclass

import numpy as np

EVENT_DTYPE = np.dtype(
    [
        ("t", np.int64),
        ("x", np.uint16),
        ("y", np.uint16),
        ("p", np.int8),
    ]
)


@dataclass(frozen=True)
class VideoData:
    """Decoded video frames and timing metadata.

    Frames are BGR at the video boundary. Timestamps are float64 seconds.
    """

    frames: np.ndarray
    timestamps: np.ndarray
    fps: float
    width: int
    height: int


@dataclass(frozen=True)
class PixelCrossingResult:
    """Single-pixel events and the reference after an interval."""

    events: list[tuple[float, int]]
    reference_log_intensity: float


@dataclass(frozen=True)
class EventFrame:
    """Separate ON and OFF counts over one half-open time window."""

    positive_counts: np.ndarray
    negative_counts: np.ndarray
    start_time_us: int
    end_time_us: int


@dataclass(frozen=True)
class SimulationMetrics:
    """Basic event-stream and runtime measurements."""

    total_events: int
    on_events: int
    off_events: int
    duration_seconds: float
    event_rate: float
    processing_seconds: float
    processing_fps: float


def empty_events() -> np.ndarray:
    """Return an empty event array with the canonical dtype."""

    return np.empty(0, dtype=EVENT_DTYPE)


def validate_events(events: np.ndarray, *, require_sorted: bool = True) -> None:
    """Validate the canonical event representation.

    Raises:
        TypeError: if the array or dtype is not canonical.
        ValueError: if polarity or ordering is invalid.
    """

    if not isinstance(events, np.ndarray):
        raise TypeError("events must be a NumPy array")
    if events.ndim != 1:
        raise ValueError("events must be a one-dimensional structured array")
    if events.dtype != EVENT_DTYPE:
        raise TypeError(f"events must use EVENT_DTYPE, got {events.dtype!r}")
    if events.size == 0:
        return
    if not np.all(np.isin(events["p"], (-1, 1))):
        raise ValueError("event polarity must be exactly -1 or +1")
    if require_sorted:
        keys = list(zip(events["t"], events["y"], events["x"], events["p"]))
        if keys != sorted(keys):
            raise ValueError("events must be sorted by (t, y, x, p)")
