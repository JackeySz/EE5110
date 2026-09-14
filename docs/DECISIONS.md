# Design Decisions

## D001: Canonical time units

- Internal frame and analytical event times use seconds as `float64`.
- Serialized event times use microseconds as `int64`.

Status: frozen.

## D002: Coordinate convention

- Arrays are indexed `[y, x]`.
- Events store fields `(x, y)`.

Status: frozen.

## D003: Event ordering

Events are deterministically sorted by `(t, y, x, p)` after timestamp quantization.

Status: frozen.

## D004: Baseline interpolation

Use analytical linear interpolation in log-intensity space. Do not scan every microsecond in Python.

Status: frozen for the baseline.

## D005: Unimplemented scaffold behavior

Unimplemented algorithms raise `NotImplementedError` only when invoked. Package import, configuration validation, and CLI help must remain functional.

Status: frozen.

## Proposing a change

Append a numbered decision containing context, alternatives, affected owners, migration plan, and approval. Do not edit historical decisions to hide changes.
