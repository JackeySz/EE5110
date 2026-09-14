"""Canonical event serialization interfaces owned by the integration member."""

from pathlib import Path

import numpy as np


def save_events_npz(path: Path, events: np.ndarray) -> None:
    """Save a validated canonical event array as compressed NPZ."""

    raise NotImplementedError("assigned to Integration: implement NPZ event writing")


def load_events_npz(path: Path) -> np.ndarray:
    """Load and validate a canonical event array from NPZ."""

    raise NotImplementedError("assigned to Integration: implement NPZ event reading")


def save_events_csv(path: Path, events: np.ndarray) -> None:
    """Save a validated canonical event array as CSV for inspection."""

    raise NotImplementedError("assigned to Integration: implement CSV event writing")
