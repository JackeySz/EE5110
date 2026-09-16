"""Generate deterministic synthetic videos for event-camera testing."""

import argparse
from collections.abc import Sequence
from pathlib import Path
from typing import Optional

import numpy as np


def build_parser() -> argparse.ArgumentParser:
    """Build the synthetic-video generator CLI."""

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-dir", type=Path, default=Path("data/synthetic"))
    parser.add_argument("--width", type=int, default=64)
    parser.add_argument("--height", type=int, default=32)
    parser.add_argument("--frames", type=int, default=24)
    parser.add_argument("--fps", type=float, default=120.0)
    parser.add_argument("--bar-width", type=int, default=6)
    return parser


def generate_constant_frames(
    *, width: int = 64, height: int = 32, frame_count: int = 24
) -> np.ndarray:
    """Return a constant-brightness BGR uint8 video."""

    return np.full((frame_count, height, width, 3), 180, dtype=np.uint8)


def generate_ramp_frames(
    *, width: int = 64, height: int = 32, frame_count: int = 24
) -> np.ndarray:
    """Return a brightness ramp from dark to bright."""

    frames = np.zeros((frame_count, height, width, 3), dtype=np.uint8)
    for index in range(frame_count):
        value = int(round(255 * index / max(frame_count - 1, 1)))
        frames[index, :, :, :] = value
    return frames


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


def generate_fast_motion_frames(
    *, width: int = 64, height: int = 32, frame_count: int = 24
) -> np.ndarray:
    """Return a fast-moving white square to stress temporal sampling."""

    frames = np.zeros((frame_count, height, width, 3), dtype=np.uint8)
    for index in range(frame_count):
        x = index % width
        y = (index * 2) % height
        frames[index, y : y + 4, x : x + 4, :] = 255
    return frames


def generate_low_contrast_frames(
    *, width: int = 64, height: int = 32, frame_count: int = 24
) -> np.ndarray:
    """Return low-contrast frames with subtle intensity changes."""

    frames = np.zeros((frame_count, height, width, 3), dtype=np.uint8)
    for index in range(frame_count):
        base = 100 + int(index * 4)
        frames[index, :, :, :] = base
    return frames


def write_video(path: Path, frames: np.ndarray, fps: float) -> None:
    """Write BGR frames as a browser-friendly MP4 using a safe codec fallback."""

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
    candidates = [
        ("avc1", "H.264"),
        ("mp4v", "MPEG-4 Part 2"),
        ("MJPG", "MJPEG"),
    ]
    last_error: Optional[Exception] = None
    for fourcc, codec_name in candidates:
        writer = cv2.VideoWriter(
            str(output),
            cv2.VideoWriter_fourcc(*fourcc),
            fps,
            (width, height),
        )
        if not writer.isOpened():
            last_error = RuntimeError(f"codec {codec_name} unavailable for {output}")
            continue
        try:
            for frame in frames:
                writer.write(frame.astype(np.uint8, copy=False))
        finally:
            writer.release()

        capture = cv2.VideoCapture(str(output))
        if not capture.isOpened():
            capture.release()
            last_error = RuntimeError(f"generated video cannot be reopened: {output}")
            continue
        ok, _ = capture.read()
        capture.release()
        if ok:
            return
        last_error = RuntimeError(f"generated video has no readable frames: {output}")

    raise RuntimeError(f"cannot write a valid browser-readable video to {output}: {last_error}")


def main(argv: Optional[Sequence[str]] = None) -> int:
    args = build_parser().parse_args(argv)
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    dataset = {
        "constant_brightness": generate_constant_frames(
            width=args.width,
            height=args.height,
            frame_count=args.frames,
        ),
        "brightness_ramp": generate_ramp_frames(
            width=args.width,
            height=args.height,
            frame_count=args.frames,
        ),
        "moving_bar": generate_moving_bar_frames(
            width=args.width,
            height=args.height,
            frame_count=args.frames,
            bar_width=args.bar_width,
        ),
        "fast_motion": generate_fast_motion_frames(
            width=args.width,
            height=args.height,
            frame_count=args.frames,
        ),
        "low_contrast": generate_low_contrast_frames(
            width=args.width,
            height=args.height,
            frame_count=args.frames,
        ),
    }

    for name, frames in dataset.items():
        output_path = output_dir / f"{name}.mp4"
        write_video(output_path, frames, args.fps)
        print(f"Wrote {frames.shape[0]} frames to {output_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
