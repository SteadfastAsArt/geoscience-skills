# Reading dispersion curves

The examples below continue from the model, periods and solvers in
[the skill entrypoint](../SKILL.md). `DispersionCurve` contains `period`,
`velocity`, `mode`, `wave`, and `type`; use its fields explicitly.

## Phase and group velocity

Phase velocity c tracks a constant phase. Group velocity U tracks a wave
packet in the corresponding mode. From `k = omega / c` and `U = d omega / dk`,
when c is a function of period T:

```text
U = c / (1 + (T/c) * dc/dT)
```

This is not `c + T*dc/dT`. Differentiation amplifies noise; prefer disba's
`GroupDispersion` for forward modelling. The helper below is useful for
checking a smooth, densely sampled phase curve, away from its endpoints or
mode discontinuities:

```python
import numpy as np

def group_from_phase(period_s, phase_km_s):
    period_s = np.asarray(period_s, dtype=float)
    phase_km_s = np.asarray(phase_km_s, dtype=float)
    if (period_s.ndim != 1 or period_s.size < 3 or
            phase_km_s.shape != period_s.shape or
            not np.all(np.isfinite(period_s)) or
            not np.all(np.isfinite(phase_km_s)) or
            np.any(period_s <= 0) or np.any(phase_km_s <= 0) or
            np.any(np.diff(period_s) <= 0)):
        raise ValueError('Provide matching positive finite curves on increasing periods')
    dc_dt = np.gradient(phase_km_s, period_s, edge_order=2)
    denominator = 1.0 + period_s * dc_dt / phase_km_s
    if np.any(denominator <= 0):
        raise ValueError('This curve does not give a positive finite group velocity')
    return phase_km_s / denominator
```

In normal dispersion c increases with period and U is lower than c. Neither
ordering is universal for every model and mode. A curve alone does not give
a unique geological interpretation.

## Higher modes

Fundamental mode is `mode=0`; positive integers select overtones. Higher
modes can have missing roots over part or all of the requested period range.
A returned partial or empty curve is not necessarily an exception.

```python
from disba import DispersionError

modes = {}
mode_errors = {}
for mode in range(3):
    try:
        curve = phase_solver(periods, mode=mode, wave='rayleigh')
    except DispersionError as error:
        mode_errors[mode] = str(error)
    else:
        modes[mode] = curve
        print(f'Mode {mode}: {curve.period.size} of {periods.size} periods')
```

Record root-search failures; they can reflect the model or numerical search,
not only physical absence of a mode. Input errors must propagate. For plots
or misfits, preserve `curve.period` and never align a partial curve by index
to the full requested period axis. Modal sensitivity and penetration depend
on the model and frequency; higher modes are not universally shallower.

## Plot returned axes

Continue from `rayleigh` and `love` in the entrypoint:

```python
import matplotlib.pyplot as plt

fig, ax = plt.subplots()
ax.plot(rayleigh.period, rayleigh.velocity, label='Rayleigh')
ax.plot(love.period, love.velocity, label='Love')
ax.set(xlabel='Period (s)', ylabel='Phase velocity (km/s)')
ax.legend()
```

Rayleigh motion is coupled P-SV; Love motion is transverse SH. In isotropic
layers, the Love problem depends on shear modulus (density times Vs squared),
density and thickness, not Vp. Do not interpret it as sensitive only to Vs.

## Frequency input

```python
import numpy as np

frequencies_hz = np.linspace(0.2, 10.0, 50)
period_order = np.argsort(1.0 / frequencies_hz)
periods_from_frequency = (1.0 / frequencies_hz)[period_order]
curve_from_frequency = phase_solver(periods_from_frequency, wave='rayleigh')
returned_frequency_hz = 1.0 / curve_from_frequency.period
```

Require finite positive input frequencies. Sort observation values and
uncertainties with the same `period_order`, then match them to returned
periods. Ascending frequency becomes descending period before sorting.
A wavelength (`c*T`) gives a scale, but sensitivity kernels provide a more
useful model-specific depth assessment than assigning a fixed fraction of
wavelength as a resolved depth.

## Sources

Checked **2026-09-14** against the official
[disba 0.7.0 result handling](https://github.com/keurfonluu/disba/blob/v0.7.0/disba/_dispersion.py)
and [CPS-derived phase/group solver](https://github.com/keurfonluu/disba/blob/v0.7.0/disba/_cps/_surf96.py).
The phase/group identity follows by differentiating `k = omega/c` above.
