"""Ideal single-pixel and private array-level event-generation kernels."""

import math

import numpy as np

from .interpolation import interpolate_crossing_time, quantize_timestamps_us
from .types import EVENT_DTYPE, PixelCrossingResult, empty_events


def _finite_float(value: float, name: str) -> float:
    """Convert a scalar input to a finite Python float."""

    if isinstance(value, (bool, np.bool_)):
        raise TypeError(f"{name} must be a finite real number")
    try:
        result = float(value)
    except (TypeError, ValueError, OverflowError) as exc:
        raise TypeError(f"{name} must be a finite real number") from exc
    if not np.isfinite(result):
        raise ValueError(f"{name} must be finite")
    return result


def _threshold_reached(distance: float, threshold: float) -> bool:
    """Compare a contrast distance to a threshold robustly at equality."""

    return distance > threshold or math.isclose(distance, threshold, rel_tol=1e-12, abs_tol=1e-12)


def _crossing_count(distance: float, threshold: float) -> int:
    """Return the number of complete threshold steps in a distance."""

    if distance < 0 and not math.isclose(distance, 0.0, rel_tol=0.0, abs_tol=1e-12):
        return 0
    ratio = max(distance, 0.0) / threshold
    nearest = round(ratio)
    if math.isclose(ratio, nearest, rel_tol=1e-12, abs_tol=1e-12):
        ratio = float(nearest)
    return max(0, math.floor(ratio))


def detect_pixel_crossings(
    start_log_intensity: float,
    end_log_intensity: float,
    start_time: float,
    end_time: float,
    reference_log_intensity: float,
    threshold_on: float,
    threshold_off: float,
) -> PixelCrossingResult:
    """Generate all ideal events for one monotonic linear frame interval.

    Returned event times are floating-point seconds. The reference is advanced
    by exactly one applicable threshold for every emitted event.
    """

    start_level = _finite_float(start_log_intensity, "start_log_intensity")
    end_level = _finite_float(end_log_intensity, "end_log_intensity")
    time_start = _finite_float(start_time, "start_time")
    time_end = _finite_float(end_time, "end_time")
    reference = _finite_float(reference_log_intensity, "reference_log_intensity")
    threshold_positive = _finite_float(threshold_on, "threshold_on")
    threshold_negative = _finite_float(threshold_off, "threshold_off")

    if time_end <= time_start:
        raise ValueError("end_time must be greater than start_time")
    if threshold_positive <= 0 or threshold_negative <= 0:
        raise ValueError("threshold_on and threshold_off must be positive")

    events: list[tuple[float, int]] = []

    # Catch up a reference exactly at or beyond a threshold at the start. A
    # correctly chained simulator normally has no overdue contrast, but this
    # makes the public single-pixel contract well-defined for standalone use.
    while _threshold_reached(start_level - reference, threshold_positive):
        events.append((time_start, 1))
        reference += threshold_positive
    while _threshold_reached(reference - start_level, threshold_negative):
        events.append((time_start, -1))
        reference -= threshold_negative

    if end_level > start_level:
        count = _crossing_count(end_level - reference, threshold_positive)
        for _ in range(count):
            target = reference + threshold_positive
            interpolation_target = target
            if target > end_level and math.isclose(target, end_level, rel_tol=1e-12, abs_tol=1e-12):
                interpolation_target = end_level
            event_time = interpolate_crossing_time(
                start_level,
                end_level,
                interpolation_target,
                time_start,
                time_end,
            )
            events.append((event_time, 1))
            reference = target
    elif end_level < start_level:
        count = _crossing_count(reference - end_level, threshold_negative)
        for _ in range(count):
            target = reference - threshold_negative
            interpolation_target = target
            if target < end_level and math.isclose(target, end_level, rel_tol=1e-12, abs_tol=1e-12):
                interpolation_target = end_level
            event_time = interpolate_crossing_time(
                start_level,
                end_level,
                interpolation_target,
                time_start,
                time_end,
            )
            events.append((event_time, -1))
            reference = target

    return PixelCrossingResult(
        events=events,
        reference_log_intensity=reference,
    )


def _detect_array_crossings(
    start_log_frame: np.ndarray,
    end_log_frame: np.ndarray,
    start_time: float,
    end_time: float,
    reference_log_frame: np.ndarray,
    threshold_on_map: np.ndarray,
    threshold_off_map: np.ndarray,
    timestamp_resolution_us: int,
) -> tuple[np.ndarray, np.ndarray]:
    """Vectorize ideal threshold crossings over one complete pixel array.

    This is a private integration kernel: it preserves the public scalar API
    while avoiding nested Python loops over pixels. It returns canonical,
    deterministically sorted events and a new reference frame.
    """

    arrays = {
        "start_log_frame": start_log_frame,
        "end_log_frame": end_log_frame,
        "reference_log_frame": reference_log_frame,
        "threshold_on_map": threshold_on_map,
        "threshold_off_map": threshold_off_map,
    }
    converted: dict[str, np.ndarray] = {}
    for name, value in arrays.items():
        if not isinstance(value, np.ndarray):
            raise TypeError(f"{name} must be a NumPy array")
        if value.ndim != 2:
            raise ValueError(f"{name} must have shape (H, W)")
        if not np.issubdtype(value.dtype, np.floating):
            raise TypeError(f"{name} must have a floating-point dtype")
        if not np.all(np.isfinite(value)):
            raise ValueError(f"{name} must contain only finite values")
        converted[name] = value.astype(np.float64, copy=False)

    start = converted["start_log_frame"]
    end = converted["end_log_frame"]
    reference = converted["reference_log_frame"].copy()
    threshold_on = converted["threshold_on_map"]
    threshold_off = converted["threshold_off_map"]
    shape = start.shape
    if any(value.shape != shape for value in converted.values()):
        raise ValueError("all frame, reference, and threshold arrays must share shape (H, W)")
    if any(size == 0 for size in shape):
        raise ValueError("pixel-array inputs must not be empty")
    if shape[0] > np.iinfo(np.uint16).max + 1 or shape[1] > np.iinfo(np.uint16).max + 1:
        raise ValueError("pixel-array dimensions exceed the uint16 event coordinate range")
    if np.any(threshold_on <= 0) or np.any(threshold_off <= 0):
        raise ValueError("threshold maps must contain only positive values")

    time_start = _finite_float(start_time, "start_time")
    time_end = _finite_float(end_time, "end_time")
    if time_end <= time_start:
        raise ValueError("end_time must be greater than start_time")
    quantize_timestamps_us(np.empty(0, dtype=np.float64), timestamp_resolution_us)

    time_parts: list[np.ndarray] = []
    x_parts: list[np.ndarray] = []
    y_parts: list[np.ndarray] = []
    polarity_parts: list[np.ndarray] = []

    def append_events(
        mask: np.ndarray,
        event_times: np.ndarray,
        polarity: int,
    ) -> None:
        rows, columns = np.nonzero(mask)
        if rows.size == 0:
            return
        time_parts.append(event_times.astype(np.float64, copy=False))
        x_parts.append(columns.astype(np.uint16, copy=False))
        y_parts.append(rows.astype(np.uint16, copy=False))
        polarity_parts.append(np.full(rows.size, polarity, dtype=np.int8))

    # Handle exact threshold equality at the interval start without duplicating
    # it in later crossing layers.
    residual = start - reference
    tolerance = 1e-12
    if np.any(residual > threshold_on + tolerance) or np.any(residual < -threshold_off - tolerance):
        raise ValueError("reference_log_frame is more than one threshold behind start_log_frame")
    due_on = np.isclose(residual, threshold_on, rtol=1e-12, atol=1e-12)
    due_off = np.isclose(residual, -threshold_off, rtol=1e-12, atol=1e-12)
    append_events(due_on, np.full(np.count_nonzero(due_on), time_start), 1)
    append_events(due_off, np.full(np.count_nonzero(due_off), time_start), -1)
    reference[due_on] += threshold_on[due_on]
    reference[due_off] -= threshold_off[due_off]

    rising = end > start
    falling = end < start
    on_ratio = np.where(rising, np.maximum((end - reference) / threshold_on, 0.0), 0.0)
    off_ratio = np.where(
        falling,
        np.maximum((reference - end) / threshold_off, 0.0),
        0.0,
    )
    int64_max = float(np.iinfo(np.int64).max)
    if np.any(on_ratio > int64_max) or np.any(off_ratio > int64_max):
        raise OverflowError("threshold configuration would generate too many events")
    on_counts = np.floor(np.nextafter(on_ratio, np.inf)).astype(np.int64)
    off_counts = np.floor(np.nextafter(off_ratio, np.inf)).astype(np.int64)

    interval_reference = reference.copy()
    duration = time_end - time_start
    maximum_on = int(on_counts.max(initial=0))
    for crossing_index in range(1, maximum_on + 1):
        mask = on_counts >= crossing_index
        rows, columns = np.nonzero(mask)
        targets = interval_reference[rows, columns] + crossing_index * threshold_on[rows, columns]
        fractions = (targets - start[rows, columns]) / (end[rows, columns] - start[rows, columns])
        event_times = time_start + np.clip(fractions, 0.0, 1.0) * duration
        append_events(mask, event_times, 1)

    maximum_off = int(off_counts.max(initial=0))
    for crossing_index in range(1, maximum_off + 1):
        mask = off_counts >= crossing_index
        rows, columns = np.nonzero(mask)
        targets = interval_reference[rows, columns] - crossing_index * threshold_off[rows, columns]
        fractions = (targets - start[rows, columns]) / (end[rows, columns] - start[rows, columns])
        event_times = time_start + np.clip(fractions, 0.0, 1.0) * duration
        append_events(mask, event_times, -1)

    reference += on_counts * threshold_on
    reference -= off_counts * threshold_off

    if not time_parts:
        return empty_events(), reference

    event_times = np.concatenate(time_parts)
    events = np.empty(event_times.size, dtype=EVENT_DTYPE)
    events["t"] = quantize_timestamps_us(event_times, timestamp_resolution_us)
    events["x"] = np.concatenate(x_parts)
    events["y"] = np.concatenate(y_parts)
    events["p"] = np.concatenate(polarity_parts)
    order = np.lexsort((events["p"], events["x"], events["y"], events["t"]))
    return events[order], reference
