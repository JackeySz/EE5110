"""Tests that must pass before feature implementations land."""

import numpy as np
import pytest

from event_camera_simulator.cli import build_parser
from event_camera_simulator.config import ConfigError, config_from_mapping
from event_camera_simulator.simulator import EventCameraSimulator
from event_camera_simulator.types import EVENT_DTYPE, empty_events, validate_events


def test_event_dtype_is_frozen() -> None:
    assert EVENT_DTYPE.names == ("t", "x", "y", "p")
    assert EVENT_DTYPE["t"] == np.dtype(np.int64)
    assert EVENT_DTYPE["x"] == np.dtype(np.uint16)
    assert EVENT_DTYPE["y"] == np.dtype(np.uint16)
    assert EVENT_DTYPE["p"] == np.dtype(np.int8)


def test_empty_events_are_canonical() -> None:
    events = empty_events()
    assert events.shape == (0,)
    validate_events(events)


def test_event_validation_rejects_float_matrix() -> None:
    with pytest.raises((TypeError, ValueError)):
        validate_events(np.empty((0, 4), dtype=np.float64))


def test_default_mapping_is_valid() -> None:
    config = config_from_mapping({})
    assert config.sensor.threshold_on == pytest.approx(0.3)
    assert config.sensor.timestamp_resolution_us == 1
    assert not config.noise.enabled


def test_unknown_config_key_is_rejected() -> None:
    with pytest.raises(ConfigError, match="unknown keys"):
        config_from_mapping({"sensor": {"typo_threshold": 0.2}})


def test_invalid_threshold_is_rejected() -> None:
    with pytest.raises(ConfigError, match="thresholds must be positive"):
        config_from_mapping({"sensor": {"threshold_on": 0.0}})


def test_simulator_reset_copies_state() -> None:
    config = config_from_mapping({})
    simulator = EventCameraSimulator(config.sensor, config.noise)
    frame = np.ones((2, 3), dtype=np.float64)
    simulator.reset(frame)
    frame[:] = 99
    assert simulator.is_initialized


def test_process_interval_requires_reset() -> None:
    config = config_from_mapping({})
    simulator = EventCameraSimulator(config.sensor, config.noise)
    frame = np.zeros((2, 2), dtype=np.float64)
    with pytest.raises(RuntimeError, match="reset"):
        simulator.process_interval(frame, frame, 0.0, 1.0)


def test_cli_contract_contains_expected_commands() -> None:
    help_text = build_parser().format_help()
    assert "simulate" in help_text
    assert "validate-config" in help_text
