"""Noise-model interfaces owned by algorithm member B."""

from typing import Protocol

import numpy as np


class NoiseModel(Protocol):
    """Structural protocol implemented by simulator noise models."""

    def initialize(self, height: int, width: int) -> None:
        """Initialize fixed per-sequence state."""

    def threshold_maps(self) -> tuple[np.ndarray, np.ndarray]:
        """Return fixed ON and OFF threshold maps."""

    def generate_background_events(
        self, start_time: float, end_time: float
    ) -> np.ndarray:
        """Return canonical background events for a half-open time interval."""


class ConfiguredNoiseModel:
    """Placeholder for the configured threshold/leak/hot-pixel model."""

    def initialize(self, height: int, width: int) -> None:
        raise NotImplementedError("assigned to Algorithm B: initialize noise state")

    def threshold_maps(self) -> tuple[np.ndarray, np.ndarray]:
        raise NotImplementedError("assigned to Algorithm B: implement threshold maps")

    def generate_background_events(
        self, start_time: float, end_time: float
    ) -> np.ndarray:
        raise NotImplementedError("assigned to Algorithm B: implement background noise")
