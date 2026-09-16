"""Event rendering interfaces owned by the visualization member."""

from pathlib import Path
from typing import cast

import numpy as np

from .event_frames import accumulate_event_frame
from .types import EventFrame, validate_events
from .video_io import VideoIOError, read_video


def render_event_frame(event_frame: EventFrame) -> np.ndarray:
    """Render ON as red and OFF as blue in a BGR uint8 image."""

    positive = np.asarray(event_frame.positive_counts)
    negative = np.asarray(event_frame.negative_counts)
    if positive.shape != negative.shape:
        raise ValueError("positive and negative count arrays must have matching shape")
    if positive.ndim != 2:
        raise ValueError("event count arrays must have shape (H, W)")
    if np.any(positive < 0) or np.any(negative < 0):
        raise ValueError("event count arrays must be nonnegative")

    image = np.zeros((*positive.shape, 3), dtype=np.uint8)
    image[..., 2] = np.where(positive > 0, 255, 0).astype(np.uint8)
    image[..., 0] = np.where(negative > 0, 255, 0).astype(np.uint8)
    both = (positive > 0) & (negative > 0)
    image[both, 1] = 255
    return image


def overlay_events(
    input_frame: np.ndarray, event_image: np.ndarray, alpha: float = 0.7
) -> np.ndarray:
    """Overlay a rendered event image on one source frame."""

    frame = np.asarray(input_frame)
    overlay = np.asarray(event_image)
    if frame.ndim != 3 or frame.shape[-1] != 3:
        raise ValueError("input_frame must have shape (H, W, 3)")
    if overlay.shape != frame.shape:
        raise ValueError("event_image must match input_frame shape")
    if frame.dtype != np.uint8 or overlay.dtype != np.uint8:
        raise TypeError("input_frame and event_image must use dtype uint8")
    if not 0.0 <= alpha <= 1.0:
        raise ValueError("alpha must be in [0, 1]")

    event_mask = np.any(overlay > 0, axis=2)
    result = frame.copy()
    blended = (1.0 - alpha) * frame.astype(np.float64) + alpha * overlay.astype(np.float64)
    result[event_mask] = np.rint(blended[event_mask]).clip(0, 255).astype(np.uint8)
    return cast(np.ndarray, result)


def create_demo_video(
    input_video: Path,
    events: np.ndarray,
    output_video: Path,
    accumulation_us: int,
) -> None:
    """Create the final illustrative event-overlay video."""

    validate_events(events)
    if accumulation_us <= 0:
        raise ValueError("accumulation_us must be positive")
    try:
        import cv2  # type: ignore[import-not-found]
    except ImportError as exc:  # pragma: no cover - optional video dependency
        raise VideoIOError("OpenCV is required; install the project with the video extra") from exc

    video = read_video(input_video)
    output = Path(output_video)
    output.parent.mkdir(parents=True, exist_ok=True)
    writer = cv2.VideoWriter(
        str(output),
        cv2.VideoWriter_fourcc(*"mp4v"),
        video.fps,
        (video.width, video.height),
    )
    if not writer.isOpened():
        raise VideoIOError(f"cannot open video writer for {output}")
    try:
        for index, frame in enumerate(video.frames):
            frame_time_us = int(round(video.timestamps[index] * 1_000_000))
            event_frame = accumulate_event_frame(
                events,
                frame_time_us,
                frame_time_us + accumulation_us,
                video.height,
                video.width,
            )
            event_image = render_event_frame(event_frame)
            writer.write(overlay_events(frame, event_image))
    finally:
        writer.release()
