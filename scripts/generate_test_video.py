"""Generate a deterministic small moving-bar video for integration testing."""

import argparse
from collections.abc import Sequence
from pathlib import Path
from typing import Optional

import numpy as np


def build_parser() -> argparse.ArgumentParser:
    """Build the moving-bar fixture generator CLI."""

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=Path("data/synthetic/moving_bar.mp4"))
    parser.add_argument("--width", type=int, default=64)
    parser.add_argument("--height", type=int, default=32)
    parser.add_argument("--frames", type=int, default=24)
    parser.add_argument("--fps", type=float, default=120.0)
    parser.add_argument("--bar-width", type=int, default=6)
    return parser


def generate_moving_bar_frames(
    *,
    width: int = 64,
    height: int = 32,
    frame_count: int = 24,
    bar_width: int = 6,
) -> np.ndarray:
    """Return BGR uint8 frames containing a white vertical bar moving right."""

    if width <= 0 or height <= 0 or frame_count <= 0 or bar_width <= 0:
        raise ValueError("width, height, frames, and bar_width must be positive")
    if bar_width > width:
        raise ValueError("bar_width must not exceed width")

    frames = np.zeros((frame_count, height, width, 3), dtype=np.uint8)
    travel = max(width - bar_width, 1)
    for index in range(frame_count):
        start_x = round(index * travel / max(frame_count - 1, 1))
        frames[index, :, start_x : start_x + bar_width, :] = 255
    return frames


def write_video(path: Path, frames: np.ndarray, fps: float) -> None:
    """Write BGR frames as MP4 using OpenCV."""

    if fps <= 0:
        raise ValueError("fps must be positive")
    try:
        import cv2  # type: ignore[import-not-found]
    except ImportError as exc:  # pragma: no cover - optional video dependency
        raise RuntimeError("OpenCV is required; install the project with the video extra") from exc

    if frames.ndim != 4 or frames.shape[-1] != 3 or frames.dtype != np.uint8:
        raise ValueError("frames must have shape (T, H, W, 3) and dtype uint8")
    output = Path(path)
    output.parent.mkdir(parents=True, exist_ok=True)
    height, width = frames.shape[1:3]
    writer = cv2.VideoWriter(
        str(output),
        cv2.VideoWriter_fourcc(*"mp4v"),
        fps,
        (width, height),
    )
    if not writer.isOpened():
        raise RuntimeError(f"cannot open video writer for {output}")
    try:
        for frame in frames:
            writer.write(frame)
    finally:
        writer.release()


def main(argv: Optional[Sequence[str]] = None) -> int:
    args = build_parser().parse_args(argv)
    frames = generate_moving_bar_frames(
        width=args.width,
        height=args.height,
        frame_count=args.frames,
        bar_width=args.bar_width,
    )
    write_video(args.output, frames, args.fps)
    print(f"Wrote {frames.shape[0]} frames to {args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
