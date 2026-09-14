# Event Camera Simulator

Team scaffold for the EE5110/EE6110 Continuous Assessment project. The repository defines the architecture, public interfaces, ownership boundaries, and verification workflow. Core algorithms are intentionally left for the assigned team members.

## Project scope

The simulator converts a high-frame-rate video into an asynchronous event stream:

```text
video -> grayscale/log intensity -> event simulation -> (t, x, y, p)
                                               |-> event files
                                               |-> event frames
                                               |-> overlay video
                                               |-> metrics and figures
```

The one-week baseline includes video input, configuration, stable event types, algorithm extension points, event serialization, visualization extension points, tests, and documentation. The initial scaffold does not implement threshold crossing, sensor noise, or final visualization algorithms.

## Read this first

All contributors and coding agents must read these files before editing:

1. `AGENTS.md`
2. `docs/ARCHITECTURE.md`
3. `docs/INTERFACES.md`
4. The assigned file in `tasks/`
5. The nearest nested `AGENTS.md`

`docs/INTERFACES.md` is the canonical API contract. Do not change a public interface in one module without recording and coordinating the change through `docs/DECISIONS.md`.

## Ownership

| Role | Task file | Primary area |
|---|---|---|
| Algorithm A | `tasks/core_algorithm.md` | preprocessing and pixel model |
| Algorithm B | `tasks/interpolation_noise.md` | crossing time and noise |
| Testing | `tasks/testing.md` | independent tests and experiments |
| Integration | `tasks/io_integration.md` | video, configuration, CLI, serialization |
| Visualization | `tasks/visualization.md` | event frames, overlays, demo video |

## Environment setup

Python 3.9 or newer is supported.

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -e '.[dev,video]'
```

## Commands

Check that the package and CLI are installed:

```bash
event-sim --help
event-sim validate-config --config configs/ideal.yaml
```

Run the scaffold tests:

```bash
pytest
ruff check .
mypy src
```

After the algorithm modules are implemented, the intended command is:

```bash
event-sim simulate \
  --input data/input/sample.mp4 \
  --config configs/ideal.yaml \
  --events outputs/events/sample.npz \
  --video outputs/videos/sample_overlay.mp4
```

Until then, `simulate` fails with a clear `NotImplementedError`; package imports, configuration validation, and interface-level smoke tests still work.

## Data conventions

- Frame arrays: `(T, H, W)` in row-major order.
- Frame access: `frames[t, y, x]`.
- Event coordinates: `(x, y)`.
- Internal frame timestamps: `float64` seconds.
- Serialized event timestamps: `int64` microseconds.
- Event polarity: `int8`, exactly `+1` or `-1`.
- Primary event format: compressed NumPy `.npz`; CSV is for inspection.

## Git workflow when the repository is uploaded

Create one branch per role:

```text
feature/core-pixel-model
feature/interpolation-noise
feature/tests
feature/io-integration
feature/visualization
```

Use pull requests. Every PR should stay inside its task scope, include meaningful tests, and pass CI. Human reviewers remain responsible for mathematical correctness and all AI-generated code.

## AI-use requirement

The course requires an AI Use and Review Report when AI tools are used. Record representative prompts, accepted changes, rejected suggestions, and human verification as work proceeds. A template is provided in `docs/AI_USE_REPORT_TEMPLATE.md`.
