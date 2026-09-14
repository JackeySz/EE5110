# Test Instructions

- Read `docs/INTERFACES.md` and `docs/TESTING_STRATEGY.md`.
- Calculate expected results independently from production implementations.
- Prefer small exact fixtures over large opaque samples.
- Never call a production helper to calculate the expected value for the same behavior.
- Separate deterministic tests from statistical tests.
- Use explicit seeds and justified statistical tolerances.
- Test public behavior, canonical dtypes, units, coordinates, boundaries, and error messages.
- Do not change production algorithms unless the human task explicitly expands scope.
- Do not weaken, delete, or broadly skip a failing test to obtain a green suite.
