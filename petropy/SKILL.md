---
name: petropy
description: |
  Petrophysical analysis and formation evaluation from well logs. Calculate
  porosity, water saturation, permeability, and lithology. Use when Claude needs
  to: (1) Calculate shale volume from gamma ray, (2) Compute porosity from
  density/neutron/sonic logs, (3) Estimate water saturation using Archie or
  Simandoux, (4) Calculate permeability from porosity and saturation, (5) Perform
  pay zone identification, (6) Conduct multi-mineral analysis, (7) Generate
  petrophysical summation plots.
---

# PetroPy - Petrophysical Analysis

## Quick Reference

```python
import petropy as pp

# Load and inspect
log = pp.Log('well.las')
print(log.keys())              # Available curves
depth, gr = log['DEPT'], log['GR']

# Calculate properties
log.shale_volume(gr_curve='GR', gr_clean=20, gr_shale=120)
log.formation_porosity(rhob_curve='RHOB', rhob_matrix=2.65, rhob_fluid=1.0)
log.water_saturation(method='archie', rt_curve='RT', porosity_curve='PHIT', rw=0.05)
log.permeability(method='timur', porosity_curve='PHIT', sw_curve='SW')
```

## Key Classes

| Class | Purpose |
|-------|---------|
| `Log` | Main well log container, extends lasio.LASFile |
| `electrofacies` | Facies classification utilities |
| `Formations` | Zone/formation management |

## Essential Operations

### Shale Volume (Vsh)
```python
log.shale_volume(
    gr_curve='GR',
    gr_clean=20,           # GR of clean sand (API)
    gr_shale=120,          # GR of shale (API)
    method='linear'        # or 'larionov_young', 'larionov_old', 'clavier'
)
vsh = log['VSH']
```

### Porosity
```python
# Density porosity with shale correction
log.formation_porosity(
    rhob_curve='RHOB',
    rhob_matrix=2.65,      # g/cc (sandstone)
    rhob_fluid=1.0,        # g/cc (water)
    rhob_shale=2.45,       # optional shale correction
    vsh_curve='VSH'        # requires VSH curve
)
phi = log['PHIT']
```

### Water Saturation
```python
log.water_saturation(
    method='archie',       # or 'simandoux', 'indonesia'
    rt_curve='RT',
    porosity_curve='PHIT',
    rw=0.05,               # Formation water resistivity (ohm-m)
    a=1.0, m=2.0, n=2.0    # Archie parameters
)
sw = log['SW']
```

### Permeability
```python
log.permeability(
    method='timur',        # or 'coates'
    porosity_curve='PHIT',
    sw_curve='SW'
)
perm = log['PERM']         # Result in mD
```

### Pay Flag and Net Pay
```python
import numpy as np
pay = (log['VSH'] < 0.4) & (log['PHIT'] > 0.08) & (log['SW'] < 0.6)
log['PAY'] = pay.astype(float)
net_pay = np.sum(pay) * log.step
```

### Export Results
```python
log.to_las('well_interpreted.las')

# Or to CSV
import pandas as pd
df = pd.DataFrame({'DEPT': log['DEPT'], 'VSH': log['VSH'], 'PHIT': log['PHIT'], 'SW': log['SW']})
df.to_csv('results.csv', index=False)
```

## Archie Parameters

| Parameter | Symbol | Range | Description |
|-----------|--------|-------|-------------|
| Tortuosity | a | 0.6-1.0 | Formation factor coefficient |
| Cementation | m | 1.8-2.2 | Pore geometry factor |
| Saturation exp | n | 1.8-2.2 | Wettability factor |

## Matrix Properties

| Lithology | rhob (g/cc) | nphi (v/v) | DT (us/ft) |
|-----------|-------------|------------|------------|
| Sandstone | 2.65 | -0.02 | 55.5 |
| Limestone | 2.71 | 0.00 | 47.5 |
| Dolomite | 2.87 | 0.02 | 43.5 |
| Shale | 2.45 | 0.30-0.45 | 70-130 |

## References

- **[Calculations](references/calculations.md)** - Porosity, saturation, and permeability equations
- **[Fluid Properties](references/fluid_properties.md)** - Fluid property models and correlations

## Scripts

- **[scripts/formation_evaluation.py](scripts/formation_evaluation.py)** - Complete formation evaluation workflow
