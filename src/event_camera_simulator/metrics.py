"""Simulation metrics owned by the testing member."""

import numpy as np

from .types import SimulationMetrics


def calculate_metrics(
    events: np.ndarray,
    duration_seconds: float,
    processing_seconds: float,
    frame_count: int = 0,
) -> SimulationMetrics:
    """Calculate event counts, rates, and processing throughput."""

    raise NotImplementedError("assigned to Testing: implement metrics calculation")
