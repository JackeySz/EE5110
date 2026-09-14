"""Event-frame construction owned by the visualization member."""

import numpy as np

from .types import EventFrame


def accumulate_event_frame(
    events: np.ndarray,
    start_time_us: int,
    end_time_us: int,
    height: int,
    width: int,
) -> EventFrame:
    """Accumulate ON/OFF counts in the half-open interval [start, end)."""

    raise NotImplementedError("assigned to Visualization: implement event accumulation")
