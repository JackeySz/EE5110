"""Ideal single-pixel event model owned by algorithm member A."""

from .types import PixelCrossingResult


def detect_pixel_crossings(
    start_log_intensity: float,
    end_log_intensity: float,
    start_time: float,
    end_time: float,
    reference_log_intensity: float,
    threshold_on: float,
    threshold_off: float,
) -> PixelCrossingResult:
    """Generate all ideal events for one linearly interpolated interval."""

    raise NotImplementedError("assigned to Algorithm A: implement ideal pixel crossings")
