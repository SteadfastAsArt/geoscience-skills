---
name: bruges
description: Geophysical equations and rock physics calculations. Provides tools for AVO analysis, fluid substitution, wavelets, reflectivity, and common geophysics formulas.
---

# Bruges - Geophysics Equations

Help users with rock physics calculations, AVO analysis, and geophysical equations.

## Installation

```bash
pip install bruges
```

## Core Concepts

### Module Overview
| Module | Purpose |
|--------|---------|
| `bruges.rockphysics` | Rock physics models, fluid substitution |
| `bruges.reflection` | Reflectivity, AVO equations |
| `bruges.filters` | Wavelets, convolution |
| `bruges.petrophysics` | Petrophysical equations |
| `bruges.transform` | Coordinate transforms |
| `bruges.util` | Utility functions |

## Common Workflows

### 1. Zoeppritz Reflectivity (AVO)
```python
from bruges.reflection import zoeppritz

# Layer properties: Vp, Vs, rho
vp1, vs1, rho1 = 3000, 1500, 2.4  # Upper layer
vp2, vs2, rho2 = 3500, 1800, 2.5  # Lower layer

# Incident angles
import numpy as np
theta = np.arange(0, 45, 1)  # 0-44 degrees

# Calculate reflection coefficients
Rpp = zoeppritz(vp1, vs1, rho1, vp2, vs2, rho2, theta)

# Plot AVO curve
import matplotlib.pyplot as plt
plt.plot(theta, Rpp)
plt.xlabel('Angle (degrees)')
plt.ylabel('Rpp')
plt.title('AVO Response')
plt.show()
```

### 2. Shuey Approximation (AVO)
```python
from bruges.reflection import shuey

# Faster than Zoeppritz, accurate to ~30 degrees
vp1, vs1, rho1 = 3000, 1500, 2.4
vp2, vs2, rho2 = 3500, 1800, 2.5

theta = np.arange(0, 35, 1)
Rpp = shuey(vp1, vs1, rho1, vp2, vs2, rho2, theta)
```

### 3. AVO Intercept and Gradient
```python
from bruges.reflection import akirichards

# Aki-Richards approximation
vp1, vs1, rho1 = 3000, 1500, 2.4
vp2, vs2, rho2 = 3500, 1800, 2.5

theta = np.arange(0, 35, 1)
Rpp, G = akirichards(vp1, vs1, rho1, vp2, vs2, rho2, theta, return_gradient=True)
# Rpp[0] is the intercept (normal incidence)
# G is the gradient
```

### 4. Gassmann Fluid Substitution
```python
from bruges.rockphysics import gassmann

# Original saturated rock
vp_sat = 3200  # m/s
vs_sat = 1800  # m/s
rho_sat = 2.4  # g/cc

# Mineral properties (quartz)
k_min = 37  # GPa
rho_min = 2.65  # g/cc

# Original fluid (brine)
k_fl1 = 2.5  # GPa
rho_fl1 = 1.05  # g/cc

# New fluid (oil)
k_fl2 = 0.9  # GPa
rho_fl2 = 0.8  # g/cc

# Porosity
phi = 0.25

# Substitute fluid
vp_new, vs_new, rho_new = gassmann(
    vp_sat, vs_sat, rho_sat,
    k_min, rho_min,
    k_fl1, rho_fl1,
    k_fl2, rho_fl2,
    phi
)

print(f"Vp: {vp_sat} → {vp_new:.0f} m/s")
print(f"Vs: {vs_sat} → {vs_new:.0f} m/s")
```

### 5. Ricker Wavelet
```python
from bruges.filters import ricker
import numpy as np

# Create Ricker wavelet
duration = 0.128  # seconds
dt = 0.001  # sample rate (1 ms)
f = 25  # dominant frequency (Hz)

t, wavelet = ricker(duration, dt, f)

import matplotlib.pyplot as plt
plt.plot(t, wavelet)
plt.xlabel('Time (s)')
plt.ylabel('Amplitude')
plt.title(f'Ricker Wavelet ({f} Hz)')
plt.show()
```

### 6. Ormsby Wavelet
```python
from bruges.filters import ormsby

# Bandpass wavelet with corner frequencies
duration = 0.128
dt = 0.001
f = [5, 10, 50, 60]  # Low cut, low pass, high pass, high cut

t, wavelet = ormsby(duration, dt, f)
```

### 7. Convolve Reflectivity with Wavelet
```python
from bruges.filters import ricker
import numpy as np
from scipy.signal import convolve

# Create reflectivity series
n_samples = 500
rc = np.zeros(n_samples)
rc[100] = 0.1   # Positive reflection
rc[200] = -0.15  # Negative reflection
rc[350] = 0.08  # Another reflection

# Create wavelet
_, wavelet = ricker(0.128, 0.001, 30)

# Convolve
synthetic = convolve(rc, wavelet, mode='same')

import matplotlib.pyplot as plt
fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(10, 5))
ax1.plot(rc)
ax1.set_title('Reflectivity')
ax2.plot(synthetic)
ax2.set_title('Synthetic Seismic')
plt.show()
```

### 8. Gardner's Relation (Density from Vp)
```python
from bruges.rockphysics import gardner

vp = np.array([2500, 3000, 3500, 4000])  # m/s
rho = gardner(vp)  # Returns density in g/cc

print(f"Vp: {vp}")
print(f"Rho: {rho}")
```

### 9. Castagna's Mudrock Line (Vs from Vp)
```python
from bruges.rockphysics import castagna

vp = np.array([2500, 3000, 3500, 4000])  # m/s
vs = castagna(vp)  # Returns Vs in m/s

print(f"Vp: {vp}")
print(f"Vs: {vs}")
```

### 10. Elastic Moduli Calculations
```python
from bruges.rockphysics import moduli

vp = 3500  # m/s
vs = 1800  # m/s
rho = 2.4  # g/cc

# Calculate bulk and shear moduli
K = moduli.bulk(vp, vs, rho)  # Bulk modulus (GPa)
mu = moduli.shear(vs, rho)    # Shear modulus (GPa)
E = moduli.youngs(vp, vs, rho)  # Young's modulus (GPa)
nu = moduli.poissons(vp, vs)    # Poisson's ratio

print(f"K = {K:.1f} GPa")
print(f"μ = {mu:.1f} GPa")
print(f"E = {E:.1f} GPa")
print(f"ν = {nu:.3f}")
```

### 11. Velocity from Moduli
```python
from bruges.rockphysics import moduli

K = 20  # Bulk modulus (GPa)
mu = 15  # Shear modulus (GPa)
rho = 2.4  # Density (g/cc)

vp = moduli.vp_from_moduli(K, mu, rho)
vs = moduli.vs_from_moduli(mu, rho)

print(f"Vp = {vp:.0f} m/s")
print(f"Vs = {vs:.0f} m/s")
```

### 12. Critical Angle and Reflection
```python
from bruges.reflection import critical_angle
import numpy as np

vp1 = 3000  # Upper layer Vp
vp2 = 3500  # Lower layer Vp

theta_c = critical_angle(vp1, vp2)
print(f"Critical angle: {np.degrees(theta_c):.1f} degrees")
```

## AVO Classification

| Class | Intercept | Gradient | Description |
|-------|-----------|----------|-------------|
| I | + | - | High impedance sand |
| II | ~0 | - | Near-zero intercept |
| IIp | ~0 | + | Phase reversal |
| III | - | - | Low impedance sand |
| IV | - | + | Very low impedance |

## Common Rock Physics Models

| Model | Use Case |
|-------|----------|
| Gassmann | Fluid substitution |
| Biot | Wave propagation in porous media |
| Hertz-Mindlin | Grain contact mechanics |
| Han | Empirical Vp-porosity-clay |

## Tips

1. **Use radians for angles** in some functions - check documentation
2. **Zoeppritz is exact** but slower than approximations
3. **Shuey works to ~30°**, use Zoeppritz beyond
4. **Gassmann assumes** low frequency, connected pores
5. **Gardner/Castagna** are empirical - calibrate to your data

## Resources

- Documentation: https://code.agilescientific.com/bruges
- GitHub: https://github.com/agilescientific/bruges
- Tutorials: https://github.com/agile-geoscience/notebooks
