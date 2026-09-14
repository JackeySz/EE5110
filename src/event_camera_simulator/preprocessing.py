"""Image preprocessing extension points owned by algorithm member A."""

from typing import Optional

import numpy as np


def to_grayscale(frames: np.ndarray) -> np.ndarray:
    """Convert input frames to grayscale as specified in the interface contract."""

    raise NotImplementedError("assigned to Algorithm A: implement grayscale conversion")


def normalize_intensity(
    frames: np.ndarray, input_max: Optional[float] = None
) -> np.ndarray:
    """Normalize a validated frame sequence into the range [0, 1]."""

    raise NotImplementedError("assigned to Algorithm A: implement intensity normalization")


def to_log_intensity(frames: np.ndarray, epsilon: float) -> np.ndarray:
    """Convert normalized nonnegative intensity to log intensity."""

    raise NotImplementedError("assigned to Algorithm A: implement log-intensity conversion")
