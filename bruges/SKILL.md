---
name: bruges
description: |
  Geophysical equations and rock physics calculations for seismic analysis.
  Use when Claude needs to: (1) Calculate AVO responses (Zoeppritz, Shuey, Aki-Richards),
  (2) Perform Gassmann fluid substitution, (3) Generate seismic wavelets (Ricker, Ormsby),
  (4) Compute reflectivity and synthetic seismograms, (5) Calculate elastic moduli from
  velocities, (6) Apply Gardner/Castagna empirical relations, (7) Model rock physics effects.
---

# bruges - Geophysics Equations

## Quick Reference

```python
import bruges
import numpy as np

# AVO - Zoeppritz reflectivity
from bruges.reflection import zoeppritz
theta = np.arange(0, 45, 1)
Rpp = zoeppritz(vp1, vs1, rho1, vp2, vs2, rho2, theta)

# Wavelet - Ricker
from bruges.filters import ricker
t, w = ricker(duration=0.128, dt=0.001, f=25)

# Fluid substitution
from bruges.rockphysics import gassmann
vp_new, vs_new, rho_new = gassmann(vp, vs, rho, k_min, rho_min,
                                    k_fl1, rho_fl1, k_fl2, rho_fl2, phi)
```

## Module Overview

| Module | Purpose |
|--------|---------|
| `bruges.reflection` | Zoeppritz, Shuey, Aki-Richards AVO equations |
| `bruges.rockphysics` | Gassmann, Gardner, Castagna, elastic moduli |
| `bruges.filters` | Ricker, Ormsby wavelets, convolution |

## AVO Analysis

```python
from bruges.reflection import zoeppritz, shuey, akirichards
theta = np.arange(0, 45, 1)  # degrees

Rpp = zoeppritz(vp1, vs1, rho1, vp2, vs2, rho2, theta)  # Exact
Rpp = shuey(vp1, vs1, rho1, vp2, vs2, rho2, theta)      # Fast (~30 deg)
Rpp, G = akirichards(vp1, vs1, rho1, vp2, vs2, rho2, theta, return_gradient=True)
```

## Fluid Substitution

```python
from bruges.rockphysics import gassmann

vp_new, vs_new, rho_new = gassmann(
    vp_sat, vs_sat, rho_sat,   # Original saturated rock
    k_min, rho_min,             # Mineral (quartz: 37 GPa, 2.65 g/cc)
    k_fl1, rho_fl1,             # Original fluid (brine: 2.5 GPa, 1.05 g/cc)
    k_fl2, rho_fl2,             # New fluid (oil: 0.9 GPa, 0.8 g/cc)
    phi                         # Porosity
)
```

## Wavelets

```python
from bruges.filters import ricker, ormsby

# Ricker (single frequency)
t, wavelet = ricker(duration=0.128, dt=0.001, f=25)

# Ormsby (bandpass: low cut, low pass, high pass, high cut)
t, wavelet = ormsby(duration=0.128, dt=0.001, f=[5, 10, 50, 60])
```

## Synthetic Seismogram

```python
from bruges.filters import ricker
from scipy.signal import convolve

rc = np.diff(impedance) / (impedance[:-1] + impedance[1:])  # Reflectivity
_, wavelet = ricker(0.128, 0.001, 30)
synthetic = convolve(rc, wavelet, mode='same')
```

## Elastic Moduli

```python
from bruges.rockphysics import moduli

K = moduli.bulk(vp, vs, rho)      # Bulk modulus (GPa)
mu = moduli.shear(vs, rho)        # Shear modulus (GPa)
E = moduli.youngs(vp, vs, rho)    # Young's modulus (GPa)
nu = moduli.poissons(vp, vs)      # Poisson's ratio
```

## Empirical Relations

```python
from bruges.rockphysics import gardner, castagna

rho = gardner(vp)    # Density from Vp (g/cc)
vs = castagna(vp)    # Vs from Vp (mudrock line)
```

## AVO Classification

| Class | Intercept | Gradient | Description |
|-------|-----------|----------|-------------|
| I | + | - | High impedance sand |
| II | ~0 | - | Near-zero intercept |
| IIp | ~0 | + | Phase reversal |
| III | - | - | Low impedance sand |
| IV | - | + | Very low impedance |

## Tips

1. **Zoeppritz is exact** but slower - use Shuey for angles < 30 degrees
2. **Gassmann assumes** low frequency and connected pores
3. **Gardner/Castagna** are empirical - calibrate to your data
4. **Angles in degrees** for reflection functions

## References

- **[Rock Physics Equations](references/rock_physics.md)** - Velocity-porosity models and moduli
- **[Wavelets](references/wavelets.md)** - Wavelet types, parameters, and selection

## Scripts

- **[scripts/avo_analysis.py](scripts/avo_analysis.py)** - AVO modeling and classification
