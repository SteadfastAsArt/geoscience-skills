---
name: mtpy
description: Magnetotelluric data processing and modelling. Read EDI files, analyze MT responses, perform inversions, and visualize resistivity models.
---

# mtpy - Magnetotelluric Analysis

Help users process and analyze magnetotelluric (MT) data.

## Installation

```bash
pip install mtpy
# Note: mtpy-v2 is the actively maintained version
pip install mtpy-v2
```

## Core Concepts

### What mtpy Does
- Read/write EDI files (industry standard)
- MT data processing and quality control
- 1D/2D/3D inversion interfaces
- Visualization of MT responses
- Phase tensor analysis

### Key Classes
| Class | Purpose |
|-------|---------|
| `MT` | Single station MT data |
| `MTCollection` | Multiple stations |
| `PlotMTResponse` | Plot impedance, phase |
| `PlotPhaseTensor` | Phase tensor ellipses |
| `PlotStrike` | Strike direction |

## Common Workflows

### 1. Load EDI File
```python
from mtpy import MT

# Load single station
mt = MT('station001.edi')

# Access data
print(f"Station: {mt.station}")
print(f"Latitude: {mt.latitude}")
print(f"Longitude: {mt.longitude}")
print(f"Frequencies: {len(mt.frequency)} points")

# Get impedance tensor
Z = mt.Z  # Complex impedance
Z_err = mt.Z_err  # Errors
```

### 2. Load Multiple Stations
```python
from mtpy import MTCollection

# Load all EDI files in directory
mc = MTCollection()
mc.from_edis('survey_data/*.edi')

# Access stations
print(f"Number of stations: {len(mc)}")
for station in mc:
    print(f"  {station.station}: ({station.latitude}, {station.longitude})")
```

### 3. Plot MT Response
```python
from mtpy import MT
from mtpy.imaging import PlotMTResponse

# Load data
mt = MT('station001.edi')

# Plot apparent resistivity and phase
plot = PlotMTResponse(mt)
plot.plot()
```

### 4. Plot Phase Tensor
```python
from mtpy import MT
from mtpy.imaging import PlotPhaseTensor

mt = MT('station001.edi')

# Phase tensor plot
pt = PlotPhaseTensor(mt)
pt.plot()

# Get phase tensor parameters
phi_min = mt.phase_tensor.phimin
phi_max = mt.phase_tensor.phimax
skew = mt.phase_tensor.skew
```

### 5. Pseudosection
```python
from mtpy import MTCollection
from mtpy.imaging import PlotPseudoSection

# Load profile data
mc = MTCollection()
mc.from_edis('profile/*.edi')

# Create pseudosection
ps = PlotPseudoSection(mc)
ps.plot(
    plot_type='apparent_resistivity',  # or 'phase'
    mode='te'  # or 'tm', 'det'
)
```

### 6. Strike Analysis
```python
from mtpy import MT
from mtpy.imaging import PlotStrike

mt = MT('station001.edi')

# Plot strike direction vs period
strike = PlotStrike(mt)
strike.plot()

# Get strike angles
strike_angle = mt.pt.strike
```

### 7. Data Quality Control
```python
from mtpy import MT
import numpy as np

mt = MT('station001.edi')

# Check data quality
Z = mt.Z

# Flag bad data (high errors)
bad_mask = mt.Z_err / np.abs(Z) > 0.5

# Remove bad frequencies
mt_clean = mt.remove_frequencies(mt.frequency[bad_mask])

# Interpolate gaps
mt_interp = mt.interpolate(np.logspace(-3, 3, 50))
```

### 8. Rotate to Strike
```python
from mtpy import MT

mt = MT('station001.edi')

# Rotate impedance tensor
rotation_angle = 30  # degrees clockwise from north
mt_rotated = mt.rotate(rotation_angle)

# Or rotate to geoelectric strike
mt.rotate_to_strike()
```

### 9. Tipper (Magnetic Transfer Function)
```python
from mtpy import MT
from mtpy.imaging import PlotTipper

mt = MT('station001.edi')

# Check if tipper data exists
if mt.has_tipper:
    # Plot tipper
    tipper = PlotTipper(mt)
    tipper.plot()

    # Get tipper values
    Tx = mt.Tipper[:, 0, 0]  # Real part, x-component
    Ty = mt.Tipper[:, 0, 1]  # Real part, y-component
```

### 10. Export Data
```python
from mtpy import MT

mt = MT('station001.edi')

# Export to different format
mt.write_edi('output.edi')

# Export to ModEM format
mt.write_modem('station001.dat')

# Export to CSV
import pandas as pd
df = pd.DataFrame({
    'frequency': mt.frequency,
    'rho_xy': mt.apparent_resistivity[:, 0, 1],
    'rho_yx': mt.apparent_resistivity[:, 1, 0],
    'phase_xy': mt.phase[:, 0, 1],
    'phase_yx': mt.phase[:, 1, 0]
})
df.to_csv('mt_data.csv', index=False)
```

### 11. 1D Inversion (Occam)
```python
from mtpy import MT
from mtpy.modeling import Occam1D

mt = MT('station001.edi')

# Setup 1D inversion
occam = Occam1D(mt)
occam.setup(
    n_layers=30,
    target_depth=10000,  # meters
    mode='det'  # determinant average
)

# Run inversion
occam.run()

# Plot result
occam.plot_model()
occam.plot_response()
```

### 12. Prepare for 2D/3D Inversion
```python
from mtpy import MTCollection

# Load data
mc = MTCollection()
mc.from_edis('survey/*.edi')

# Write ModEM input files
mc.write_modem(
    data_filename='ModEM_data.dat',
    model_filename='ModEM_model.rho',
    center_lat=35.0,
    center_lon=-120.0
)

# Write Mare2DEM input
mc.write_mare2dem('mare2dem_input.emdata')
```

## EDI File Structure

EDI files contain:
- Station metadata (location, elevation)
- Frequency array
- Impedance tensor (Z)
- Impedance errors
- Tipper (optional)

## Impedance Components

| Component | Description |
|-----------|-------------|
| Zxx | Ex/Bx (usually small) |
| Zxy | Ex/By (TE mode) |
| Zyx | Ey/Bx (TM mode) |
| Zyy | Ey/By (usually small) |

## Phase Tensor Parameters

| Parameter | Description |
|-----------|-------------|
| phi_min | Minimum phase |
| phi_max | Maximum phase |
| skew | 3D indicator |
| ellipticity | Shape measure |

## Tips

1. **Check data quality** before analysis
2. **Rotate to strike** for 2D interpretation
3. **Use phase tensor** for dimensionality analysis
4. **Compare TE and TM** modes for consistency
5. **Static shift correction** may be needed

## Resources

- Documentation: https://mtpy2.readthedocs.io/
- GitHub (v2): https://github.com/MTgeophysics/mtpy-v2
- GitHub (legacy): https://github.com/MTgeophysics/mtpy
- MT Forum: https://www.mtnet.info/
