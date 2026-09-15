---
name: discretize
description: Create finite-volume meshes and discrete differential operators with discretize. Use for TensorMesh or TreeMesh geometry, cell/face/edge ordering, divergence, interpolation and meshes supporting SimPEG; use a physics solver for inversion itself.
license: MIT
metadata:
  version: "1.0.0"
  author: Geoscience Skills
  skill_type: domain
  tags: '["Mesh", "Finite Volume", "Differential Operators"]'
  dependencies: '["discretize==0.12.0"]'
  complements: '["simpeg", "pyvista"]'
  workflow_role: processing
---

# discretize

Construct the mesh and location-aware operators before attaching physical data.
The library does not determine the CRS or the physical units of its coordinates.

## Choose geometry and data locations

Use `TensorMesh` for separable rectangular grids; choose `TreeMesh` when local
refinement substantially reduces cost. Finalize a tree before using its operators.
Pad model boundaries and refine sources, receivers and property contrasts as
required by the forward problem, then test domain and resolution sensitivity.

Record axis meanings, origin, units, cell widths and active-cell mask. In a 2D
vertical section the second coordinate can mean elevation, but this is a project
convention. A vector of length `n_cells` is not a face or edge vector.

## Divergence with an independent answer

The **synthetic** velocity field is u = (2x, -3y) per second. Its divergence is
-1 s⁻¹, including on this nonuniform mesh. Boundary fluxes are represented at
their actual face locations; no zero boundary condition is imposed implicitly.

```python
# example: nonuniform-divergence
import numpy as np
from discretize import TensorMesh

mesh = TensorMesh([[1.0, 2.0, 3.0], [2.0, 4.0]], origin=[0.0, 0.0])
face_velocity_m_s = np.r_[2 * mesh.faces_x[:, 0], -3 * mesh.faces_y[:, 1]]
divergence_s_inv = mesh.face_divergence @ face_velocity_m_s
integrated_divergence_m2_s = np.dot(mesh.cell_volumes, divergence_s_inv)
```

The rectangular area is 36 m², so the area-integrated divergence and outward
boundary flux are both -36 m²/s. In 2D, `cell_volumes` are cell **areas**.

## Handoffs and checks

- Inspect `cell_centers`, `faces_x`, `faces_y` and the operator shape. Keep cell,
  face, node and edge quantities distinct when interpolating or plotting.
- Cell ordering has the first coordinate varying fastest; reshape cell vectors
  with Fortran order when required. Test a spatially varying field, not a uniform
  array that could hide an ordering error.
- Verify constants/linear fields, conservation and convergence against an
  independent analytic case before using a mesh in an inverse problem.
- Preserve inactive/air masks and do not turn NaNs into zero conductivity.

See the [operator tutorials](https://discretize.simpeg.xyz/en/latest/tutorials/index.html)
and [API](https://discretize.simpeg.xyz/en/latest/api/index.html) for the chosen mesh.
