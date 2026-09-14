# Task: Tests and Experiments

## Owner

Testing member.

## Owned files

- `tests/`
- `scripts/generate_test_video.py`
- `scripts/analyze_thresholds.py`
- `src/event_camera_simulator/metrics.py`
- `docs/TESTING_STRATEGY.md`

## Required work

- Turn interface expectations into executable pytest tests.
- Independently calculate analytical expected values.
- Cover constant, bright ramp, dark ramp, multiple crossing, reference persistence, reversal, asymmetric threshold, timestamp, coordinate, and sorting behavior.
- Add deterministic seed and statistical noise tests when noise implementations land.
- Create a small synthetic moving-bar video fixture.
- Produce threshold-sensitivity and performance reports after integration.

## Restrictions

- Do not copy production formulas into helpers that calculate expected results.
- Do not modify algorithm code to make tests pass.
- Do not weaken tolerances without mathematical justification.
- Mark tests for unimplemented interfaces as skipped with a specific reason; remove skips when the owning feature merges.

## Acceptance criteria

- Scaffold tests pass before feature work.
- Each merged algorithm feature has meaningful behavior tests.
- Failures include minimal reproducible inputs.
- Test commands and platform-dependent benchmarks are documented.

## Suggested agent prompt

> Read AGENTS.md, tests/AGENTS.md, docs/INTERFACES.md, docs/TESTING_STRATEGY.md, and tasks/testing.md. Implement tests from independent analytical expectations. Do not edit production algorithms or weaken failures. Run the suite and report passes, skips, and defects separately.
