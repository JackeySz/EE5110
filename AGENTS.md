# Repository Instructions for Coding Agents

This repository is a one-week team project scaffold for an event camera simulator. Humans review and own every change. Complete only the assigned task and do not silently expand scope.

## Required reading

Before editing, read:

1. `docs/ARCHITECTURE.md`
2. `docs/INTERFACES.md`
3. `docs/DECISIONS.md`
4. The relevant file under `tasks/`
5. The nearest nested `AGENTS.md`

## Authority and contracts

- `docs/INTERFACES.md` is the canonical public API contract.
- `docs/DECISIONS.md` records frozen cross-module decisions.
- A task file defines the files and behavior owned by one contributor.
- Do not change public signatures, event dtypes, units, array shapes, or coordinate conventions without an explicit cross-team decision.
- If an interface is insufficient, document a proposal in `docs/DECISIONS.md` and stop at the boundary instead of inventing an incompatible API.

## Frozen conventions

- Python 3.9+.
- Frames are NumPy arrays with shape `(T, H, W)`.
- A pixel is accessed as `frames[t, y, x]`; events store `(x, y)`.
- Internal time is `float64` seconds.
- Serialized event time is `int64` microseconds.
- Polarity is `int8` and is exactly `+1` or `-1`.
- `EVENT_DTYPE` in `types.py` is authoritative.
- Random behavior must use an injected or explicitly seeded NumPy generator.
- Public code must not depend on notebooks.

## Implementation rules

- Keep core mathematical logic independent from video I/O and visualization.
- Do not duplicate algorithms across modules.
- Do not replace explicit `NotImplementedError` placeholders outside the assigned scope.
- Validate inputs at public boundaries and raise actionable errors.
- Preserve deterministic behavior in ideal mode.
- Do not add GUI, GPU, 3D simulation, SLAM, optical flow, or neural-network scope during the baseline week.
- Never weaken tests merely to make an implementation pass.

## Verification

Run checks relevant to the change:

```bash
pytest
ruff check .
mypy src
```

For algorithm changes, add independently derived analytical tests. For stochastic behavior, use statistical assertions and deterministic seed tests.

## Completion report

Report:

- files changed;
- behavior implemented;
- tests run and results;
- assumptions introduced;
- unresolved issues or proposed contract changes.
