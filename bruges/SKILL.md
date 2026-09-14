---
name: bruges
description: |
  Geophysical equations and rock physics calculations for seismic analysis.
  Use when the agent needs to: (1) Calculate AVO responses (Zoeppritz, Shuey, Aki-Richards),
  (2) Perform Gassmann fluid substitution, (3) Generate seismic wavelets (Ricker, Ormsby),
  (4) Compute reflectivity and synthetic seismograms, (5) Calculate elastic moduli from
  velocities, (6) Apply Gardner/Castagna empirical relations, (7) Model rock physics effects.
license: MIT
metadata:
  version: "1.0.2"
  author: Geoscience Skills
  tags: '["Rock Physics", "AVO", "Gassmann", "Wavelets", "Seismic Modelling"]'
  dependencies: '["bruges>=0.5.4", "numpy", "scipy", "setuptools<81"]'
  complements: '["segyio", "obspy", "lasio", "welly"]'
  workflow_role: analysis
  skill_type: domain
---

# Bruges: reflection and rock physics

Use Bruges for interface reflectivity, elastic properties, fluid substitution,
and analytic wavelets. Use a wave-equation solver for propagation modelling;
use a log reader for LAS input. Companion skills are optional.

## Inputs and conventions

- Convert velocity to **m/s**, density to **kg/m³**, and moduli to **Pa** for
  the examples below. Divide Pa by `1e9` only when reporting GPa.
- Reflection functions take incidence angles in **degrees**. Supply finite
  layer properties; positive density and shear modulus alone are insufficient:
  an isotropic solid also needs `vp**2 > (4/3) * vs**2` for positive bulk modulus.
- Keep missing log intervals marked. Do not turn NaNs into zero-valued rock
  properties or convolve through missing intervals as if they were observed.
- A synthetic seismic trace requires regularly sampled **two-way time**.
  Convert and resample depth logs first, retaining the velocity/datum choices.

## AVO at one interface

Runnable example with illustrative upper/lower properties:

```python
import numpy as np
from bruges.reflection import zoeppritz, shuey, akirichards

vp1, vs1, rho1 = 3000.0, 1700.0, 2300.0  # m/s, m/s, kg/m³
vp2, vs2, rho2 = 3200.0, 1800.0, 2350.0
theta_deg = np.arange(0.0, 31.0)
r_exact = zoeppritz(vp1, vs1, rho1, vp2, vs2, rho2, theta_deg)
r_shuey = shuey(vp1, vs1, rho1, vp2, vs2, rho2, theta_deg)
r_aki = akirichards(vp1, vs1, rho1, vp2, vs2, rho2, theta_deg)
intercept, gradient = shuey(vp1, vs1, rho1, vp2, vs2, rho2,
                            return_gradient=True)
```

`return_gradient` belongs to `shuey`, not `akirichards`; it returns the
intercept/gradient pair, not reflectivity plus gradient. Shuey's intercept is
an approximation to the exact normal-incidence impedance contrast. Verify the
exact result against `(rho2*vp2 - rho1*vp1) / (rho2*vp2 + rho1*vp1)`.

At or beyond critical angles, Zoeppritz responses can be complex. Retain their
phase or explicitly define the amplitude being plotted. An approximate
angle limit alone does not establish accuracy for every elastic contrast.
Interpret AVO classes using polarity convention, angle coverage and lithology;
an intercept/gradient sign pair is not a unique fluid diagnosis.

## Wavelet and time-domain synthetic

Bruges wavelets return a named tuple with **`amplitude` then `time`**.
Use the fields to avoid swapping a wavelet for its time axis.

```python
import numpy as np
from bruges.filters import ricker
from scipy.signal import convolve

dt_s = 0.001
time_s = np.arange(257) * dt_s  # Regular two-way-time sampling.
impedance = np.full(time_s.size, 3000.0 * 2300.0)
impedance[128:] = 3200.0 * 2350.0
reflectivity = np.zeros_like(impedance)
# Place an interface at the first sample of the lower layer.
reflectivity[1:] = np.diff(impedance) / (impedance[:-1] + impedance[1:])
wavelet = ricker(duration=0.128, dt=dt_s, f=25.0)
synthetic = convolve(reflectivity, wavelet.amplitude, mode='same')
```

Check sample interval, time alignment, peak polarity and amplitude on a single
known interface before generating a well tie. Read
[wavelet details](references/wavelets.md) for Ormsby/Klauder and phase rotation.

## Rock properties and fluid changes

For elastic moduli, Gardner/Castagna estimates or Gassmann substitution, read
[rock physics examples](references/rock_physics.md). The tested API uses
`moduli.mu`, `moduli.pr`, `moduli.vp`, `moduli.vs`, and `avseth_fluidsub`;
there is no top-level `gassmann` or `castagna` in `bruges.rockphysics`.
Gardner is in `bruges.petrophysics` and returns **kg/m³** by default.

Use measured/calibrated mineral and fluid properties at reservoir conditions.
Gassmann assumes a connected pore system, pressure equilibration at low
frequency, and an unchanged solid frame/shear modulus. Check the resulting
density change and shear-modulus invariance; unchanged Vs is not the invariant.

## Verification and resources

Examples were checked with Bruges **0.5.4**, NumPy **1.26.4** and SciPy
**1.17.1** on **2026-09-14**. Bruges 0.5.4 imports `pkg_resources`; the tested
environment uses setuptools 80.9.0. Install scientific dependencies in an
isolated environment. These examples do not certify every Bruges operation.

- [Reflection API](https://code.agilescientific.com/bruges/api/bruges.reflection.html)
- [Rock physics API](https://code.agilescientific.com/bruges/api/bruges.rockphysics.html)
- [Wavelet API](https://code.agilescientific.com/bruges/api/bruges.filters.html)
- [scripts/avo_analysis.py](scripts/avo_analysis.py): tested AVO helper. Its CLI
  takes velocity in m/s and density in **g/cm³**, unlike the SI examples above.
  Exact reflection requires Bruges; missing imports fail explicitly. Plots
  preserve real/imaginary components beyond critical angles. Classification
  is a screening heuristic; IIp is not inferred from gradient sign alone.
