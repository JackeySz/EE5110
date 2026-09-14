# Task: I/O and Integration

## Owner

Integration member and recommended team lead.

## Owned files

- `src/event_camera_simulator/config.py`
- `src/event_camera_simulator/video_io.py`
- `src/event_camera_simulator/event_io.py`
- `src/event_camera_simulator/simulator.py`
- `src/event_camera_simulator/cli.py`
- `configs/`
- `README.md`

## Required work

- Maintain strict configuration validation.
- Read video frames, dimensions, FPS, and timestamps.
- Compose preprocessing, simulation, output, and optional visualization without embedding their algorithms.
- Save and load canonical NPZ; optionally export CSV.
- Maintain actionable CLI errors and README commands.

## Restrictions

- Do not reimplement event mathematics in the orchestration layer.
- Do not silently coerce malformed event arrays.
- Do not catch `NotImplementedError` and report success.
- Preserve streaming-friendly `process_interval()` boundaries.

## Acceptance criteria

- CLI help and config validation work before algorithms land.
- Valid configuration round-trips to dataclasses.
- NPZ round-trip preserves dtype and values once event I/O is implemented.
- End-to-end invocation fails clearly while required algorithms remain unimplemented and succeeds after they merge.

## Suggested agent prompt

> Read AGENTS.md, docs/ARCHITECTURE.md, docs/INTERFACES.md, and tasks/io_integration.md. Implement only orchestration and I/O boundaries. Preserve algorithm placeholders, validate inputs strictly, run integration checks, and report any required interface proposal rather than changing contracts silently.
