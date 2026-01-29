---
name: loopstructural
description: |
  Build 3D geological models with implicit surfaces, faults, folds, and stratigraphic
  constraints from structural geology data. Use when Claude needs to: (1) Build 3D
  geological models from structural data, (2) Model fault networks and displacements,
  (3) Create folded geology representations, (4) Interpolate geological surfaces,
  (5) Export models to VTK for visualization, (6) Perform uncertainty analysis on
  geological models, (7) Evaluate model values on grids.
---

# LoopStructural - 3D Geological Modelling

## Quick Reference

```python
from LoopStructural import GeologicalModel
from LoopStructural.visualisation import LavaVuModelViewer
import pandas as pd
import numpy as np

# Create model
model = GeologicalModel(origin=[0, 0, -1000], maximum=[10000, 10000, 0])

# Add data
model.data = pd.DataFrame({
    'X': [5000], 'Y': [5000], 'Z': [-500],
    'feature_name': ['strat'], 'val': [0]
})

# Build and visualize
model.create_and_add_foliation('strat', interpolatortype='PLI')
model.update()

viewer = LavaVuModelViewer(model)
viewer.add_isosurface(model['strat'], isovalue=0)
viewer.interactive()
```

## Key Classes

| Class | Purpose |
|-------|---------|
| `GeologicalModel` | Main model container - holds features and data |
| `ProcessInputData` | Data preparation and validation |
| `StructuralFrame` | Coordinate system for fold modelling |
| `FaultSegment` | Individual fault surface with displacement |

## Essential Operations

### Build Stratigraphic Model

```python
model = GeologicalModel([0, 0, -1000], [10000, 10000, 0])
model.data = pd.DataFrame({
    'X': [5000, 5000, 5000],
    'Y': [5000, 5000, 5000],
    'Z': [-200, -500, -800],
    'feature_name': ['strat', 'strat', 'strat'],
    'val': [0, 1, 2]  # Different unit values
})
model.create_and_add_foliation('strat', interpolatortype='PLI', nelements=1000)
model.update()
```

### Add Orientation Data

```python
# Structural measurements (strike/dip)
orientations = pd.DataFrame({
    'X': [2000, 5000, 8000],
    'Y': [5000, 5000, 5000],
    'Z': [-100, -100, -100],
    'feature_name': ['strat', 'strat', 'strat'],
    'strike': [90, 90, 90],
    'dip': [30, 30, 30],
    'val': [np.nan, np.nan, np.nan]
})
model.data = pd.concat([interfaces, orientations])
```

### Model with Fault

```python
# Define fault data
fault_data = pd.DataFrame({
    'X': [5000, 5000], 'Y': [2000, 8000], 'Z': [-500, -500],
    'feature_name': ['fault1', 'fault1'],
    'val': [0, 0], 'coord': [0, 0]
})
fault_orient = pd.DataFrame({
    'X': [5000], 'Y': [5000], 'Z': [-500],
    'feature_name': ['fault1'],
    'gx': [1], 'gy': [0], 'gz': [0]  # Fault normal
})

model.data = pd.concat([fault_data, fault_orient, strat_data])
model.create_and_add_fault('fault1', displacement=200)  # Add fault first
model.create_and_add_foliation('strat')  # Stratigraphy affected by fault
model.update()
```

### Folded Geology

```python
# Generate fold interface data
x = np.linspace(0, 10000, 20)
z = -500 + 200 * np.sin(2 * np.pi * x / 5000)
fold_data = pd.DataFrame({
    'X': x, 'Y': np.ones(20) * 5000, 'Z': z,
    'feature_name': 'strat', 'val': 0
})

model.data = fold_data
model.create_and_add_fold_frame('fold_frame')
model.create_and_add_folded_foliation('strat', fold_frame='fold_frame')
model.update()
```

### Evaluate on Grid

```python
# Create evaluation grid
x = np.linspace(0, 10000, 100)
y = np.linspace(0, 10000, 100)
z = np.linspace(-1000, 0, 50)
xx, yy, zz = np.meshgrid(x, y, z)
points = np.column_stack([xx.ravel(), yy.ravel(), zz.ravel()])

# Evaluate stratigraphy
values = model['strat'].evaluate_value(points)
values_3d = values.reshape(xx.shape)
```

### Export to VTK

```python
import pyvista as pv

# Export isosurface
isosurface = model['strat'].isosurface(isovalue=0)
isosurface.save('horizon.vtk')

# Export regular grid
surfaces = model.regular_grid(nsteps=[50, 50, 50])
grid = pv.StructuredGrid(*surfaces)
grid.save('geological_model.vtk')
```

## Data Requirements

| Data Type | Required Columns | Description |
|-----------|-----------------|-------------|
| Interface | X, Y, Z, feature_name, val | Points on geological surfaces |
| Orientation | X, Y, Z, feature_name, strike, dip | Structural measurements |
| Gradient | X, Y, Z, feature_name, gx, gy, gz | Normal vectors to surfaces |
| Fault | X, Y, Z, feature_name, val, coord | Fault surface points |

## Modelling Tips

1. **Add faults before stratigraphy** - Order matters for geological relationships
2. **Use orientation data** - Significantly improves model quality
3. **Check data consistency** - Conflicting data causes interpolation issues
4. **Start simple** - Add complexity incrementally
5. **Validate with sections** - Compare cross-sections to known geology

## References

- **[Geological Features](references/geological_features.md)** - Feature types and when to use them
- **[Interpolators](references/interpolators.md)** - Interpolation methods and parameters

## Scripts

- **[scripts/build_model.py](scripts/build_model.py)** - Build a basic geological model from CSV data
