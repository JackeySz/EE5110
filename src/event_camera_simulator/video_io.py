"""Video I/O interfaces owned by the integration member."""

from pathlib import Path
from typing import Optional

from .types import VideoData


class VideoIOError(RuntimeError):
    """Raised when video input or output cannot be processed."""


def read_video(path: Path, fps_override: Optional[float] = None) -> VideoData:
    """Decode a video and construct strictly increasing frame timestamps."""

    raise NotImplementedError("assigned to Integration: implement OpenCV video reading")
