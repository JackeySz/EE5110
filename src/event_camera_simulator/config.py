"""Strict application configuration."""

from collections.abc import Mapping
from dataclasses import dataclass, fields
from pathlib import Path
from typing import Any, Optional, TypeVar


class ConfigError(ValueError):
    """Raised for malformed or inconsistent application configuration."""


@dataclass(frozen=True)
class InputConfig:
    fps_override: Optional[float] = None


@dataclass(frozen=True)
class SensorConfig:
    threshold_on: float = 0.30
    threshold_off: float = 0.30
    timestamp_resolution_us: int = 1
    log_epsilon: float = 1e-3


@dataclass(frozen=True)
class NoiseConfig:
    enabled: bool = False
    threshold_std: float = 0.03
    leak_rate_hz: float = 0.1
    hot_pixel_ratio: float = 0.0
    hot_pixel_rate_hz: float = 50.0
    seed: int = 42


@dataclass(frozen=True)
class VisualizationConfig:
    accumulation_us: int = 10_000
    overlay_input: bool = True
    positive_color_bgr: tuple[int, int, int] = (0, 0, 255)
    negative_color_bgr: tuple[int, int, int] = (255, 0, 0)


@dataclass(frozen=True)
class AppConfig:
    input: InputConfig = InputConfig()
    sensor: SensorConfig = SensorConfig()
    noise: NoiseConfig = NoiseConfig()
    visualization: VisualizationConfig = VisualizationConfig()


T = TypeVar("T")


def _strict_dataclass(cls: type[T], values: Mapping[str, Any], section: str) -> T:
    allowed = {item.name for item in fields(cls)}  # type: ignore[arg-type]
    unknown = set(values) - allowed
    if unknown:
        raise ConfigError(f"unknown keys in {section}: {sorted(unknown)}")
    try:
        return cls(**dict(values))
    except TypeError as exc:
        raise ConfigError(f"invalid {section} configuration: {exc}") from exc


def validate_config(config: AppConfig) -> None:
    """Validate value ranges and cross-field invariants."""

    if config.input.fps_override is not None and config.input.fps_override <= 0:
        raise ConfigError("input.fps_override must be positive")
    if config.sensor.threshold_on <= 0 or config.sensor.threshold_off <= 0:
        raise ConfigError("sensor thresholds must be positive")
    if config.sensor.timestamp_resolution_us <= 0:
        raise ConfigError("sensor.timestamp_resolution_us must be positive")
    if config.sensor.log_epsilon <= 0:
        raise ConfigError("sensor.log_epsilon must be positive")
    if config.noise.threshold_std < 0:
        raise ConfigError("noise.threshold_std cannot be negative")
    if config.noise.leak_rate_hz < 0 or config.noise.hot_pixel_rate_hz < 0:
        raise ConfigError("noise event rates cannot be negative")
    if not 0 <= config.noise.hot_pixel_ratio <= 1:
        raise ConfigError("noise.hot_pixel_ratio must be in [0, 1]")
    if config.visualization.accumulation_us <= 0:
        raise ConfigError("visualization.accumulation_us must be positive")
    for name, color in (
        ("positive_color_bgr", config.visualization.positive_color_bgr),
        ("negative_color_bgr", config.visualization.negative_color_bgr),
    ):
        if len(color) != 3 or any(not 0 <= value <= 255 for value in color):
            raise ConfigError(f"visualization.{name} must contain three values in [0,255]")


def config_from_mapping(data: Mapping[str, Any]) -> AppConfig:
    """Create an application config from a parsed mapping."""

    allowed_sections = {"input", "sensor", "noise", "visualization"}
    unknown = set(data) - allowed_sections
    if unknown:
        raise ConfigError(f"unknown configuration sections: {sorted(unknown)}")

    def section(name: str) -> Mapping[str, Any]:
        value = data.get(name, {})
        if not isinstance(value, Mapping):
            raise ConfigError(f"{name} must be a mapping")
        return value

    visual_values: dict[str, Any] = dict(section("visualization"))
    for color_name in ("positive_color_bgr", "negative_color_bgr"):
        if color_name in visual_values:
            visual_values[color_name] = tuple(visual_values[color_name])

    config = AppConfig(
        input=_strict_dataclass(InputConfig, section("input"), "input"),
        sensor=_strict_dataclass(SensorConfig, section("sensor"), "sensor"),
        noise=_strict_dataclass(NoiseConfig, section("noise"), "noise"),
        visualization=_strict_dataclass(
            VisualizationConfig, visual_values, "visualization"
        ),
    )
    validate_config(config)
    return config


def load_config(path: Path) -> AppConfig:
    """Load and validate YAML configuration from ``path``."""

    try:
        import yaml
    except ImportError as exc:  # pragma: no cover - environment guidance
        raise ConfigError("PyYAML is required; install the project dependencies") from exc

    try:
        with Path(path).open("r", encoding="utf-8") as stream:
            raw = yaml.safe_load(stream)
    except OSError as exc:
        raise ConfigError(f"cannot read configuration {path}: {exc}") from exc
    except yaml.YAMLError as exc:
        raise ConfigError(f"invalid YAML in {path}: {exc}") from exc

    if raw is None:
        raw = {}
    if not isinstance(raw, Mapping):
        raise ConfigError("configuration root must be a mapping")
    return config_from_mapping(raw)
