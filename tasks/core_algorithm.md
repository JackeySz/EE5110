# Task: Core Event Algorithm

## Owner

Algorithm member A.

## Read first

- `AGENTS.md`
- `docs/MATHEMATICAL_MODEL.md`
- `docs/INTERFACES.md`
- `src/event_camera_simulator/AGENTS.md`

## Owned files

- `src/event_camera_simulator/preprocessing.py`
- `src/event_camera_simulator/pixel_model.py`
- Relevant focused tests if coordinated with the testing owner

## Required implementation

- grayscale conversion;
- normalization and log-intensity conversion;
- ideal ON/OFF detection;
- persistent reference intensity;
- multiple crossings within one interval;
- distinct crossing levels passed to the interpolation contract.

## Boundary

Do not implement video I/O, noise, visualization, CLI behavior, or file serialization. Do not change shared types or public signatures.

## Acceptance criteria

- Constant signal: zero events.
- Bright and dark ramps match analytical counts and polarities.
- Multiple crossings update the reference once per event.
- Reversal below the opposite threshold causes no false event.
- Input validation is documented and tested.
- Required checks pass.

## Suggested agent prompt

> Read the repository AGENTS.md, docs/INTERFACES.md, docs/MATHEMATICAL_MODEL.md, and tasks/core_algorithm.md. Implement the complete assigned scope without changing frozen interfaces. Add focused independently derived tests, run the required checks, and report assumptions and unresolved contract issues.
