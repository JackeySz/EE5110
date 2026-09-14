# Testing Strategy

## Principles

- Test public observable behavior.
- Derive expected values analytically and independently from production code.
- Keep deterministic and stochastic tests separate.
- Use tiny arrays for unit tests and generated videos for integration tests.
- A printed demo is not a test; assertions are required.

## Required deterministic cases

1. Constant intensity produces zero ideal events.
2. A monotonic bright ramp produces the analytically expected ON events.
3. A monotonic dark ramp produces the analytically expected OFF events.
4. One interval crossing multiple thresholds produces multiple distinct event times.
5. Reference state persists across frame boundaries.
6. Reversal below the opposite threshold produces no false event.
7. ON and OFF thresholds may differ.
8. Timestamp quantization follows the documented rounding rule.
9. Coordinates use `(x,y)` while arrays use `[y,x]`.
10. Event output is canonical, valid, and deterministically sorted.

## Required stochastic cases

- Same seed produces identical output.
- Threshold maps have plausible sample mean and standard deviation and remain positive.
- Threshold maps remain fixed throughout one simulated sequence.
- Leak-event counts are statistically consistent with their configured Poisson rate.
- Hot pixels fire in a constant scene while ordinary pixels remain quiet when other noise is disabled.

## Integration cases

- Generate and process a small moving-bar video.
- Leading and trailing edges have the expected dominant polarities.
- Save and reload NPZ without loss.
- Create an overlay video with matching frame dimensions and nonzero duration.

## Performance reporting

Benchmarks are reports, not hardware-independent pass/fail tests. Record platform, video size, input FPS, frame count, event count, wall time, processing FPS, and peak memory when available.
