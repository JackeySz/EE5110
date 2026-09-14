# Task: Event Visualization

## Owner

Visualization and presentation member.

## Owned files

- `src/event_camera_simulator/event_frames.py`
- `src/event_camera_simulator/visualization.py`
- `scripts/create_demo.py`
- Presentation assets under `outputs/figures/` and `outputs/videos/` (not committed when large)

## Required work

- Accumulate events over configurable half-open time windows.
- Build separate ON/OFF count images.
- Render ON as red and OFF as blue in OpenCV BGR output.
- Overlay events on source frames.
- Create a playable demonstration video with matching FPS and dimensions.
- Add time, threshold, window length, and event-count annotations if schedule allows.

## Restrictions

- Do not generate or change events in visualization code.
- Do not change event dtype or time units.
- Do not infer image size from maximum event coordinate when source metadata is available.

## Acceptance criteria

- Empty windows render cleanly.
- Boundary timestamps obey `[start,end)`.
- Coordinates and colors are correct.
- Output frames are BGR `uint8` with source dimensions.
- Demonstration video opens and contains the expected number of frames.

## Suggested agent prompt

> Read AGENTS.md, docs/INTERFACES.md, tasks/visualization.md, and the nearest source instructions. Implement event accumulation and visualization only. Add focused tests for window boundaries, coordinates, colors, and output shape, then report generated artifacts and verification results.
