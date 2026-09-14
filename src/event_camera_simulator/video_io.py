"""Video I/O interfaces owned by the integration member."""

from pathlib import Path
from typing import Optional

import numpy as np

from .types import VideoData


class VideoIOError(RuntimeError):
    """Raised when video input or output cannot be processed."""


def read_video(path: Path, fps_override: Optional[float] = None) -> VideoData:
    """Decode a video and construct strictly increasing frame timestamps."""

    source = Path(path)
    if not source.exists():
        raise VideoIOError(f"video file does not exist: {source}")
    if fps_override is not None and fps_override <= 0:
        raise VideoIOError("fps_override must be positive")
    try:
        import cv2  # type: ignore[import-not-found]
    except ImportError as exc:  # pragma: no cover - environment guidance
        raise VideoIOError("OpenCV is required; install the project with the video extra") from exc

    capture = cv2.VideoCapture(str(source))
    if not capture.isOpened():
        raise VideoIOError(f"cannot open video file: {source}")
    try:
        source_fps = float(capture.get(cv2.CAP_PROP_FPS))
        width = int(capture.get(cv2.CAP_PROP_FRAME_WIDTH))
        height = int(capture.get(cv2.CAP_PROP_FRAME_HEIGHT))
        if width <= 0 or height <= 0:
            raise VideoIOError("video reports invalid dimensions")
        effective_fps = float(fps_override) if fps_override is not None else source_fps
        if not np.isfinite(effective_fps) or effective_fps <= 0:
            raise VideoIOError("video FPS is invalid; provide a positive fps_override")

        frames: list[np.ndarray] = []
        while True:
            ok, frame = capture.read()
            if not ok:
                break
            frames.append(frame)
    finally:
        capture.release()

    if not frames:
        raise VideoIOError(f"video contains no decodable frames: {source}")
    frame_array = np.stack(frames, axis=0)
    timestamps = np.arange(frame_array.shape[0], dtype=np.float64) / effective_fps
    return VideoData(
        frames=frame_array,
        timestamps=timestamps,
        fps=effective_fps,
        width=width,
        height=height,
    )
