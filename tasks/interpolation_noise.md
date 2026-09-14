# Task: Interpolation and Noise

## Owner

Algorithm member B.

## Owned files

- `src/event_camera_simulator/interpolation.py`
- `src/event_camera_simulator/noise.py`
- Relevant focused tests if coordinated with the testing owner

## Priority order

1. Analytical crossing-time interpolation.
2. Timestamp quantization.
3. Fixed pixel-to-pixel threshold maps.
4. Leak events.
5. Hot pixels.

Items 4 and 5 may be deferred if the one-week deadline is at risk.

## Required constraints

- Do not scan at every timestamp-resolution interval.
- Multiple crossings receive distinct analytical times before quantization.
- Threshold mismatch is sampled once per pixel per sequence, not once per time step.
- Random behavior is reproducible from the configured seed.
- Do not modify the core pixel-model API.

## Acceptance criteria

- Crossing times match closed-form values.
- Quantization produces integer microseconds and is documented at ties.
- Invalid/non-crossing inputs raise actionable errors.
- Same seed produces identical maps/events.
- Fixed threshold maps remain unchanged during a sequence.

## Suggested agent prompt

> Read AGENTS.md, docs/INTERFACES.md, docs/MATHEMATICAL_MODEL.md, and tasks/interpolation_noise.md. Implement tasks in priority order without altering public contracts. Verify analytical cases and seeded stochastic behavior, then report test results and any deferred optional work.
