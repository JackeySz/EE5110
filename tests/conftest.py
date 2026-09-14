"""Shared test fixtures should stay small and analytically transparent."""

import numpy as np
import pytest


@pytest.fixture
def constant_log_frames() -> np.ndarray:
    """Three constant 4x5 log-intensity frames."""

    return np.full((3, 4, 5), 0.5, dtype=np.float64)


@pytest.fixture
def three_timestamps() -> np.ndarray:
    """Strictly increasing timestamps in seconds."""

    return np.array([0.0, 0.1, 0.2], dtype=np.float64)
