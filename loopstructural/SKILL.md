---
name: loopstructural
description: |
  Build 3D geological models with implicit surfaces, faults, folds, and stratigraphic
  constraints from structural geology data. Use when the agent needs to: (1) Build 3D
  geological models from structural data, (2) Model fault networks and displacements,
  (3) Create folded geology representations, (4) Interpolate geological surfaces,
  (5) Export models to VTK for visualization, (6) Perform uncertainty analysis on
  geological models, (7) Evaluate model values on grids.
license: MIT
metadata:
  version: "1.0.2"
  author: Geoscience Skills
  tags: '["Geological Modelling", "3D", "Faults", "Folds", "Structural Geology"]'
  dependencies: '["LoopStructural>=1.8.0", "numpy", "pandas", "pyvista"]'
  complements: '["gemgis", "gempy", "pyvista"]'
  workflow_role: modelling
  skill_type: domain
---

# Constrained implicit geological models

Use LoopStructural when observations constrain continuous geological scalar
fields. A scalar value labels an interface; it is not automatically an age,
measured depth or elevation. Record the coordinate CRS, shared XYZ units,
positive-Z convention, feature order and meaning of each scalar level.

## A constrained planar model

This synthetic example uses metre coordinates with a nonzero origin and an
asymmetric box. Its scalar field is
`Z - 3030 + 0.1*(X - 1050) - 0.05*(Y - 2100)` in metres. Scalar observations
and gradient constraints anchor both level and orientation; a single point
alone cannot define a geological surface.

```python
from itertools import product
from LoopStructural import GeologicalModel
import numpy as np
import pandas as pd

origin = np.array([1000., 2000., 3000.])
maximum = np.array([1100., 2200., 3060.])
xyz = np.array(list(product([1010., 1050., 1090.], [2020., 2180.], [3010., 3050.])))
data = pd.DataFrame(xyz, columns=['X', 'Y', 'Z'])
data['feature_name'] = 'strat'
data['val'] = xyz[:, 2] - 3030 + .1 * (xyz[:, 0] - 1050) - .05 * (xyz[:, 1] - 2100)
data[['gx', 'gy', 'gz']] = [.1, -.05, 1.]
model = GeologicalModel(origin, maximum)
model.data = data
model.create_and_add_foliation('strat', interpolatortype='FDI', nelements=1000)
model.update()
query = np.array([[1020., 2040., 3020.], [1080., 2160., 3040.], [1050., 2100., 3030.]])
values = model.evaluate_feature_value('strat', query)
```

The expected values are approximately −10, +10 and 0. Pass world coordinates
to `model.evaluate_feature_value(..., scale=True)` (the default). Direct feature
evaluation has a different local-coordinate contract. `GeologicalModel` 1.8
accepts the two bounds positionally; do not assume `origin=` and `maximum=`
constructor keywords from older examples still work.

## Evaluate a VTK grid

Continue with the model above. `regular_grid` returns an N×3 array; disable
shuffling and use Fortran ordering for VTK's x-fastest points. Write actual
scalar values into point data before saving.

```python
import pyvista as pv

shape = (9, 7, 5)
points = model.regular_grid(nsteps=shape, shuffle=False, order='F')
grid = pv.StructuredGrid()
grid.points = points
grid.dimensions = shape
grid.point_data['strat'] = model.evaluate_feature_value('strat', points)
surface = grid.contour([0.], scalars='strat')
if not np.isfinite(grid['strat']).all() or surface.n_cells == 0:
    raise ValueError('Model evaluation or requested isosurface is invalid')
```

Use `grid.save('model.vtk')` or `surface.save('strat.vtk')` when export is
requested. A rendered surface is a discretized level set; check constraint
residuals and mesh convergence before interpreting small structures.

## CSV helper and conditional models

The [model builder](scripts/build_model.py) supports constrained FDI/PLI
foliations and grid/isosurface export. It validates finite coordinates,
complete constraints and positive 3D extents, and reports failed or empty
exports with a nonzero exit status. Provide explicit bounds for planar or
zero-span input geometry rather than inventing an extent.

```bash
python scripts/build_model.py constraints.csv --grid --output model.vtk \
  --origin 1000 2000 3000 --maximum 1100 2200 3060 --nsteps 9 7 5
```

Resolve the command relative to this installed skill directory. The helper
requires `X,Y,Z,feature_name`, plus `val` and/or complete `gx,gy,gz` or `nx,ny,nz`
constraints; each feature needs a scalar level anchor. Missing vector rows are
all NaN, not zero vectors.

Read [interpolation and validation](references/interpolators.md) for numerical
choices, and [fault/fold requirements](references/geological_features.md) only
when those structures are needed. Faults, fold frames and uncertainty ensembles
need explicit kinematics/data and a separate configured model; they are not
created by a nominal CSV column or by this foliation helper.

## Verification scope

LoopStructural 1.8.0 with loop-interpolation 0.0.2 was exercised with FDI and
PLI planar models, world-coordinate evaluation, asymmetric grid ordering,
isosurface and VTK readback, plus malformed-input/CLI failures. This validates
the entrypoint and export path, not fault-network inversion, folded geology,
uncertainty estimates or the geological adequacy of sparse field constraints.

[Official model source](https://github.com/Loop3D/LoopStructural/blob/master/LoopStructural/modelling/core/geological_model.py),
checked 2026-09-14 against the installed 1.8.0 API.
