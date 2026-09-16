"""Event-frame construction owned by the visualization member."""

import numpy as np

from .types import EventFrame, validate_events


def accumulate_event_frame(
    events: np.ndarray,
    start_time_us: int,
    end_time_us: int,
    height: int,
    width: int,
) -> EventFrame:
    """Accumulate ON/OFF counts in the half-open interval [start, end)."""

    validate_events(events)
    if end_time_us <= start_time_us:
        raise ValueError("end_time_us must be greater than start_time_us")
    if height <= 0 or width <= 0:
        raise ValueError("height and width must be positive")

    positive_counts = np.zeros((height, width), dtype=np.int32)
    negative_counts = np.zeros((height, width), dtype=np.int32)
    if events.size == 0:
        return EventFrame(positive_counts, negative_counts, start_time_us, end_time_us)

    in_window = (events["t"] >= start_time_us) & (events["t"] < end_time_us)
    selected = events[in_window]
    if selected.size == 0:
        return EventFrame(positive_counts, negative_counts, start_time_us, end_time_us)

    x = selected["x"].astype(np.int64, copy=False)
    y = selected["y"].astype(np.int64, copy=False)
    if np.any(x >= width) or np.any(y >= height):
        raise ValueError("event coordinates exceed the provided frame dimensions")

    positive = selected["p"] == 1
    negative = selected["p"] == -1
    np.add.at(positive_counts, (y[positive], x[positive]), 1)
    np.add.at(negative_counts, (y[negative], x[negative]), 1)
    return EventFrame(positive_counts, negative_counts, start_time_us, end_time_us)
