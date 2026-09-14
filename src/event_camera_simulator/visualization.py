"""Event rendering interfaces owned by the visualization member."""

from pathlib import Path

import numpy as np

from .types import EventFrame


def render_event_frame(event_frame: EventFrame) -> np.ndarray:
    """Render ON as red and OFF as blue in a BGR uint8 image."""

    raise NotImplementedError("assigned to Visualization: render event counts")


def overlay_events(
    input_frame: np.ndarray, event_image: np.ndarray, alpha: float = 0.7
) -> np.ndarray:
    """Overlay a rendered event image on one source frame."""

    raise NotImplementedError("assigned to Visualization: implement frame overlay")


def create_demo_video(
    input_video: Path,
    events: np.ndarray,
    output_video: Path,
    accumulation_us: int,
) -> None:
    """Create the final illustrative event-overlay video."""

    raise NotImplementedError("assigned to Visualization: implement demo video output")
