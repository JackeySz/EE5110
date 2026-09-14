# Canonical Interface Contract

This document is the single source of truth for public APIs. Implementation details may change without coordination; signatures, units, shapes, field meanings, and documented exceptions may not.

## Shared arrays and units

### Raw or grayscale frame sequence

```text
shape: (T, H, W) or (T, H, W, C) at the video/preprocessing boundary
dtype: uint8, uint16, float32, or float64
```

### Log-intensity frame sequence

```text
shape: (T, H, W)
dtype: float32 or float64
all entries finite
```

### Frame timestamps

```text
shape: (T,)
dtype: float64
unit: seconds
strictly increasing
```

### Event array

The canonical dtype is `event_camera_simulator.types.EVENT_DTYPE`:

```python
np.dtype([
    ("t", np.int64),
    ("x", np.uint16),
    ("y", np.uint16),
    ("p", np.int8),
])
```

`t` is integer microseconds. Events are sorted by `(t, y, x, p)` for deterministic output. Polarity is exactly `+1` for ON or `-1` for OFF.

## `config.py`

```python
def load_config(path: Path) -> AppConfig
```

Loads YAML and returns validated nested dataclasses. Unknown keys and invalid values raise `ConfigError`.

## `preprocessing.py`

```python
def to_grayscale(frames: np.ndarray) -> np.ndarray
```

Accepts `(T,H,W)` or `(T,H,W,3)` frames and returns `(T,H,W)` floating-point grayscale frames. The selected RGB/BGR convention must match `video_io.py` and be documented in code.

```python
def normalize_intensity(frames: np.ndarray, input_max: Optional[float] = None) -> np.ndarray
```

Returns finite values in `[0,1]`. Negative values, non-finite values, invalid maxima, and unsupported dtypes raise `ValueError`.

```python
def to_log_intensity(frames: np.ndarray, epsilon: float) -> np.ndarray
```

Returns `log(frames + epsilon)`. Input must already be normalized, finite, and nonnegative. `epsilon` must be positive.

## `interpolation.py`

```python
def interpolate_crossing_time(
    start_log_intensity: float,
    end_log_intensity: float,
    crossing_level: float,
    start_time: float,
    end_time: float,
) -> float
```

Returns the analytical linear crossing time in seconds. Raises `ValueError` if times are invalid, the interval is flat, or the crossing level lies outside the closed intensity interval.

```python
def quantize_timestamps_us(times_seconds: np.ndarray, resolution_us: int) -> np.ndarray
```

Returns `int64` microseconds rounded to the nearest resolution unit. The implementation must document and test tie handling.

## `pixel_model.py`

```python
def detect_pixel_crossings(
    start_log_intensity: float,
    end_log_intensity: float,
    start_time: float,
    end_time: float,
    reference_log_intensity: float,
    threshold_on: float,
    threshold_off: float,
) -> PixelCrossingResult
```

Returns all ideal events for a single monotonic, linearly interpolated frame interval and the updated reference. Multiple threshold crossings produce distinct timestamps. The reference changes by exactly one applicable threshold per event.

## `noise.py`

```python
class NoiseModel(Protocol):
    def initialize(self, height: int, width: int) -> None: ...
    def threshold_maps(self) -> Tuple[np.ndarray, np.ndarray]: ...
    def generate_background_events(
        self, start_time: float, end_time: float
    ) -> np.ndarray: ...
```

Threshold mismatch maps are sampled once during initialization and remain fixed for a sequence. Stochastic implementations accept a seed and are reproducible.

## `simulator.py`

```python
class EventCameraSimulator:
    def reset(self, initial_log_frame: np.ndarray) -> None: ...
    def process_interval(
        self,
        previous_log_frame: np.ndarray,
        current_log_frame: np.ndarray,
        previous_time: float,
        current_time: float,
    ) -> np.ndarray: ...
    def simulate(
        self, log_frames: np.ndarray, timestamps: np.ndarray
    ) -> np.ndarray: ...
```

`reset()` establishes the reference state. `process_interval()` requires prior initialization. `simulate()` resets state and returns one canonical, deterministically sorted event array.

## `video_io.py`

```python
def read_video(path: Path, fps_override: Optional[float] = None) -> VideoData
```

Returns decoded BGR frames, strictly increasing timestamps in seconds, source/effective FPS, width, and height. Invalid files and FPS values raise `VideoIOError`.

## `event_io.py`

```python
def save_events_npz(path: Path, events: np.ndarray) -> None
def load_events_npz(path: Path) -> np.ndarray
def save_events_csv(path: Path, events: np.ndarray) -> None
```

All functions validate the canonical dtype and event values. Loading rejects malformed or incompatible data.

## `event_frames.py`

```python
def accumulate_event_frame(
    events: np.ndarray,
    start_time_us: int,
    end_time_us: int,
    height: int,
    width: int,
) -> EventFrame
```

The interval is half-open: `[start_time_us, end_time_us)`. Returns separate nonnegative ON and OFF count arrays with shape `(H,W)`.

## `visualization.py`

```python
def render_event_frame(event_frame: EventFrame) -> np.ndarray
def overlay_events(input_frame: np.ndarray, event_image: np.ndarray, alpha: float) -> np.ndarray
def create_demo_video(...) -> None
```

Rendered images use BGR `uint8` for OpenCV compatibility. ON is red and OFF is blue unless configuration explicitly overrides colors.

## `metrics.py`

```python
def calculate_metrics(events: np.ndarray, duration_seconds: float, processing_seconds: float) -> SimulationMetrics
```

Returns total, ON and OFF counts, event rate, processing time, and optional processing FPS when frame count is supplied.
