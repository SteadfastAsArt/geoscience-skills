# Petrophysical Calculations Reference

## Table of Contents
- [Shale Volume](#shale-volume)
- [Porosity](#porosity)
- [Water Saturation](#water-saturation)
- [Permeability](#permeability)
- [Net Pay](#net-pay)

## Shale Volume

### Linear Method
```
Vsh = (GR - GR_clean) / (GR_shale - GR_clean)
```

### Larionov (Tertiary/Young Rocks)
```
Vsh_linear = (GR - GR_clean) / (GR_shale - GR_clean)
Vsh = 0.083 * (2^(3.7 * Vsh_linear) - 1)
```

### Larionov (Older Rocks)
```
Vsh_linear = (GR - GR_clean) / (GR_shale - GR_clean)
Vsh = 0.33 * (2^(2.0 * Vsh_linear) - 1)
```

### Clavier Method
```
Vsh_linear = (GR - GR_clean) / (GR_shale - GR_clean)
Vsh = 1.7 - sqrt(3.38 - (Vsh_linear + 0.7)^2)
```

### Implementation
```python
import numpy as np

def shale_volume(gr, gr_clean, gr_shale, method='linear'):
    """Calculate shale volume from gamma ray."""
    vsh_linear = (gr - gr_clean) / (gr_shale - gr_clean)
    vsh_linear = np.clip(vsh_linear, 0, 1)

    if method == 'linear':
        return vsh_linear
    elif method == 'larionov_young':
        return 0.083 * (np.power(2, 3.7 * vsh_linear) - 1)
    elif method == 'larionov_old':
        return 0.33 * (np.power(2, 2.0 * vsh_linear) - 1)
    elif method == 'clavier':
        return 1.7 - np.sqrt(3.38 - np.power(vsh_linear + 0.7, 2))
    else:
        raise ValueError(f"Unknown method: {method}")
```

## Porosity

### Density Porosity
```
PHID = (rho_matrix - rho_bulk) / (rho_matrix - rho_fluid)
```

With shale correction:
```
PHID_corr = PHID - Vsh * (rho_matrix - rho_shale) / (rho_matrix - rho_fluid)
```

### Neutron-Density Crossplot
```
PHI_ND = sqrt((NPHI^2 + PHID^2) / 2)
```

For gas-bearing zones:
```
PHI_ND = (NPHI + PHID) / 2  # if NPHI < PHID (gas crossover)
```

### Sonic Porosity (Wyllie)
```
PHIS = (DT - DT_matrix) / (DT_fluid - DT_matrix)
```

### Effective Porosity
```
PHIE = PHIT * (1 - Vsh)
```

### Implementation
```python
import numpy as np

def density_porosity(rhob, rho_matrix=2.65, rho_fluid=1.0,
                     rho_shale=None, vsh=None):
    """Calculate density porosity with optional shale correction."""
    phid = (rho_matrix - rhob) / (rho_matrix - rho_fluid)

    if rho_shale is not None and vsh is not None:
        shale_effect = vsh * (rho_matrix - rho_shale) / (rho_matrix - rho_fluid)
        phid = phid - shale_effect

    return np.clip(phid, 0, 0.5)

def neutron_density_porosity(nphi, phid):
    """Calculate neutron-density crossplot porosity."""
    # Check for gas crossover
    gas_flag = nphi < phid

    phi = np.where(
        gas_flag,
        (nphi + phid) / 2,
        np.sqrt((nphi**2 + phid**2) / 2)
    )
    return np.clip(phi, 0, 0.5)

def sonic_porosity(dt, dt_matrix=55.5, dt_fluid=189.0):
    """Calculate sonic porosity using Wyllie equation."""
    phis = (dt - dt_matrix) / (dt_fluid - dt_matrix)
    return np.clip(phis, 0, 0.5)
```

## Water Saturation

### Archie Equation
```
Sw = ((a * Rw) / (Rt * phi^m))^(1/n)

Where:
  a = tortuosity factor (0.6-1.0)
  m = cementation exponent (1.8-2.2)
  n = saturation exponent (1.8-2.2)
  Rw = formation water resistivity
  Rt = true formation resistivity
  phi = porosity
```

### Simandoux (Shaly Sands)
```
Sw = ((a * Rw) / (2 * phi^m)) *
     (-Vsh/Rsh + sqrt((Vsh/Rsh)^2 + (4 * phi^m) / (a * Rw * Rt)))

Where:
  Rsh = resistivity of shale
  Vsh = volume of shale
```

### Indonesian Equation
```
1/sqrt(Rt) = sqrt(phi^m / (a * Rw)) * Sw^(n/2) + Vsh^(1-Vsh/2) / sqrt(Rsh) * Sw

(Solved iteratively for Sw)
```

### Implementation
```python
import numpy as np

def archie_sw(rt, phi, rw, a=1.0, m=2.0, n=2.0):
    """Calculate water saturation using Archie equation."""
    sw = np.power((a * rw) / (rt * np.power(phi, m)), 1/n)
    return np.clip(sw, 0, 1)

def simandoux_sw(rt, phi, rw, vsh, rsh, a=1.0, m=2.0, n=2.0):
    """Calculate water saturation using Simandoux equation."""
    term1 = (a * rw) / (2 * np.power(phi, m))
    term2 = vsh / rsh
    term3 = np.sqrt(term2**2 + (4 * np.power(phi, m)) / (a * rw * rt))
    sw = term1 * (-term2 + term3)
    return np.clip(np.power(sw, 1/n), 0, 1)
```

## Permeability

### Timur Equation
```
k = (a * phi^b) / Swi^c

Typical coefficients:
  a = 8581 (for k in mD, phi in fraction)
  b = 4.4
  c = 2.0
```

### Coates (Free Fluid Model)
```
k = ((100 * phi) * (FFI / BVI))^2

Where:
  FFI = Free Fluid Index (from NMR or estimated)
  BVI = Bulk Volume Irreducible
```

### Coates-Dumanoir
```
k = (c * phi^a * (1-Swi)^b / Swi^b)^2

Typical coefficients:
  c = 10 (sandstone)
  a = 2, b = 1
```

### Implementation
```python
import numpy as np

def timur_permeability(phi, swi, a=8581, b=4.4, c=2.0):
    """Calculate permeability using Timur equation."""
    swi = np.maximum(swi, 0.01)  # Avoid division by zero
    k = (a * np.power(phi, b)) / np.power(swi, c)
    return np.maximum(k, 0.001)  # Minimum 0.001 mD

def coates_permeability(phi, swi, c=10, a=2, b=1):
    """Calculate permeability using Coates-Dumanoir equation."""
    swi = np.maximum(swi, 0.01)
    numerator = c * np.power(phi, a) * np.power(1 - swi, b)
    denominator = np.power(swi, b)
    k = np.power(numerator / denominator, 2)
    return np.maximum(k, 0.001)
```

## Net Pay

### Cutoff-Based Pay Identification
```
Pay = 1 if:
  - Vsh < Vsh_cutoff (typically 0.3-0.5)
  - Phi > Phi_cutoff (typically 0.05-0.10)
  - Sw < Sw_cutoff (typically 0.5-0.7)
```

### Net-to-Gross
```
N/G = Net Pay Thickness / Gross Interval Thickness
```

### Hydrocarbon Pore Volume
```
HCPV = Phi * (1 - Sw) * h * A

Where:
  h = net pay thickness
  A = drainage area
```

### Implementation
```python
import numpy as np

def calculate_pay(vsh, phi, sw, vsh_cut=0.4, phi_cut=0.08, sw_cut=0.6):
    """Identify pay zones based on cutoffs."""
    pay = (vsh < vsh_cut) & (phi > phi_cut) & (sw < sw_cut)
    return pay.astype(float)

def net_pay_summary(depth, pay, phi, sw):
    """Calculate net pay statistics."""
    step = np.median(np.diff(depth))
    pay_mask = pay > 0.5

    net_pay = np.sum(pay_mask) * step
    gross = depth[-1] - depth[0]
    ntg = net_pay / gross if gross > 0 else 0

    avg_phi = np.mean(phi[pay_mask]) if np.any(pay_mask) else 0
    avg_sw = np.mean(sw[pay_mask]) if np.any(pay_mask) else 1

    return {
        'net_pay': net_pay,
        'gross': gross,
        'ntg': ntg,
        'avg_porosity': avg_phi,
        'avg_sw': avg_sw,
        'avg_hc_saturation': 1 - avg_sw
    }
```

## Typical Parameter Ranges

### Archie Parameters by Lithology

| Lithology | a | m | n |
|-----------|---|---|---|
| Clean Sandstone | 0.81 | 2.0 | 2.0 |
| Consolidated Sandstone | 1.0 | 2.0 | 2.0 |
| Unconsolidated Sand | 0.62 | 2.15 | 2.0 |
| Carbonate | 1.0 | 2.0-2.3 | 2.0 |
| Shaly Sandstone | 1.0 | 1.8-2.0 | 2.0 |

### Cutoff Guidelines

| Parameter | Low Cutoff | Moderate | High Cutoff |
|-----------|------------|----------|-------------|
| Vsh | 0.30 | 0.40 | 0.50 |
| Porosity | 0.05 | 0.08 | 0.10 |
| Sw | 0.50 | 0.60 | 0.70 |
| Permeability (mD) | 0.1 | 1.0 | 10.0 |
