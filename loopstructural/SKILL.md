---
name: loopstructural
description: 3D geological modelling with implicit surfaces. Build geological models with faults, folds, and stratigraphic constraints using structural geology data.
---

# LoopStructural - 3D Geological Modelling

Help users create 3D geological models from structural data.

## Installation

```bash
pip install LoopStructural
# For visualization
pip install pyvista
```

## Core Concepts

### What LoopStructural Does
- Implicit 3D geological modelling
- Fault network modelling
- Fold geometry modelling
- Uncertainty quantification
- Integration with structural data

### Key Classes
| Class | Purpose |
|-------|---------|
| `GeologicalModel` | Main model container |
| `ProcessInputData` | Data preparation |
| `StructuralFrame` | Coordinate system for folds |
| `FaultSegment` | Individual fault surfaces |

## Common Workflows

### 1. Simple Stratigraphic Model
```python
from LoopStructural import GeologicalModel
from LoopStructural.visualisation import LavaVuModelViewer
import pandas as pd
import numpy as np

# Define model extent
origin = [0, 0, -1000]
maximum = [10000, 10000, 0]

# Create stratigraphic data
data = pd.DataFrame({
    'X': [5000, 5000, 5000],
    'Y': [5000, 5000, 5000],
    'Z': [-200, -500, -800],
    'feature_name': ['unit_a', 'unit_b', 'unit_c'],
    'val': [0, 0, 0]  # Interface values
})

# Create model
model = GeologicalModel(origin, maximum)

# Add stratigraphy
model.create_and_add_foliation(
    'stratigraphy',
    interpolatortype='PLI',  # Piecewise linear interpolation
    nelements=1000
)

# Add data
model.data = data

# Update model
model.update()

# Visualize
viewer = LavaVuModelViewer(model)
viewer.add_isosurface(model['stratigraphy'], isovalue=0)
viewer.interactive()
```

### 2. Add Orientation Data
```python
import pandas as pd
import numpy as np
from LoopStructural import GeologicalModel

# Structural measurements (strike/dip)
data = pd.DataFrame({
    'X': [2000, 5000, 8000, 2000, 5000, 8000],
    'Y': [5000, 5000, 5000, 5000, 5000, 5000],
    'Z': [-100, -100, -100, -300, -300, -300],
    'feature_name': ['strat', 'strat', 'strat', 'strat', 'strat', 'strat'],
    'strike': [90, 90, 90, 90, 90, 90],      # Strike direction
    'dip': [30, 30, 30, 30, 30, 30],          # Dip angle
    'val': [np.nan, np.nan, np.nan, np.nan, np.nan, np.nan]  # No value for orientations
})

# Add interface points
interfaces = pd.DataFrame({
    'X': [5000, 5000],
    'Y': [5000, 5000],
    'Z': [-200, -600],
    'feature_name': ['strat', 'strat'],
    'val': [0, 1]  # Different units
})

all_data = pd.concat([data, interfaces])

model = GeologicalModel([0, 0, -1000], [10000, 10000, 0])
model.data = all_data
model.create_and_add_foliation('strat')
model.update()
```

### 3. Model with Fault
```python
from LoopStructural import GeologicalModel
import pandas as pd
import numpy as np

# Define fault data
fault_data = pd.DataFrame({
    'X': [5000, 5000, 5000],
    'Y': [2000, 5000, 8000],
    'Z': [-500, -500, -500],
    'feature_name': ['fault1', 'fault1', 'fault1'],
    'val': [0, 0, 0],  # On fault surface
    'coord': [0, 0, 0]  # Fault coordinate
})

# Fault orientation
fault_orient = pd.DataFrame({
    'X': [5000],
    'Y': [5000],
    'Z': [-500],
    'feature_name': ['fault1'],
    'gx': [1], 'gy': [0], 'gz': [0]  # Fault normal
})

# Stratigraphy data
strat_data = pd.DataFrame({
    'X': [3000, 7000],
    'Y': [5000, 5000],
    'Z': [-300, -700],
    'feature_name': ['strat', 'strat'],
    'val': [0, 0]
})

all_data = pd.concat([fault_data, fault_orient, strat_data])

# Create model with fault
model = GeologicalModel([0, 0, -1000], [10000, 10000, 0])
model.data = all_data

# Add fault first
model.create_and_add_fault(
    'fault1',
    displacement=200  # Fault displacement in model units
)

# Add stratigraphy (will be affected by fault)
model.create_and_add_foliation('strat')
model.update()
```

### 4. Folded Geology
```python
from LoopStructural import GeologicalModel
import pandas as pd
import numpy as np

# Generate synthetic fold data
x = np.linspace(0, 10000, 20)
y = np.ones(20) * 5000
z = -500 + 200 * np.sin(2 * np.pi * x / 5000)  # Sinusoidal fold

fold_data = pd.DataFrame({
    'X': x,
    'Y': y,
    'Z': z,
    'feature_name': 'strat',
    'val': 0
})

# Create model with fold
model = GeologicalModel([0, 0, -1000], [10000, 10000, 0])
model.data = fold_data

# Use fold interpolator
model.create_and_add_fold_frame('fold_frame')
model.create_and_add_folded_foliation(
    'strat',
    fold_frame='fold_frame'
)
model.update()
```

### 5. Export to VTK
```python
from LoopStructural import GeologicalModel

# After building model
model.update()

# Export surfaces to VTK
surfaces = model.regular_grid(nsteps=[50, 50, 50])

# Save as VTK for ParaView
import pyvista as pv
grid = pv.StructuredGrid(*surfaces)
grid.save('geological_model.vtk')

# Or export specific isosurface
isosurface = model['strat'].isosurface(isovalue=0)
isosurface.save('horizon.vtk')
```

### 6. Evaluate Model on Grid
```python
from LoopStructural import GeologicalModel
import numpy as np

# After building model
model.update()

# Create evaluation grid
x = np.linspace(0, 10000, 100)
y = np.linspace(0, 10000, 100)
z = np.linspace(-1000, 0, 50)
xx, yy, zz = np.meshgrid(x, y, z)

points = np.column_stack([xx.ravel(), yy.ravel(), zz.ravel()])

# Evaluate stratigraphy
values = model['strat'].evaluate_value(points)

# Reshape to 3D grid
values_3d = values.reshape(xx.shape)
```

### 7. Add Multiple Units
```python
from LoopStructural import GeologicalModel
import pandas as pd

# Interface data for multiple units
data = pd.DataFrame({
    'X': [5000, 5000, 5000, 5000],
    'Y': [5000, 5000, 5000, 5000],
    'Z': [-100, -300, -500, -700],
    'feature_name': ['strat', 'strat', 'strat', 'strat'],
    'val': [0, 1, 2, 3]  # Different unit values
})

model = GeologicalModel([0, 0, -1000], [10000, 10000, 0])
model.data = data
model.create_and_add_foliation('strat')
model.update()

# Extract specific horizons
from LoopStructural.visualisation import LavaVuModelViewer
viewer = LavaVuModelViewer(model)
viewer.add_isosurface(model['strat'], isovalue=0, name='unit_top')
viewer.add_isosurface(model['strat'], isovalue=1, name='unit_base')
viewer.interactive()
```

### 8. Model Quality Assessment
```python
from LoopStructural import GeologicalModel

model.update()

# Get model metrics
strat_feature = model['strat']

# Check data fit
residuals = strat_feature.evaluate_gradient(strat_feature.interpolator.get_gradient_control())

# Model statistics
print(f"Number of elements: {strat_feature.interpolator.n_elements}")
print(f"Number of data points: {len(strat_feature.interpolator.get_value_constraints())}")
```

### 9. Uncertainty Analysis
```python
from LoopStructural import GeologicalModel
from LoopStructural.modelling.features.fault import FaultSegment
import numpy as np

# Run multiple model realizations with perturbed data
n_realizations = 10
results = []

for i in range(n_realizations):
    # Perturb input data
    data_perturbed = data.copy()
    data_perturbed['Z'] += np.random.normal(0, 10, len(data))  # 10m uncertainty

    model = GeologicalModel([0, 0, -1000], [10000, 10000, 0])
    model.data = data_perturbed
    model.create_and_add_foliation('strat')
    model.update()

    # Store surface at evaluation points
    values = model['strat'].evaluate_value(eval_points)
    results.append(values)

# Calculate statistics
results = np.array(results)
mean = np.mean(results, axis=0)
std = np.std(results, axis=0)
```

### 10. Intrusive Bodies
```python
from LoopStructural import GeologicalModel
import pandas as pd

# Define intrusion boundary
intrusion_data = pd.DataFrame({
    'X': [5000, 4000, 6000, 5000, 5000],
    'Y': [5000, 5000, 5000, 4000, 6000],
    'Z': [-500, -500, -500, -500, -500],
    'feature_name': ['intrusion', 'intrusion', 'intrusion', 'intrusion', 'intrusion'],
    'val': [0, 0, 0, 0, 0]  # On boundary
})

model = GeologicalModel([0, 0, -1000], [10000, 10000, 0])
model.data = intrusion_data
model.create_and_add_foliation(
    'intrusion',
    interpolatortype='PLI'
)
model.update()
```

## Data Requirements

| Data Type | Required Columns | Description |
|-----------|-----------------|-------------|
| Interface | X, Y, Z, feature_name, val | Points on geological surfaces |
| Orientation | X, Y, Z, feature_name, strike, dip | Structural measurements |
| Gradient | X, Y, Z, feature_name, gx, gy, gz | Normal vectors |

## Interpolator Options

| Type | Description | Use Case |
|------|-------------|----------|
| `PLI` | Piecewise Linear | General purpose |
| `FDI` | Finite Difference | Faster, regular grids |
| `Surfe` | RBF-based | Sparse data |

## Tips

1. **Add faults before stratigraphy** - Order matters
2. **Use orientation data** - Improves model quality
3. **Check data consistency** - Conflicting data causes issues
4. **Start simple** - Add complexity incrementally
5. **Validate with sections** - Compare to known geology

## Resources

- Documentation: https://loop3d.github.io/LoopStructural/
- GitHub: https://github.com/Loop3D/LoopStructural
- Tutorials: https://loop3d.github.io/LoopStructural/auto_examples/
- Loop3D Project: https://loop3d.org/
