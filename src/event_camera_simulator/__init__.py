"""Public package surface for the event camera simulator scaffold."""

from .config import AppConfig, NoiseConfig, SensorConfig, VisualizationConfig
from .simulator import EventCameraSimulator
from .types import EVENT_DTYPE, EventFrame, SimulationMetrics, VideoData

__all__ = [
    "AppConfig",
    "EVENT_DTYPE",
    "EventCameraSimulator",
    "EventFrame",
    "NoiseConfig",
    "SensorConfig",
    "SimulationMetrics",
    "VideoData",
    "VisualizationConfig",
]

__version__ = "0.1.0"
