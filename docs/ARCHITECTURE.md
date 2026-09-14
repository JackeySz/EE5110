# Architecture

## Objective

Convert a timestamped sequence of intensity frames into a temporally ordered event stream and provide stable boundaries for serialization, event-frame construction, visualization, and evaluation.

## Components

```text
VideoReader -> Preprocessor -> EventCameraSimulator -> EventArray
                                      |                  |
                                 NoiseModel              +-> EventWriter
                                                         +-> EventFrameBuilder
                                                         +-> Metrics
                                                                  |
                                                                  +-> Visualization
```

## Dependency direction

- `types.py` and `config.py` are foundational and must not import feature modules.
- Mathematical modules may import `types.py` and configuration dataclasses.
- `simulator.py` orchestrates mathematical modules but does not read or write videos.
- `video_io.py` owns media decoding and encoding boundaries.
- `event_io.py` owns event persistence.
- `event_frames.py` converts event streams into image representations.
- `visualization.py` consumes frames and event-frame representations.
- `cli.py` composes modules and contains no mathematical implementation.

Circular imports are prohibited.

## Baseline execution path

1. Load and validate YAML configuration.
2. Read video frames and frame timestamps.
3. Convert frames to normalized grayscale log intensity.
4. Initialize simulator state using the first frame.
5. Process every adjacent frame interval.
6. Merge ideal events and optional background-noise events.
7. Quantize and sort event timestamps.
8. Save events and optionally create an overlay video.

## State ownership

`EventCameraSimulator` owns the reference log-intensity array and noise-model state. Calling `reset()` replaces all sequence-specific state. Video I/O and visualization functions must remain stateless.

## Failure behavior

Public APIs validate shapes, dtypes, ranges, and monotonic timestamps. Unsupported or unimplemented algorithm paths raise clear exceptions rather than returning empty results that appear successful.
