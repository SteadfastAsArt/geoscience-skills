---
name: disba
description: Surface wave dispersion computation. Calculate phase and group velocity dispersion curves for layered Earth models using Numba acceleration.
---

# disba - Surface Wave Dispersion

Help users compute surface wave dispersion curves for layered velocity models.

## Installation

```bash
pip install disba
```

## Core Concepts

### What disba Does
- Calculate Rayleigh wave dispersion
- Calculate Love wave dispersion
- Phase and group velocities
- Sensitivity kernels
- Fast computation with Numba

### Key Functions
| Function | Purpose |
|----------|---------|
| `PhaseDispersion` | Phase velocity curves |
| `GroupDispersion` | Group velocity curves |
| `PhaseSensitivity` | Sensitivity kernels |
| `surf96` | Direct interface to algorithm |

## Common Workflows

### 1. Basic Dispersion Calculation
```python
import numpy as np
from disba import PhaseDispersion

# Define velocity model (thickness, Vp, Vs, density)
# thickness in km, velocities in km/s, density in g/cm³
thickness = np.array([0.5, 1.0, 2.0, 0.0])  # 0.0 = half-space
vp = np.array([1.5, 2.5, 4.0, 6.0])
vs = np.array([0.8, 1.4, 2.3, 3.5])
rho = np.array([1.8, 2.0, 2.3, 2.6])

# Periods to compute (seconds)
periods = np.linspace(0.1, 5.0, 50)

# Calculate Rayleigh wave phase velocity
pd = PhaseDispersion(*zip(thickness, vp, vs, rho))
cpr = pd(periods, mode=0, wave='rayleigh')  # Fundamental mode

print(f"Periods: {periods}")
print(f"Phase velocities: {cpr}")

# Plot
import matplotlib.pyplot as plt
plt.plot(periods, cpr, 'b-', label='Rayleigh')
plt.xlabel('Period (s)')
plt.ylabel('Phase velocity (km/s)')
plt.legend()
plt.show()
```

### 2. Multiple Modes
```python
import numpy as np
from disba import PhaseDispersion
import matplotlib.pyplot as plt

# Define model
thickness = np.array([0.5, 1.0, 2.0, 0.0])
vp = np.array([1.5, 2.5, 4.0, 6.0])
vs = np.array([0.8, 1.4, 2.3, 3.5])
rho = np.array([1.8, 2.0, 2.3, 2.6])

periods = np.linspace(0.1, 5.0, 50)
pd = PhaseDispersion(*zip(thickness, vp, vs, rho))

# Calculate multiple modes
for mode in range(3):  # Fundamental + 2 higher modes
    try:
        cpr = pd(periods, mode=mode, wave='rayleigh')
        plt.plot(periods, cpr, label=f'Mode {mode}')
    except:
        print(f"Mode {mode} not computed for all periods")

plt.xlabel('Period (s)')
plt.ylabel('Phase velocity (km/s)')
plt.legend()
plt.title('Rayleigh Wave Dispersion')
plt.show()
```

### 3. Group Velocity
```python
import numpy as np
from disba import GroupDispersion

# Define model
thickness = np.array([0.5, 1.0, 2.0, 0.0])
vp = np.array([1.5, 2.5, 4.0, 6.0])
vs = np.array([0.8, 1.4, 2.3, 3.5])
rho = np.array([1.8, 2.0, 2.3, 2.6])

periods = np.linspace(0.2, 5.0, 50)

# Calculate group velocity
gd = GroupDispersion(*zip(thickness, vp, vs, rho))
ugr = gd(periods, mode=0, wave='rayleigh')

import matplotlib.pyplot as plt
plt.plot(periods, ugr, 'r-', label='Group velocity')
plt.xlabel('Period (s)')
plt.ylabel('Group velocity (km/s)')
plt.legend()
plt.show()
```

### 4. Love Waves
```python
import numpy as np
from disba import PhaseDispersion

# Define model
thickness = np.array([0.5, 1.0, 2.0, 0.0])
vp = np.array([1.5, 2.5, 4.0, 6.0])
vs = np.array([0.8, 1.4, 2.3, 3.5])
rho = np.array([1.8, 2.0, 2.3, 2.6])

periods = np.linspace(0.1, 5.0, 50)
pd = PhaseDispersion(*zip(thickness, vp, vs, rho))

# Love wave dispersion
cpl = pd(periods, mode=0, wave='love')

import matplotlib.pyplot as plt
plt.plot(periods, cpl, 'g-', label='Love')
plt.xlabel('Period (s)')
plt.ylabel('Phase velocity (km/s)')
plt.legend()
plt.show()
```

### 5. Compare Rayleigh and Love
```python
import numpy as np
from disba import PhaseDispersion
import matplotlib.pyplot as plt

thickness = np.array([0.5, 1.0, 2.0, 0.0])
vp = np.array([1.5, 2.5, 4.0, 6.0])
vs = np.array([0.8, 1.4, 2.3, 3.5])
rho = np.array([1.8, 2.0, 2.3, 2.6])

periods = np.linspace(0.1, 5.0, 50)
pd = PhaseDispersion(*zip(thickness, vp, vs, rho))

cpr = pd(periods, mode=0, wave='rayleigh')
cpl = pd(periods, mode=0, wave='love')

plt.plot(periods, cpr, 'b-', label='Rayleigh')
plt.plot(periods, cpl, 'g-', label='Love')
plt.xlabel('Period (s)')
plt.ylabel('Phase velocity (km/s)')
plt.legend()
plt.title('Fundamental Mode Dispersion')
plt.show()
```

### 6. Sensitivity Kernels
```python
import numpy as np
from disba import PhaseSensitivity
import matplotlib.pyplot as plt

# Define model
thickness = np.array([0.5, 1.0, 2.0, 0.0])
vp = np.array([1.5, 2.5, 4.0, 6.0])
vs = np.array([0.8, 1.4, 2.3, 3.5])
rho = np.array([1.8, 2.0, 2.3, 2.6])

# Calculate sensitivity at specific period
period = 1.0  # seconds
ps = PhaseSensitivity(*zip(thickness, vp, vs, rho))

# Sensitivity to Vs
kernel = ps(period, mode=0, wave='rayleigh', parameter='velocity_s')

# Get depth array
depth = np.cumsum(thickness[:-1])
depth = np.insert(depth, 0, 0)

# Plot
plt.figure(figsize=(6, 8))
for i, (d, k) in enumerate(zip(depth, kernel)):
    if i < len(thickness) - 1:
        plt.barh(d + thickness[i]/2, k, height=thickness[i]*0.9)
plt.xlabel('Sensitivity (dc/dVs)')
plt.ylabel('Depth (km)')
plt.gca().invert_yaxis()
plt.title(f'Vs Sensitivity at T={period}s')
plt.show()
```

### 7. Forward Modelling for Inversion
```python
import numpy as np
from disba import PhaseDispersion

def forward_model(vs_profile, thickness, vp_vs_ratio=1.73, periods=None):
    """
    Forward model: Vs profile -> dispersion curve
    """
    if periods is None:
        periods = np.linspace(0.1, 5.0, 50)

    vp = vs_profile * vp_vs_ratio
    rho = 0.32 * vp + 0.77  # Gardner relation (approximate)

    pd = PhaseDispersion(*zip(thickness, vp, vs_profile, rho))
    return pd(periods, mode=0, wave='rayleigh')

# Example
thickness = np.array([0.5, 1.0, 2.0, 0.0])
vs = np.array([0.8, 1.4, 2.3, 3.5])
periods = np.linspace(0.1, 5.0, 50)

dc_predicted = forward_model(vs, thickness, periods=periods)
```

### 8. Inversion Setup (Simple Grid Search)
```python
import numpy as np
from disba import PhaseDispersion

# Observed dispersion curve
periods_obs = np.array([0.5, 1.0, 1.5, 2.0, 2.5, 3.0])
dc_obs = np.array([0.9, 1.1, 1.3, 1.5, 1.7, 1.9])
dc_err = np.array([0.05, 0.05, 0.05, 0.05, 0.05, 0.05])

# Fixed model structure
thickness = np.array([1.0, 2.0, 0.0])  # 2 layers + halfspace

# Grid search over Vs values
vs_range = np.arange(0.5, 2.5, 0.1)
best_misfit = np.inf
best_model = None

for vs1 in vs_range:
    for vs2 in vs_range:
        for vs3 in vs_range:
            if vs1 > vs2 or vs2 > vs3:  # Skip velocity inversions
                continue

            vs = np.array([vs1, vs2, vs3])
            vp = vs * 1.73
            rho = np.array([1.8, 2.0, 2.3])

            try:
                pd = PhaseDispersion(*zip(thickness, vp, vs, rho))
                dc_pred = pd(periods_obs, mode=0, wave='rayleigh')
                misfit = np.sum(((dc_obs - dc_pred) / dc_err) ** 2)

                if misfit < best_misfit:
                    best_misfit = misfit
                    best_model = vs.copy()
            except:
                continue

print(f"Best model: Vs = {best_model}")
print(f"Misfit: {best_misfit:.2f}")
```

### 9. Frequency vs Period
```python
import numpy as np
from disba import PhaseDispersion

thickness = np.array([0.5, 1.0, 2.0, 0.0])
vp = np.array([1.5, 2.5, 4.0, 6.0])
vs = np.array([0.8, 1.4, 2.3, 3.5])
rho = np.array([1.8, 2.0, 2.3, 2.6])

# Using frequency instead of period
frequencies = np.linspace(0.2, 10.0, 50)  # Hz
periods = 1.0 / frequencies

pd = PhaseDispersion(*zip(thickness, vp, vs, rho))
cpr = pd(periods, mode=0, wave='rayleigh')

import matplotlib.pyplot as plt
plt.plot(frequencies, cpr, 'b-')
plt.xlabel('Frequency (Hz)')
plt.ylabel('Phase velocity (km/s)')
plt.show()
```

### 10. Model Comparison
```python
import numpy as np
from disba import PhaseDispersion
import matplotlib.pyplot as plt

periods = np.linspace(0.1, 5.0, 50)

# Model 1: Simple gradient
thickness1 = np.array([0.5, 0.5, 0.5, 0.5, 0.0])
vs1 = np.array([0.5, 1.0, 1.5, 2.0, 2.5])

# Model 2: Low velocity zone
thickness2 = np.array([0.5, 0.5, 0.5, 0.5, 0.0])
vs2 = np.array([1.0, 0.7, 1.5, 2.0, 2.5])  # LVZ at 0.5-1.0 km

for vs, label in [(vs1, 'Gradient'), (vs2, 'LVZ')]:
    vp = vs * 1.73
    rho = np.ones_like(vs) * 2.0

    pd = PhaseDispersion(*zip(thickness1, vp, vs, rho))
    cpr = pd(periods, mode=0, wave='rayleigh')
    plt.plot(periods, cpr, label=label)

plt.xlabel('Period (s)')
plt.ylabel('Phase velocity (km/s)')
plt.legend()
plt.title('Effect of Low Velocity Zone')
plt.show()
```

## Model Parameters

| Parameter | Unit | Description |
|-----------|------|-------------|
| thickness | km | Layer thickness (0 = half-space) |
| vp | km/s | P-wave velocity |
| vs | km/s | S-wave velocity |
| rho | g/cm³ | Density |

## Wave Types

| Type | Description |
|------|-------------|
| Rayleigh | Vertical + radial motion |
| Love | Horizontal (SH) motion |

## Tips

1. **Last layer thickness = 0** indicates half-space
2. **Numba JIT compilation** - First call is slower
3. **Higher modes** may not exist at all periods
4. **Group velocity** is derivative of phase velocity
5. **Sensitivity kernels** help understand resolution

## Resources

- GitHub: https://github.com/keurfonluu/disba
- Paper: Thomson-Haskell method
- Related: surf96 (Computer Programs in Seismology)
