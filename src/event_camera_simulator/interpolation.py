"""Crossing-time and timestamp extension points owned by algorithm member B."""

import numpy as np


def interpolate_crossing_time(
    start_log_intensity: float,
    end_log_intensity: float,
    crossing_level: float,
    start_time: float,
    end_time: float,
) -> float:
    """Return an analytical linear threshold-crossing time in seconds."""

    raise NotImplementedError("assigned to Algorithm B: implement analytical interpolation")


def quantize_timestamps_us(times_seconds: np.ndarray, resolution_us: int) -> np.ndarray:
    """Quantize floating-point seconds to integer microseconds."""

    raise NotImplementedError("assigned to Algorithm B: implement timestamp quantization")
