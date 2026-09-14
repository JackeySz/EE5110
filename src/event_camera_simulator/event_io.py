"""Canonical event serialization interfaces owned by the integration member."""

import csv
from pathlib import Path

import numpy as np

from .types import EVENT_DTYPE, validate_events


def save_events_npz(path: Path, events: np.ndarray) -> None:
    """Save a validated canonical event array as compressed NPZ."""

    validate_events(events)
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    np.savez_compressed(target, events=events)


def load_events_npz(path: Path) -> np.ndarray:
    """Load and validate a canonical event array from NPZ."""

    source = Path(path)
    try:
        with np.load(source, allow_pickle=False) as data:
            if "events" not in data:
                raise ValueError("NPZ file must contain an 'events' array")
            events = data["events"]
    except OSError as exc:
        raise OSError(f"cannot read event file {source}: {exc}") from exc
    if events.dtype != EVENT_DTYPE:
        raise TypeError(f"events must use EVENT_DTYPE, got {events.dtype!r}")
    validate_events(events)
    return events


def save_events_csv(path: Path, events: np.ndarray) -> None:
    """Save a validated canonical event array as CSV for inspection."""

    validate_events(events)
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    with target.open("w", encoding="utf-8", newline="") as stream:
        writer = csv.writer(stream)
        writer.writerow(["t", "x", "y", "p"])
        for event in events:
            writer.writerow(
                [
                    int(event["t"]),
                    int(event["x"]),
                    int(event["y"]),
                    int(event["p"]),
                ]
            )
