# Mathematical Model

## Log-intensity assumption

For normalized nonnegative intensity `I`, define:

```text
L(x, y, t) = log(I(x, y, t) + epsilon)
```

Digital number is only treated as proportional to incident intensity under a documented approximation. The implementation must not claim radiometric calibration unless calibration is actually performed.

## Ideal event condition

Each pixel maintains a reference `L_ref` associated with its last threshold update.

```text
ON:  L(t) - L_ref >= C_on
OFF: L(t) - L_ref <= -C_off
```

After an event of polarity `p`, update the reference by one applicable threshold:

```text
ON:  L_ref <- L_ref + C_on
OFF: L_ref <- L_ref - C_off
```

Comparing only adjacent input frames is incorrect because the reference belongs to the event state, not necessarily the previous frame.

## Interpolation

The baseline assumes log intensity changes linearly between adjacent frames. For a crossing level `L_target`:

```text
t_event = t0 + (L_target - L0) / (L1 - L0) * (t1 - t0)
```

Distinct threshold crossings in the same frame interval must receive distinct analytical times before timestamp quantization.

## Noise assumptions

The baseline extension may include:

- fixed pixel-to-pixel threshold mismatch;
- spontaneous ON leak events;
- a small set of hot pixels.

Threshold mismatch is not resampled at every timestamp. Advanced intensity-dependent bandwidth and temporal noise are outside the one-week baseline unless all required work is already complete.
