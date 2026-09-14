# Preparing layered velocity models

Use this reference when converting field-derived arrays or running parameter
studies. disba uses thickness in km, Vp and Vs in km/s, density in g/cm³,
and period in seconds. Convert m, m/s, and kg/m³ by dividing by 1000.

## Solid-model validation

This helper deliberately covers **solid isotropic layers**. It rejects water
layers, missing observations and malformed shapes rather than allowing them
to reach a numerical root search. A fluid top layer needs a separate model
and wave-specific boundary-condition check.

```python
import numpy as np

def validate_solid_model(thickness, vp, vs, rho):
    arrays = tuple(np.asarray(a, dtype=float) for a in (thickness, vp, vs, rho))
    if any(a.ndim != 1 for a in arrays):
        raise ValueError('Model properties must be one-dimensional arrays')
    if not arrays[0].size or any(a.size != arrays[0].size for a in arrays):
        raise ValueError('Model properties must have the same nonzero length')
    if any(not np.all(np.isfinite(a)) for a in arrays):
        raise ValueError('Model properties must be finite')
    thickness, vp, vs, rho = arrays
    if np.any(thickness[:-1] <= 0) or thickness[-1] != 0:
        raise ValueError('Positive layer thicknesses must end with a zero half-space')
    if np.any(vp <= 0) or np.any(vs <= 0) or np.any(rho <= 0):
        raise ValueError('Solid velocities and density must be positive')
    if np.any(vp**2 <= (4.0 / 3.0) * vs**2):
        raise ValueError('Solid elastic bulk modulus must be positive')
    return arrays
```

The zero final thickness records the half-space convention; disba does not
interpret a nonzero final thickness as a finite bottom boundary. Positive
bulk and shear moduli imply `-1 < Poisson ratio < 0.5`. Ratios outside a local
empirical range warrant investigation but are not automatically unstable.

## Layer table

Continue after defining `validate_solid_model`. Transpose row-per-layer input
exactly once, then pass the four columns to the solver:

```python
from disba import PhaseDispersion

model = np.array([
    [0.5, 1.5, 0.8, 1.8],
    [1.0, 2.5, 1.4, 2.0],
    [0.0, 4.0, 2.3, 2.3],
])  # thickness, Vp, Vs, density
thickness, vp, vs, rho = validate_solid_model(*model.T)
phase_solver = PhaseDispersion(thickness, vp, vs, rho)
```

`*model` passes rows as arguments. Likewise, `*zip(thickness, vp, vs, rho)`
passes layer rows: neither is the four property columns the constructor needs.

## Forward function

Continue after defining `validate_solid_model`. Provide periods and every
model property explicitly so an outer-scope period axis or density fit cannot
silently change an inversion's forward response.

```python
from disba import PhaseDispersion

def forward_model(thickness, vp, vs, rho, periods, mode=0, wave='rayleigh'):
    model = validate_solid_model(thickness, vp, vs, rho)
    periods = np.asarray(periods, dtype=float)
    if (periods.ndim != 1 or not periods.size or
            not np.all(np.isfinite(periods)) or np.any(periods <= 0) or
            np.any(np.diff(periods) <= 0)):
        raise ValueError('Periods must be finite, positive and strictly increasing')
    if not isinstance(mode, (int, np.integer)) or mode < 0:
        raise ValueError('Mode must be a nonnegative integer')
    if wave not in ('rayleigh', 'love'):
        raise ValueError('Wave must be rayleigh or love')
    return PhaseDispersion(*model)(periods, mode=mode, wave=wave)
```

Compare predictions and observations only at matching returned periods and
modes. Report unavailable predictions explicitly; dropping them from a misfit
without a declared rule can bias an inversion.

## Density estimates

If density is not measured, select and label a calibrated empirical estimate.
Gardner's standard coefficient `0.31` uses **m/s** to return **g/cm³**. The
following standalone function accepts the **km/s** used by disba and converts
before applying it:

```python
import numpy as np

def gardner_density(vp_km_s):
    vp_km_s = np.asarray(vp_km_s, dtype=float)
    if not np.all(np.isfinite(vp_km_s)) or np.any(vp_km_s <= 0):
        raise ValueError('Vp must be finite and positive')
    return 0.31 * (1000.0 * vp_km_s)**0.25
```

For Vp = 3 km/s this gives approximately 2.294 g/cm³, not 0.408 g/cm³.
The linear expression `0.32*vp + 0.77` is not Gardner's power law. Do not use
any density or Vp/Vs relationship outside its calibration conditions without
reporting that modelling assumption. Dispersion depends on density contrasts
as well as shear velocity.

For a velocity gradient, refine layers until curves converge at the periods
of interest. Constant-property layers are solved analytically; an arbitrary
number of layers per wavelength is not a universal accuracy requirement.

## Sources

Checked **2026-09-14**:

- [disba 0.7.0 model implementation](https://github.com/keurfonluu/disba/blob/v0.7.0/disba/_base.py)
- [disba 0.7.0 dispersion implementation](https://github.com/keurfonluu/disba/blob/v0.7.0/disba/_dispersion.py)
- [Gardner units in Bruges 0.5.4](https://github.com/agilescientific/bruges/blob/v0.5.4/bruges/petrophysics/petrophysics.py)
