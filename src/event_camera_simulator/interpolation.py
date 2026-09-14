"""Analytical crossing-time interpolation and timestamp quantization."""

import numpy as np


def _finite_float(value: float, name: str) -> float:
    """Return a finite Python float or raise an actionable public error."""

    if isinstance(value, (bool, np.bool_)):
        raise TypeError(f"{name} must be a finite real number")
    try:
        result = float(value)
    except (TypeError, ValueError, OverflowError) as exc:
        raise TypeError(f"{name} must be a finite real number") from exc
    if not np.isfinite(result):
        raise ValueError(f"{name} must be finite")
    return result


def interpolate_crossing_time(
    start_log_intensity: float,
    end_log_intensity: float,
    crossing_level: float,
    start_time: float,
    end_time: float,
) -> float:
    """Return the linear threshold-crossing time in seconds.

    The crossing level must lie in the closed intensity interval. A flat
    interval has no uniquely defined crossing time and is rejected.
    """

    start_level = _finite_float(start_log_intensity, "start_log_intensity")
    end_level = _finite_float(end_log_intensity, "end_log_intensity")
    target = _finite_float(crossing_level, "crossing_level")
    time_start = _finite_float(start_time, "start_time")
    time_end = _finite_float(end_time, "end_time")

    if time_end <= time_start:
        raise ValueError("end_time must be greater than start_time")
    if end_level == start_level:
        raise ValueError("cannot interpolate a crossing in a flat intensity interval")
    lower = min(start_level, end_level)
    upper = max(start_level, end_level)
    if target < lower or target > upper:
        raise ValueError("crossing_level must lie within the closed intensity interval")

    fraction = (target - start_level) / (end_level - start_level)
    fraction = min(max(fraction, 0.0), 1.0)
    return time_start + fraction * (time_end - time_start)


def quantize_timestamps_us(times_seconds: np.ndarray, resolution_us: int) -> np.ndarray:
    """Round seconds to int64 microseconds on the configured time grid.

    Halfway cases use NumPy's round-to-nearest, ties-to-even rule. Input shape
    is preserved and no sorting or deduplication is performed.
    """

    if not isinstance(times_seconds, np.ndarray):
        raise TypeError("times_seconds must be a NumPy array")
    if times_seconds.ndim != 1:
        raise ValueError("times_seconds must be one-dimensional")
    if times_seconds.dtype.kind not in "fiu":
        raise TypeError("times_seconds must have a real numeric dtype")
    if not np.all(np.isfinite(times_seconds)):
        raise ValueError("times_seconds must contain only finite values")
    if isinstance(resolution_us, (bool, np.bool_)) or not isinstance(
        resolution_us, (int, np.integer)
    ):
        raise TypeError("resolution_us must be a positive integer")
    resolution = int(resolution_us)
    if resolution <= 0:
        raise ValueError("resolution_us must be a positive integer")

    times = times_seconds.astype(np.float64, copy=False)
    quantized = np.rint(times * 1_000_000.0 / resolution) * resolution
    info = np.iinfo(np.int64)
    if np.any(quantized < info.min) or np.any(quantized > info.max):
        raise OverflowError("quantized timestamps do not fit in int64 microseconds")
    return quantized.astype(np.int64)
