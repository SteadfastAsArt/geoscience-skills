---
name: petropy
description: Petrophysical analysis and formation evaluation. Calculate porosity, water saturation, permeability, and lithology from well logs.
---

# PetroPy - Petrophysical Analysis

Help users perform formation evaluation and petrophysical calculations from well logs.

## Installation

```bash
pip install petropy
```

## Core Concepts

### What PetroPy Does
- Load and manage well log data
- Calculate petrophysical properties
- Multi-mineral analysis
- Fluid saturation calculations
- Permeability estimation

### Key Classes
| Class | Purpose |
|-------|---------|
| `Log` | Main well log container |
| `electrofacies` | Facies classification |
| `Formations` | Zone management |

## Common Workflows

### 1. Load Well Log Data
```python
import petropy as pp

# Load from LAS file
log = pp.Log('well.las')

# View available curves
print(log.keys())

# Access curve data
depth = log['DEPT']
gr = log['GR']
nphi = log['NPHI']
rhob = log['RHOB']

# View header info
print(log.well)
```

### 2. Basic Formation Evaluation
```python
import petropy as pp

log = pp.Log('well.las')

# Calculate total porosity from density
log.formation_porosity(
    rhob_curve='RHOB',
    rhob_matrix=2.65,    # g/cc (sandstone)
    rhob_fluid=1.0       # g/cc (water)
)

# Calculate water saturation (Archie)
log.water_saturation(
    method='archie',
    rt_curve='RT',
    porosity_curve='PHIT',
    rw=0.05,            # Formation water resistivity
    a=1.0,              # Tortuosity factor
    m=2.0,              # Cementation exponent
    n=2.0               # Saturation exponent
)

# View results
print(log['PHIT'])  # Total porosity
print(log['SW'])    # Water saturation
```

### 3. Shale Volume Calculation
```python
import petropy as pp

log = pp.Log('well.las')

# Calculate shale volume from gamma ray
log.shale_volume(
    gr_curve='GR',
    gr_clean=20,     # GR of clean sand
    gr_shale=120,    # GR of shale
    method='linear'  # or 'larionov_young', 'larionov_old', 'clavier'
)

# View result
vsh = log['VSH']
```

### 4. Porosity Corrections
```python
import petropy as pp

log = pp.Log('well.las')

# Calculate shale volume first
log.shale_volume(gr_curve='GR', gr_clean=20, gr_shale=120)

# Density porosity with shale correction
log.formation_porosity(
    rhob_curve='RHOB',
    rhob_matrix=2.65,
    rhob_fluid=1.0,
    rhob_shale=2.45,
    vsh_curve='VSH'
)

# Neutron-density crossplot porosity
log.crossplot_porosity(
    nphi_curve='NPHI',
    rhob_curve='RHOB',
    nphi_matrix=0.0,
    rhob_matrix=2.65
)
```

### 5. Permeability Estimation
```python
import petropy as pp

log = pp.Log('well.las')

# Timur equation
log.permeability(
    method='timur',
    porosity_curve='PHIT',
    sw_curve='SW'
)

# Or Coates equation
log.permeability(
    method='coates',
    porosity_curve='PHIT',
    sw_curve='SW'
)

# View results (in mD)
perm = log['PERM']
```

### 6. Multi-Mineral Analysis
```python
import petropy as pp

log = pp.Log('well.las')

# Define mineral endpoints
minerals = {
    'quartz': {'rhob': 2.65, 'nphi': -0.02, 'pe': 1.81},
    'calcite': {'rhob': 2.71, 'nphi': 0.0, 'pe': 5.08},
    'dolomite': {'rhob': 2.87, 'nphi': 0.02, 'pe': 3.14},
    'clay': {'rhob': 2.45, 'nphi': 0.35, 'pe': 3.5}
}

# Solve for volumes (requires optimization)
# This is typically done with matrix methods
```

### 7. Pay Flag Calculation
```python
import petropy as pp
import numpy as np

log = pp.Log('well.las')

# Calculate properties
log.shale_volume(gr_curve='GR', gr_clean=20, gr_shale=120)
log.formation_porosity(rhob_curve='RHOB', rhob_matrix=2.65, rhob_fluid=1.0)
log.water_saturation(method='archie', rt_curve='RT', porosity_curve='PHIT', rw=0.05)

# Define pay cutoffs
vsh_cutoff = 0.4     # Max shale volume
phi_cutoff = 0.08    # Min porosity
sw_cutoff = 0.6      # Max water saturation

# Calculate pay flag
pay = (log['VSH'] < vsh_cutoff) & \
      (log['PHIT'] > phi_cutoff) & \
      (log['SW'] < sw_cutoff)

log['PAY'] = pay.astype(float)

# Calculate net pay
net_pay = np.sum(pay) * log.step
print(f"Net pay: {net_pay:.1f} m")
```

### 8. Fluid Contacts
```python
import petropy as pp
import numpy as np

log = pp.Log('well.las')

# Calculate water saturation
log.water_saturation(method='archie', rt_curve='RT', porosity_curve='PHIT', rw=0.05)

# Find oil-water contact (OWC)
# Where Sw transitions from low to high
sw = log['SW']
depth = log['DEPT']

# Simple gradient method
sw_gradient = np.gradient(sw)
owc_idx = np.argmax(sw_gradient)
owc_depth = depth[owc_idx]
print(f"Estimated OWC: {owc_depth:.1f} m")
```

### 9. Electrofacies Classification
```python
import petropy as pp
from sklearn.cluster import KMeans
import numpy as np

log = pp.Log('well.las')

# Prepare data for clustering
features = np.column_stack([
    log['GR'],
    log['RHOB'],
    log['NPHI'],
    log['RT']
])

# Remove NaN
valid = ~np.isnan(features).any(axis=1)
features_valid = features[valid]

# K-means clustering
kmeans = KMeans(n_clusters=4, random_state=42)
clusters = kmeans.fit_predict(features_valid)

# Add to log
facies = np.full(len(log['DEPT']), np.nan)
facies[valid] = clusters
log['FACIES'] = facies
```

### 10. Quick Look Plot
```python
import petropy as pp
import matplotlib.pyplot as plt

log = pp.Log('well.las')

# Calculate all properties
log.shale_volume(gr_curve='GR', gr_clean=20, gr_shale=120)
log.formation_porosity(rhob_curve='RHOB', rhob_matrix=2.65, rhob_fluid=1.0)
log.water_saturation(method='archie', rt_curve='RT', porosity_curve='PHIT', rw=0.05)

# Create plot
fig, axes = plt.subplots(1, 5, figsize=(15, 10), sharey=True)

depth = log['DEPT']

# Track 1: GR
axes[0].plot(log['GR'], depth, 'g-')
axes[0].set_xlim(0, 150)
axes[0].set_xlabel('GR (API)')
axes[0].fill_betweenx(depth, log['GR'], 0, alpha=0.3, color='green')

# Track 2: Resistivity
axes[1].semilogx(log['RT'], depth, 'r-')
axes[1].set_xlim(0.1, 1000)
axes[1].set_xlabel('RT (ohm-m)')

# Track 3: Porosity
axes[2].plot(log['NPHI'], depth, 'b-', label='NPHI')
axes[2].plot(log['PHIT'], depth, 'r-', label='PHIT')
axes[2].set_xlim(0.45, -0.15)
axes[2].set_xlabel('Porosity (v/v)')
axes[2].legend()

# Track 4: Saturation
axes[3].plot(log['SW'], depth, 'b-')
axes[3].set_xlim(0, 1)
axes[3].set_xlabel('Sw (v/v)')
axes[3].fill_betweenx(depth, log['SW'], 1, alpha=0.3, color='green', label='Hydrocarbon')
axes[3].fill_betweenx(depth, 0, log['SW'], alpha=0.3, color='blue', label='Water')

# Track 5: VSH
axes[4].plot(log['VSH'], depth, 'brown')
axes[4].set_xlim(0, 1)
axes[4].set_xlabel('Vsh (v/v)')
axes[4].fill_betweenx(depth, log['VSH'], 0, alpha=0.3, color='brown')

axes[0].invert_yaxis()
axes[0].set_ylabel('Depth (m)')
plt.tight_layout()
plt.savefig('petrophysical_summary.png', dpi=200)
```

### 11. Formation Tops
```python
import petropy as pp

log = pp.Log('well.las')

# Define formation tops
tops = {
    'Formation_A': 1500,
    'Formation_B': 1750,
    'Formation_C': 2000,
    'Formation_D': 2300
}

# Calculate properties by zone
for name, top_depth in tops.items():
    # Get zone indices
    if name != list(tops.keys())[-1]:
        next_name = list(tops.keys())[list(tops.keys()).index(name) + 1]
        base_depth = tops[next_name]
    else:
        base_depth = log['DEPT'].max()

    mask = (log['DEPT'] >= top_depth) & (log['DEPT'] < base_depth)

    print(f"\n{name} ({top_depth}-{base_depth} m):")
    print(f"  Avg Porosity: {log['PHIT'][mask].mean():.3f}")
    print(f"  Avg Sw: {log['SW'][mask].mean():.3f}")
    print(f"  Avg Vsh: {log['VSH'][mask].mean():.3f}")
```

### 12. Export Results
```python
import petropy as pp

log = pp.Log('well.las')

# Calculate all properties
log.shale_volume(gr_curve='GR', gr_clean=20, gr_shale=120)
log.formation_porosity(rhob_curve='RHOB', rhob_matrix=2.65, rhob_fluid=1.0)
log.water_saturation(method='archie', rt_curve='RT', porosity_curve='PHIT', rw=0.05)

# Export to LAS
log.to_las('well_interpreted.las')

# Export to CSV
import pandas as pd
df = pd.DataFrame({
    'DEPT': log['DEPT'],
    'GR': log['GR'],
    'VSH': log['VSH'],
    'PHIT': log['PHIT'],
    'SW': log['SW']
})
df.to_csv('well_interpreted.csv', index=False)
```

## Archie Parameters

| Parameter | Symbol | Typical Range |
|-----------|--------|---------------|
| Tortuosity | a | 0.6-1.0 |
| Cementation | m | 1.8-2.2 |
| Saturation exp | n | 1.8-2.2 |

## Porosity Equations

| Method | Equation |
|--------|----------|
| Density | φ = (ρma - ρb) / (ρma - ρfl) |
| Neutron-Density | φ = √(φN² + φD²) / 2 |
| Sonic | φ = (Δt - Δtma) / (Δtfl - Δtma) |

## Tips

1. **QC raw data** before calculations
2. **Apply environmental corrections** to logs
3. **Calibrate to core** when available
4. **Use local parameters** for Archie equation
5. **Check results** against expected ranges

## Resources

- GitHub: https://github.com/toddheitmann/PetroPy
- SPWLA: https://www.spwla.org/ (petrophysics resources)
