"""Validated image preprocessing for the event-generation pipeline.

Video frames are BGR at the OpenCV boundary. The mathematical pipeline uses
floating-point grayscale arrays with shape (T, H, W).
"""

from typing import Optional

import numpy as np

_SUPPORTED_DTYPES = {
    np.dtype(np.uint8),
    np.dtype(np.uint16),
    np.dtype(np.float32),
    np.dtype(np.float64),
}


def _validate_frame_array(
    frames: np.ndarray,
    *,
    allowed_dimensions: tuple[int, ...],
) -> np.ndarray:
    """Validate a public frame-array input without changing its values."""

    if not isinstance(frames, np.ndarray):
        raise TypeError("frames must be a NumPy array")
    if frames.ndim not in allowed_dimensions:
        expected = " or ".join(str(value) for value in allowed_dimensions)
        raise ValueError(f"frames must have {expected} dimensions, got shape {frames.shape}")
    if any(size == 0 for size in frames.shape):
        raise ValueError("frames must not contain an empty dimension")
    if frames.dtype not in _SUPPORTED_DTYPES:
        raise TypeError(f"frames must use uint8, uint16, float32, or float64, got {frames.dtype}")
    if np.issubdtype(frames.dtype, np.floating) and not np.all(np.isfinite(frames)):
        raise ValueError("frames must contain only finite values")
    return frames


def to_grayscale(frames: np.ndarray) -> np.ndarray:
    """Convert (T,H,W) or BGR (T,H,W,3) frames to float64 grayscale.

    The BGR coefficients match OpenCV's conventional luminance conversion:
    0.114 B + 0.587 G + 0.299 R.
    """

    array = _validate_frame_array(frames, allowed_dimensions=(3, 4))
    if array.ndim == 3:
        return array.astype(np.float64, copy=True)
    if array.shape[-1] != 3:
        raise ValueError("color frames must have shape (T, H, W, 3) in BGR channel order")

    values = array.astype(np.float64, copy=False)
    grayscale = 0.114 * values[..., 0] + 0.587 * values[..., 1] + 0.299 * values[..., 2]
    return grayscale


def normalize_intensity(frames: np.ndarray, input_max: Optional[float] = None) -> np.ndarray:
    """Normalize a grayscale frame sequence into [0, 1].

    Integer inputs use their dtype maximum when input_max is omitted.
    Floating-point inputs are treated as already normalized unless an explicit
    positive input_max is supplied. Values are validated rather than silently
    clipped because clipping would alter the event model.
    """

    array = _validate_frame_array(frames, allowed_dimensions=(3,))
    values = array.astype(np.float64, copy=False)
    if np.any(values < 0):
        raise ValueError("frames must contain nonnegative intensity values")

    if input_max is None:
        if array.dtype == np.dtype(np.uint8):
            scale = float(np.iinfo(np.uint8).max)
        elif array.dtype == np.dtype(np.uint16):
            scale = float(np.iinfo(np.uint16).max)
        else:
            scale = 1.0
    else:
        if isinstance(input_max, (bool, np.bool_)):
            raise TypeError("input_max must be a positive finite number")
        try:
            scale = float(input_max)
        except (TypeError, ValueError, OverflowError) as exc:
            raise TypeError("input_max must be a positive finite number") from exc
        if not np.isfinite(scale) or scale <= 0:
            raise ValueError("input_max must be a positive finite number")

    if np.any(values > scale):
        raise ValueError(
            f"frame intensity exceeds input_max={scale}; provide the correct input_max"
        )
    normalized = values / scale
    if not np.all(np.isfinite(normalized)):
        raise ValueError("normalization produced non-finite values")
    return normalized


def to_log_intensity(frames: np.ndarray, epsilon: float) -> np.ndarray:
    """Return log(frames + epsilon) for normalized grayscale frames."""

    array = _validate_frame_array(frames, allowed_dimensions=(3,))
    if not np.issubdtype(array.dtype, np.floating):
        raise TypeError("normalized frames must have a floating-point dtype")
    values = array.astype(np.float64, copy=False)
    if np.any(values < 0) or np.any(values > 1):
        raise ValueError("normalized frames must contain values in [0, 1]")

    if isinstance(epsilon, (bool, np.bool_)):
        raise TypeError("epsilon must be a positive finite number")
    try:
        epsilon_value = float(epsilon)
    except (TypeError, ValueError, OverflowError) as exc:
        raise TypeError("epsilon must be a positive finite number") from exc
    if not np.isfinite(epsilon_value) or epsilon_value <= 0:
        raise ValueError("epsilon must be a positive finite number")

    result = np.log(values + epsilon_value)
    if not np.all(np.isfinite(result)):
        raise ValueError("log-intensity conversion produced non-finite values")
    return result
