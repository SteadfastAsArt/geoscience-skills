---
name: welly
description: Subsurface well data analysis toolkit. Load, process, and analyze well logs, striplogs, formation tops, and synthetic seismograms. Built on lasio.
---

# welly - Well Data Analysis

Help users load, process, and analyze subsurface well data including logs, striplogs, and synthetics.

## Installation

```bash
pip install welly
```

## Core Concepts

### Key Classes
| Class | Purpose |
|-------|---------|
| `Well` | Single well with curves, location, tops |
| `Project` | Collection of wells |
| `Curve` | Log curve with depth basis and data |
| `Synthetic` | Synthetic seismogram generation |

### Well Components
- **Header** - Well metadata (name, UWI, location)
- **Curves** - Log data (GR, NPHI, RHOB, etc.)
- **Tops** - Formation/horizon picks
- **Location** - Coordinates and deviation

## Common Workflows

### 1. Load a Single Well
```python
from welly import Well

# From LAS file
w = Well.from_las('well.las')

# Print summary
print(w)

# Access well info
print(w.name)
print(w.uwi)
print(w.location)
```

### 2. Load Multiple Wells (Project)
```python
from welly import Project

# Load all LAS files in directory
p = Project.from_las('wells/*.las')

# Print summary
print(p)
print(f"Number of wells: {len(p)}")

# Iterate over wells
for well in p:
    print(well.name, list(well.data.keys()))
```

### 3. Access Curve Data
```python
w = Well.from_las('well.las')

# List available curves
print(w.data.keys())

# Get specific curve
gr = w.data['GR']

# Curve properties
print(gr.mnemonic)
print(gr.units)
print(gr.start, gr.stop, gr.step)

# Get numpy array
data = gr.values
basis = gr.basis  # depth array
```

### 4. Plot Well Logs
```python
w = Well.from_las('well.las')

# Quick plot of single curve
w.data['GR'].plot()

# Plot multiple curves
import matplotlib.pyplot as plt

fig, axes = plt.subplots(1, 3, figsize=(10, 12), sharey=True)

w.data['GR'].plot(ax=axes[0], c='green')
w.data['NPHI'].plot(ax=axes[1], c='blue')
w.data['RHOB'].plot(ax=axes[2], c='red')

axes[0].set_ylabel('Depth (m)')
plt.tight_layout()
plt.show()
```

### 5. Work with Formation Tops
```python
from welly import Well

w = Well.from_las('well.las')

# Add tops manually
w.tops = {
    'TopFormationA': 1500.0,
    'TopFormationB': 1750.0,
    'TopFormationC': 2100.0,
}

# Access tops
for name, depth in w.tops.items():
    print(f"{name}: {depth} m")

# Plot with tops
ax = w.data['GR'].plot()
for name, depth in w.tops.items():
    ax.axhline(depth, color='red', linestyle='--', label=name)
```

### 6. Curve Processing
```python
w = Well.from_las('well.las')
gr = w.data['GR']

# Despike
gr_clean = gr.despike(window=5, z=2)

# Smooth
gr_smooth = gr.smooth(window=11)

# Resample to different step
gr_resampled = gr.resample(step=0.5)

# Normalize (0-1)
gr_norm = gr.normalize()

# Clip to depth range
gr_clipped = gr.clip(top=1500, bottom=2000)
```

### 7. Quality Control
```python
w = Well.from_las('well.las')

# Check for gaps
for name, curve in w.data.items():
    nulls = curve.null_count()
    pct = 100 * nulls / len(curve)
    print(f"{name}: {pct:.1f}% null")

# Check depth coverage
print(f"Start: {w.data['GR'].start}")
print(f"Stop: {w.data['GR'].stop}")
```

### 8. Create Synthetic Seismogram
```python
from welly import Well, Synthetic
import numpy as np

w = Well.from_las('well.las')

# Need sonic (DT) and density (RHOB)
dt = w.data['DT']
rhob = w.data['RHOB']

# Create acoustic impedance
vp = 1e6 / dt.values  # Convert to velocity
ai = vp * rhob.values

# Generate reflection coefficients
rc = np.diff(ai) / (ai[:-1] + ai[1:])

# Convolve with wavelet for synthetic
# (simplified example)
```

### 9. Export Data
```python
w = Well.from_las('well.las')

# To DataFrame
df = w.df()

# To LAS
w.to_las('output.las')

# To CSV
df.to_csv('well_data.csv')
```

### 10. Project-Level Analysis
```python
from welly import Project
import pandas as pd

p = Project.from_las('wells/*.las')

# Get all wells with GR curve
wells_with_gr = [w for w in p if 'GR' in w.data]

# Compute statistics across project
stats = []
for w in p:
    if 'GR' in w.data:
        gr = w.data['GR']
        stats.append({
            'well': w.name,
            'gr_mean': gr.values.mean(),
            'gr_std': gr.values.std(),
            'depth_range': gr.stop - gr.start
        })

df = pd.DataFrame(stats)
print(df)
```

### 11. Well Location and Deviation
```python
w = Well.from_las('well.las')

# Set location
w.location.x = 500000.0  # Easting
w.location.y = 6000000.0  # Northing
w.location.kb = 350.0     # Kelly bushing elevation

# Add deviation survey
w.location.deviation = deviation_data  # DataFrame with MD, INC, AZI
```

## Tips

1. **Use Project** for multi-well workflows - easier than managing individual files
2. **Check units** - welly tracks units, ensure consistency
3. **Despike before analysis** - remove outliers with `curve.despike()`
4. **Resample to common basis** - use `curve.resample()` for cross-well comparison
5. **welly extends lasio** - all lasio functionality available

## Common Curve Mnemonics

| Mnemonic | Description | Common Units |
|----------|-------------|--------------|
| GR | Gamma Ray | GAPI |
| NPHI | Neutron Porosity | v/v |
| RHOB | Bulk Density | g/cc |
| DT | Sonic | us/ft |
| RT/ILD | Deep Resistivity | ohm.m |
| CALI | Caliper | in |

## Resources

- GitHub: https://github.com/agile-geoscience/welly
- Tutorials: https://github.com/agile-geoscience/welly/tree/main/tutorial
- Related: lasio, striplog, bruges
