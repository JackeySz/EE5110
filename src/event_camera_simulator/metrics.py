"""Simulation metrics owned by the testing member."""

import numpy as np

from .types import SimulationMetrics, validate_events


def calculate_metrics(
    events: np.ndarray,
    duration_seconds: float,
    processing_seconds: float,
    frame_count: int = 0,
) -> SimulationMetrics:
    """Calculate event counts, rates, and processing throughput."""

    validate_events(events)
    if isinstance(duration_seconds, (bool, np.bool_)):
        raise TypeError("duration_seconds must be a positive finite number")
    if isinstance(processing_seconds, (bool, np.bool_)):
        raise TypeError("processing_seconds must be a nonnegative finite number")
    if isinstance(frame_count, (bool, np.bool_)) or not isinstance(frame_count, (int, np.integer)):
        raise TypeError("frame_count must be a nonnegative integer")

    duration = float(duration_seconds)
    processing = float(processing_seconds)
    frames = int(frame_count)
    if not np.isfinite(duration) or duration <= 0:
        raise ValueError("duration_seconds must be positive and finite")
    if not np.isfinite(processing) or processing < 0:
        raise ValueError("processing_seconds must be nonnegative and finite")
    if frames < 0:
        raise ValueError("frame_count must be nonnegative")

    total_events = int(events.size)
    on_events = int(np.count_nonzero(events["p"] == 1))
    off_events = int(np.count_nonzero(events["p"] == -1))
    processing_fps = frames / processing if frames > 0 and processing > 0 else 0.0
    return SimulationMetrics(
        total_events=total_events,
        on_events=on_events,
        off_events=off_events,
        duration_seconds=duration,
        event_rate=total_events / duration,
        processing_seconds=processing,
        processing_fps=processing_fps,
    )
