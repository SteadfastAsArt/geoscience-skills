---
name: pygimli
description: Multi-method geophysical modelling and inversion. Supports electrical resistivity tomography (ERT), seismic refraction (SRT), GPR, and joint inversions.
---

# pyGIMLi - Geophysical Inversion

Help users with geophysical modelling and inversion using pyGIMLi.

## Installation

```bash
pip install pygimli
# Or with conda (recommended)
conda install -c gimli -c conda-forge pygimli
```

## Core Concepts

### What pyGIMLi Does
- Electrical Resistivity Tomography (ERT/DC)
- Seismic Refraction Tomography (SRT)
- Induced Polarization (IP)
- Ground Penetrating Radar (GPR)
- Joint inversions
- Custom forward modelling

### Key Classes
| Class | Purpose |
|-------|---------|
| `pg.Mesh` | Finite element meshes |
| `pg.DataContainer` | Survey data and geometry |
| `pg.Inversion` | Base inversion framework |
| `ert.ERTManager` | ERT processing and inversion |
| `srt.SRTManager` | Seismic refraction inversion |

## Common Workflows

### 1. Load and View ERT Data
```python
import pygimli as pg
from pygimli.physics import ert

# Load data file (Unified Data Format)
data = ert.load("survey.ohm")

# View data
print(data)
print(f"Number of measurements: {data.size()}")

# Plot apparent resistivity pseudosection
ert.showData(data)
```

### 2. ERT Inversion
```python
import pygimli as pg
from pygimli.physics import ert

# Load data
data = ert.load("survey.ohm")

# Create ERT manager
mgr = ert.ERTManager(data)

# Run inversion
model = mgr.invert(
    lam=20,          # Regularization parameter
    verbose=True
)

# Plot result
mgr.showResult()

# Get resistivity values
resistivity = mgr.model
```

### 3. Create Custom Mesh
```python
import pygimli as pg
from pygimli.physics import ert

# Load data for electrode positions
data = ert.load("survey.ohm")

# Create mesh with quality parameters
mesh = pg.meshtools.createParaMesh(
    data.sensors(),
    quality=34.0,      # Mesh quality
    paraMaxCellSize=5, # Max cell size in m
    boundary=2,        # Boundary extension factor
    paraDX=0.3         # Horizontal refinement
)

# View mesh
pg.show(mesh)
```

### 4. Forward Modelling (ERT)
```python
import pygimli as pg
from pygimli.physics import ert
import numpy as np

# Create simple mesh
mesh = pg.createGrid(
    x=np.linspace(0, 50, 51),
    y=np.linspace(-20, 0, 21)
)

# Assign resistivity model
rho = np.ones(mesh.cellCount()) * 100  # Background 100 Ohm-m
rho[mesh.cellCenters()[:, 1] > -5] = 500  # Top layer 500 Ohm-m

# Define electrode positions
electrodes = pg.utils.grange(0, 50, n=26)

# Create data container for Wenner array
scheme = ert.createData(
    elecs=electrodes,
    schemeName='wa'  # Wenner-alpha
)

# Forward modelling
fop = ert.ERTModelling()
fop.setMesh(mesh)
fop.setData(scheme)

# Calculate synthetic data
data_synthetic = fop.response(rho)
```

### 5. Seismic Refraction Tomography
```python
import pygimli as pg
from pygimli.physics import srt

# Load traveltime data
data = srt.load("traveltimes.sgt")

# Create SRT manager
mgr = srt.SRTManager(data)

# Run inversion
model = mgr.invert(
    lam=30,
    zWeight=0.3,  # Vertical smoothing
    verbose=True
)

# Plot velocity model
mgr.showResult()
```

### 6. Induced Polarization
```python
import pygimli as pg
from pygimli.physics import ert

# Load IP data (with phase or chargeability)
data = pg.load("ip_data.ohm")

# ERT + IP joint processing
mgr = ert.ERTManager(data)

# Invert resistivity first
mgr.invert(lam=20)

# Then IP (phase or chargeability)
ip_model = mgr.invertIPData(data['ip'])
```

### 7. Time-lapse ERT
```python
import pygimli as pg
from pygimli.physics import ert

# Load baseline and monitor data
data_base = ert.load("baseline.ohm")
data_mon = ert.load("monitor.ohm")

# Invert baseline
mgr = ert.ERTManager(data_base)
model_base = mgr.invert(lam=20)

# Time-lapse inversion (ratio approach)
from pygimli.physics.ert import TimelapseERT

tl = TimelapseERT([data_base, data_mon])
tl.invert(lam=20)
tl.showResults()
```

### 8. Mesh Generation Options
```python
import pygimli as pg
from pygimli import meshtools as mt

# Polygon-based mesh
world = mt.createWorld(
    start=[-50, 0],
    end=[50, -30],
    worldMarker=True
)

# Add a circular anomaly
circle = mt.createCircle(
    pos=[0, -10],
    radius=5,
    marker=2
)

# Combine geometries
geometry = world + circle

# Generate mesh
mesh = mt.createMesh(geometry, quality=33, area=2)

# Visualize
pg.show(mesh)
```

### 9. Save and Load Results
```python
import pygimli as pg
from pygimli.physics import ert

# After inversion
mgr = ert.ERTManager()
mgr.load("survey.ohm")
model = mgr.invert()

# Save mesh with model
mgr.mesh.save("result_mesh.bms")

# Save model values
pg.save(model, "resistivity_model.vector")

# Export to VTK for ParaView
mgr.mesh.exportVTK("result", mgr.model)

# Load later
mesh = pg.load("result_mesh.bms")
model = pg.load("resistivity_model.vector")
```

### 10. Joint Inversion (ERT + SRT)
```python
import pygimli as pg
from pygimli.physics import ert, srt

# Load both datasets
ert_data = ert.load("ert_survey.ohm")
srt_data = srt.load("srt_survey.sgt")

# Create managers
ert_mgr = ert.ERTManager(ert_data)
srt_mgr = srt.SRTManager(srt_data)

# Structurally coupled joint inversion
from pygimli.frameworks import JointInversion

ji = JointInversion([ert_mgr, srt_mgr])
ji.invert(lam=20)
```

### 11. Model Quality Assessment
```python
import pygimli as pg
from pygimli.physics import ert

mgr = ert.ERTManager()
mgr.load("survey.ohm")
model = mgr.invert(lam=20)

# Coverage (sensitivity)
coverage = mgr.coverage()
pg.show(mgr.mesh, coverage, label='Coverage')

# Chi-squared misfit
chi2 = mgr.inv.chi2()
print(f"Chi² = {chi2:.2f}")

# Model resolution
# Higher = better resolved
```

### 12. Regularization Options
```python
from pygimli.physics import ert

mgr = ert.ERTManager()
mgr.load("survey.ohm")

# Standard smoothness constraint
model = mgr.invert(lam=20)

# Anisotropic smoothing (stronger vertical)
model = mgr.invert(lam=20, zWeight=0.3)

# Different regularization types
model = mgr.invert(
    lam=20,
    isReference=True,  # Occam-type
    # or
    # blockyModel=True  # Minimum gradient
)
```

## Data Formats

| Format | Extension | Description |
|--------|-----------|-------------|
| BERT/pyGIMLi | .ohm | Unified data format |
| Syscal | .txt | IRIS export |
| Res2DInv | .dat | 2D inversion format |
| ABEM | .ohm | ABEM Terrameter |
| SRT | .sgt | Seismic traveltimes |

## Array Types

| Code | Array |
|------|-------|
| `wa` | Wenner-alpha |
| `wb` | Wenner-beta |
| `dd` | Dipole-dipole |
| `pd` | Pole-dipole |
| `pp` | Pole-pole |
| `slm` | Schlumberger |
| `gr` | Gradient |

## Tips

1. **Start with higher lambda** (50-100) and decrease
2. **Check data quality** - remove outliers before inversion
3. **Use zWeight < 1** for layered structures
4. **Check coverage** - low coverage = poorly resolved
5. **Chi² ≈ 1** indicates good fit without overfitting

## Resources

- Documentation: https://www.pygimli.org/
- GitHub: https://github.com/gimli-org/gimli
- Tutorials: https://www.pygimli.org/tutorials.html
- Examples: https://www.pygimli.org/examples.html
