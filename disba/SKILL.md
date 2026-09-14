---
name: disba
description: |
  Compute Rayleigh and Love wave phase/group dispersion and sensitivity kernels
  for one-dimensional isotropic layered Earth models. Use when forward modelling
  velocity profiles, comparing layered models, or preparing numerical derivatives
  for a separately defined inversion. Does not extract observed dispersion from
  waveforms or perform tomography.
license: MIT
metadata:
  version: "1.0.2"
  author: Geoscience Skills
  tags: '["Surface Waves", "Dispersion", "Rayleigh", "Love", "Seismology", "Disba", "Phase Velocity", "Group Velocity"]'
  dependencies: '["disba>=0.7.0", "numpy", "numba"]'
  complements: '["obspy", "segyio"]'
  workflow_role: analysis
  skill_type: domain
---

# disba: layered surface-wave dispersion

Use disba for 1D isotropic layered-model dispersion and sensitivity kernels.
It is a forward solver; extracting observed dispersion from raw waveforms or
performing tomography requires separate processing and inversion design.

## Model and period conventions

- Supply **four equal-length one-dimensional arrays**: thickness in **km**,
  Vp/Vs in **km/s**, and density in **g/cm³**. A row-per-layer table must be
  transposed once: `PhaseDispersion(*model.T)`.
- Do not use `*zip(thickness, vp, vs, rho)`: with four layers it silently
  interchanges properties, and other layer counts give the wrong arguments.
- Treat the last layer as the half-space and write its thickness as `0.0`.
  Other layers have positive thickness. The final thickness is not a finite
  bottom boundary, even if a nonzero value is accepted by the library.
- Use finite positive periods in **increasing order**. Density must be
  positive; for the solid models below require `vs > 0` and
  `vp**2 > (4/3) * vs**2`. Preserve measured units and model provenance.

## Phase and group velocity

This complete example uses a solid layered model. The first call may take
longer while Numba compiles the solver.

```python
import numpy as np
from disba import PhaseDispersion, GroupDispersion

thickness = np.array([0.5, 1.0, 2.0, 0.0])  # km
vp = np.array([1.5, 2.5, 4.0, 6.0])          # km/s
vs = np.array([0.8, 1.4, 2.3, 3.5])          # km/s
rho = np.array([1.8, 2.0, 2.3, 2.6])         # g/cm³
periods = np.linspace(0.1, 5.0, 50)          # s, increasing

phase_solver = PhaseDispersion(thickness, vp, vs, rho)
group_solver = GroupDispersion(thickness, vp, vs, rho)
rayleigh = phase_solver(periods, mode=0, wave='rayleigh')
love = phase_solver(periods, mode=0, wave='love')
group = group_solver(periods, mode=0, wave='rayleigh')
period_s, phase_km_s = rayleigh.period, rayleigh.velocity
```

Each result is a `DispersionCurve` named tuple, not a velocity array.
Use **`result.period` and `result.velocity` together**: unavailable roots may
be omitted, especially for higher modes. `len(result)` counts tuple fields,
not computed periods; use `result.period.size`.

Read [dispersion curves](references/dispersion_curves.md) for plotting,
phase/group conversion, mode tracking and frequency conversion. Love waves
depend on Vs, density and layer thickness in an isotropic model, while Vp
does not enter the SH problem. Modal depth sensitivity is model dependent.

## Sensitivity kernels

Continue from the model above. The call takes a scalar period as `t` or its
first positional argument; `period=` is not a supported keyword.

```python
from disba import PhaseSensitivity

sensitivity = PhaseSensitivity(thickness, vp, vs, rho)
kernel_vs = sensitivity(1.0, mode=0, wave='rayleigh', parameter='velocity_s')
depth_km, dc_dvs = kernel_vs.depth, kernel_vs.kernel
```

Other parameters are `velocity_p`, `density`, and `thickness`. These are
numerical derivatives in the model's units. Check a kernel against a small
finite perturbation before using it in an inverse problem; one kernel does
not establish unique depth resolution.

## Prepare models for parameter studies

Read [velocity model preparation](references/velocity_models.md) for shape,
unit and physical checks, table transposition, and an explicit forward-model
function. Supply density and Vp estimates deliberately; do not silently turn
a Vs profile into an uncalibrated density model. The solid-model validator in
that reference does not cover water layers; fluid-layer and Love-wave
boundary conditions require separate treatment.

For incomplete curves, record the mode, wave type, returned period range and
solver settings. Catch `disba.DispersionError` only when handling a failed
root search, and retain the diagnostic. Do not suppress arbitrary exceptions
or relabel malformed inputs as nonexistent modes.

## Verification and resources

Examples were checked with disba **0.7.0** and NumPy **1.26.4** on
**2026-09-14** using synthetic solid models. Checks cover a homogeneous
Rayleigh limit, layered phase/group curves, numerical sensitivities and
the helper's CSV/plot output and failure diagnostics. They do not validate
field-data inversion or fluid-layer models.

- [Official documentation](https://keurfonluu.github.io/disba/)
- [Version 0.7.0 dispersion implementation](https://github.com/keurfonluu/disba/blob/v0.7.0/disba/_dispersion.py)
- [Version 0.7.0 sensitivity implementation](https://github.com/keurfonluu/disba/blob/v0.7.0/disba/_sensitivity.py)
- [scripts/dispersion_analysis.py](scripts/dispersion_analysis.py): compute solid
  model dispersion, CSVs and optional plots. Input text begins with
  `thickness vp vs rho`, followed by rows in km, km/s, km/s and g/cm³.
  CSV columns retain requested periods and use NaN for unavailable roots;
  root-search diagnostics are printed separately. The built-in gradient/LVZ
  density estimates are illustrative assumptions, not Gardner's law.
