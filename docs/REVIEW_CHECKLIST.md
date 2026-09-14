# Human Review Checklist

## Every pull request

- The change matches one assigned task and avoids unrelated edits.
- Public signatures, units, shapes, coordinates, and event dtype remain compatible.
- Error handling does not hide failed or unimplemented work.
- Tests check observable behavior and have independently derived expectations.
- Documentation describes every new assumption.
- AI-generated code has been read line by line and material AI use recorded.

## Mathematical changes

- The reference is tied to previous event updates, not merely the previous frame.
- Every threshold crossing generates exactly one reference update.
- Multiple crossings receive distinct analytical times before quantization.
- ON and OFF thresholds are applied with the correct sign.
- Constant ideal input produces no events.
- Units are consistent throughout every equation and implementation step.

## Noise changes

- Threshold mismatch is fixed per pixel for one sequence.
- Random state is explicit and reproducible.
- Statistical tests use enough samples and justified tolerances.
- Ideal mode remains deterministic and free of background events.

## I/O and visualization changes

- Loaded FPS and overridden FPS are distinguished and documented.
- NPZ round-trip preserves canonical dtype exactly.
- Event windows use `[start,end)` without double counting boundaries.
- Array `[y,x]` and event `(x,y)` conventions are not swapped.
- ON/OFF colors are verified in BGR order.
- Output video dimensions, FPS, duration, and playback are checked.
