---
name: rock-physics-avo
description: |
  Rock physics and AVO analysis workflow from well log preparation
  through elastic property calculation, fluid substitution, AVO
  modelling, and synthetic seismogram generation. Use when performing
  rock physics studies or AVO feasibility analysis.
license: MIT
metadata:
  skill_type: workflow
  version: 1.0.2
  author: Geoscience Skills
  tags: '["Rock Physics", "AVO", "Gassmann", "Fluid Substitution", "Synthetics", "Workflow"]'
  dependencies: '["lasio>=0.31", "bruges>=0.5.4", "numpy", "scipy", "setuptools<81"]'
  complements: '["lasio", "welly", "bruges", "segyio", "obspy"]'
  workflow_role: analysis
---

# Rock Physics & AVO Workflow

End-to-end pipeline for rock physics analysis and AVO feasibility studies,
from well log preparation through elastic property calculation, Gassmann
fluid substitution, AVO modelling, and synthetic seismogram generation.

## Skill Chain

```text
lasio / welly          bruges                    segyio / obspy
[Well Log Prep]     --> [Rock Physics]         --> [Synthetics / Tie]
  |                      |                          |
  Load LAS/DLIS          Elastic moduli             Wavelet extraction
  QC & despike           Gassmann fluid sub         Reflectivity series
  Resample curves        AVO intercept/gradient     Convolve synthetic
  Extract Vp, Vs, rho    Backus averaging           Well-seismic tie
```

## Decision Points

| Task | Library | When to Use |
|------|---------|-------------|
| Load well logs | lasio / dlisio | When logs are not already loaded |
| Curve QC and management | welly | Multi-curve processing, despiking |
| Elastic moduli, AVO equations | bruges | Core rock physics calculations |
| Gassmann fluid substitution | bruges | Predict fluid replacement effects |
| Wavelet extraction from seismic | segyio + bruges | When tying to seismic |
| Synthetic seismogram | bruges | Generate reflectivity and convolve |
| Dispersion curves | disba | Surface wave rock physics |

## Step-by-Step Orchestration

### Stage 1: Well Log Preparation (lasio + welly)

Select and QC a contiguous interval before these calculations. Required curves
are DT and RHOB; DTS is optional. This example explicitly permits the Castagna
estimate for missing DTS in an appropriate siliciclastic interval. It is an
empirical estimate, not a measured shear log. Nulls in unrelated curves must not
remove elastic samples, and invalid elastic samples must not be silently bridged.

```python
import lasio
import numpy as np

las = lasio.read('well.las')
df = las.df().copy()

def unit(curve):
    return las.curves[curve].unit.replace('µ', 'u').replace('μ', 'u').upper().replace(' ', '')

def sonic_velocity(curve):
    factors = {'US/FT': 0.3048e6, 'US/M': 1e6}
    values = df[curve].to_numpy(dtype=float)
    if unit(curve) not in factors:
        raise ValueError(f'Confirm sonic units for {curve}: {unit(curve)}')
    if not np.all(np.isfinite(values) & (values > 0)):
        raise ValueError(f'QC {curve}: nonpositive or missing transit times')
    return factors[unit(curve)] / values  # m/s

vp = sonic_velocity('DT')
vs_estimated = 'DTS' not in df.columns
if vs_estimated:
    vs = 0.8621 * vp - 1172.4
else:
    vs = sonic_velocity('DTS')  # Check existence before reading

density_factors = {'G/CC': 1000.0, 'G/CM3': 1000.0, 'G/C3': 1000.0, 'KG/M3': 1.0}
if unit('RHOB') not in density_factors:
    raise ValueError('Confirm RHOB units before converting to kg/m3')
rho = df['RHOB'].to_numpy(dtype=float) * density_factors[unit('RHOB')]
if not np.all(np.isfinite(rho) & (rho > 0) & (vs > 0) & (vp**2 > 4/3 * vs**2)):
    raise ValueError('Invalid elastic inputs: require positive density, Vs and bulk modulus')

depth_factors = {'M': 1.0, 'FT': 0.3048}
depth_unit = unit(las.curves[0].mnemonic)
if depth_unit not in depth_factors:
    raise ValueError('Confirm LAS depth units')
depth_m = df.index.to_numpy(dtype=float) * depth_factors[depth_unit]
if len(depth_m) < 2 or not np.all(np.isfinite(depth_m)) or np.any(np.diff(depth_m) <= 0):
    raise ValueError('Provide at least two samples on an increasing depth basis')
```

### Stage 2: Rock Physics Analysis (bruges)

```python
import bruges

# Elastic moduli from velocities
K = bruges.rockphysics.moduli.bulk(vp=vp, vs=vs, rho=rho)   # Bulk modulus
G = bruges.rockphysics.moduli.mu(vs=vs, rho=rho)            # Shear modulus, Pa
E = bruges.rockphysics.moduli.youngs(bulk=K, mu=G)          # Young's modulus, Pa
nu = bruges.rockphysics.moduli.pr(vp=vp, vs=vs)             # Poisson's ratio
AI = vp * rho                                             # Acoustic impedance, SI
SI = vs * rho                                             # Shear impedance, SI

# Vp/Vs ratio (key AVO indicator)
vp_vs = vp / vs
```

### Stage 3: Gassmann Fluid Substitution (bruges)

This branch assumes a brine-saturated, isotropic interval with connected pores,
an unchanged frame, and suitable low-frequency conditions. Supply interpreted
porosity as PHIE in v/v; raw NPHI requires lithology/gas corrections first. Fluid
properties below are illustrative and must match formation conditions.

```python
from bruges.rockphysics.fluidsub import avseth_fluidsub

if unit('PHIE') != 'V/V':
    raise ValueError('Supply interpreted PHIE in v/v for fluid substitution')
phi = df['PHIE'].to_numpy(dtype=float)
if not np.all(np.isfinite(phi) & (phi > 0) & (phi < 1)):
    raise ValueError('Fluid substitution requires finite porosity between 0 and 1')

# Mineral and fluid properties
K_mineral = 36.6e9   # Quartz bulk modulus (Pa)
K_brine = 2.6e9      # Brine bulk modulus (Pa)
rho_brine = 1050     # Brine density (kg/m3)
K_gas = 0.02e9       # Gas bulk modulus (Pa)
rho_gas = 100        # Gas density (kg/m3)

# The library performs inverse/forward Gassmann; VRH mixing is not this operation.
vp_gas, vs_gas, rho_gas_sat = avseth_fluidsub(
    vp=vp, vs=vs, rho=rho, phi=phi,
    rhof1=rho_brine, rhof2=rho_gas,
    kmin=K_mineral, kf1=K_brine, kf2=K_gas,
)
if not np.all(np.isfinite([vp_gas, vs_gas, rho_gas_sat])):
    raise ValueError('Invalid substituted model; review frame and fluid assumptions')
```

### Stage 4: AVO Analysis (bruges)

```python
# Keep every adjacent interface, rather than overwriting the last result.
angles_deg = np.arange(0, 40, 1)
upper = (vp[:-1], vs[:-1], rho[:-1])
lower = (vp[1:], vs[1:], rho[1:])
rc = bruges.reflection.shuey(*upper, *lower, theta1=angles_deg)
intercept, gradient = bruges.reflection.shuey(
    *upper, *lower, return_gradient=True
)

# AVO classification from intercept (R0) and gradient (G)
# Class I:   R0 > 0, G < 0  (hard sand, dim with offset)
# Class II:  R0 ~ 0, G < 0  (near-zero, polarity reversal)
# Class III: R0 < 0, G < 0  (soft sand, bright with offset)
# Class IV:  R0 < 0, G > 0  (very soft, dim with offset)

# Zoeppritz exact for full offset range
rc_exact = bruges.reflection.zoeppritz_rpp(*upper, *lower, theta1=angles_deg)
```

### Stage 5: Synthetic Seismogram (bruges + segyio)

Supply `time_depth.csv` with columns `depth_m,twt_s` from checkshots or a calibrated
sonic integration. Its depth basis and datum must match the LAS samples: measured
depth is not automatically TVD. Interpolate impedance onto uniform two-way time
before convolving a time-domain wavelet. For a well tie, select a seismic trace by
survey coordinates and compare matching time axes; trace 0 is not a well location.

```python
from scipy.signal import convolve

time_depth = np.loadtxt('time_depth.csv', delimiter=',', skiprows=1, ndmin=2)
if (time_depth.shape[1] != 2 or len(time_depth) < 2
        or not np.all(np.isfinite(time_depth))
        or np.any(np.diff(time_depth, axis=0) <= 0)):
    raise ValueError('Require increasing finite depth_m and twt_s columns')
if depth_m[0] < time_depth[0, 0] or depth_m[-1] > time_depth[-1, 0]:
    raise ValueError('Time-depth relation must cover the entire selected log interval')
twt_s = np.interp(depth_m, time_depth[:, 0], time_depth[:, 1])
dt_s = 0.002
twt_regular_s = np.arange(twt_s[0], twt_s[-1] + dt_s * 1e-6, dt_s)
if len(twt_regular_s) < 2:
    raise ValueError('Selected time interval is shorter than one sample')
impedance_t = np.interp(twt_regular_s, twt_s, vp * rho)
rc_series = np.r_[0.0, np.diff(impedance_t) / (impedance_t[:-1] + impedance_t[1:])]

# Bruges returns amplitudes first, time samples second.
wavelet, wavelet_time = bruges.filters.ricker(duration=0.128, dt=dt_s, f=25)
synthetic = convolve(rc_series, wavelet, mode='same')
assert synthetic.shape == twt_regular_s.shape
```

Repeat Stages 4–5 with the substituted velocities/density to compare fluid scenarios,
using the same chosen time-depth relation unless a travel-time change is explicitly
being modelled. Report correlation together with wavelet, time-depth provenance,
and any justified alignment edits; unconstrained stretching can hide a poor model.

## Common Pipelines

### AVO Feasibility Study
```text
- [ ] Load well logs (Vp, Vs, Rho, porosity) with lasio
- [ ] QC a contiguous log interval; retain raw data and document any justified gap treatment
- [ ] If no Vs log: estimate from Castagna or Greenberg-Castagna
- [ ] Calculate elastic moduli and impedances with bruges
- [ ] Run Gassmann fluid substitution (brine to gas/oil)
- [ ] Compare Vp, Vs, density, impedance before/after fluid sub
- [ ] Compute AVO response at target interface (Shuey or Zoeppritz)
- [ ] Classify AVO response (Class I-IV)
- [ ] Generate synthetic seismograms for both fluid scenarios
- [ ] Plot AVO crossplot (intercept vs gradient)
```

### Well-Seismic Tie
```text
- [ ] Load well logs and seismic trace at well location
- [ ] Create time-depth relationship from check shots or sonic
- [ ] Convert logs to time domain
- [ ] Extract wavelet from seismic (statistical or deterministic)
- [ ] Generate synthetic seismogram from reflectivity * wavelet
- [ ] Cross-correlate synthetic with seismic trace
- [ ] Constrain any alignment edits with checkshots and document their justification
- [ ] Report correlation coefficient
```

### Backus Averaging (Upscaling)
```text
- [ ] Load thin-bed well logs at fine sampling (0.5 ft)
- [ ] Define averaging window (e.g., quarter wavelength at target frequency)
- [ ] Apply Backus averaging to get effective anisotropic elastic properties
- [ ] Compare fine-scale vs upscaled reflectivity
- [ ] Assess thin-bed tuning effects
```

## When to Use

Use the rock physics & AVO workflow when:

- Performing AVO feasibility studies for exploration prospects
- Running Gassmann fluid substitution to predict fluid effects
- Generating synthetic seismograms for well-seismic ties
- Calculating elastic properties from well logs
- Classifying AVO response at target horizons

Use individual domain skills when:
- Only loading well logs (use `lasio` alone)
- Only computing dispersion curves (use `disba` alone)
- Only creating wavelets or filters (use `bruges` alone)

## Common Issues

| Issue | Solution |
|-------|----------|
| No shear sonic log | Estimate Vs from Castagna mudrock line or Greenberg-Castagna |
| Gassmann gives unrealistic velocities | Check porosity and mineral modulus inputs; phi must be > 0 |
| Negative Poisson's ratio | Usually indicates bad Vs data; QC shear sonic |
| Poor well-seismic tie | Check time-depth relationship; try different wavelets |
| AVO effect too small | May be real; check impedance contrast and Vp/Vs ratio |
| Fluid sub in shales | Review anisotropy, pore connectivity and frequency assumptions before applying Gassmann |

## API Sources

- [Bruges moduli and fluid substitution](https://code.agilescientific.com/bruges/api/bruges.rockphysics.html)
- [Bruges reflection signatures](https://code.agilescientific.com/bruges/api/bruges.reflection.html)
- [Bruges wavelet return order](https://code.agilescientific.com/bruges/userguide/Making_wavelets.html)
