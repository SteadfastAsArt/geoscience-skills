# SimPEG Mesh Types and Discretization

## Table of Contents
- [Tensor Mesh](#tensor-mesh)
- [Tree Mesh](#tree-mesh)
- [Cylindrical Mesh](#cylindrical-mesh)
- [Mesh Design Guidelines](#mesh-design-guidelines)
- [Cell Properties](#cell-properties)

## Tensor Mesh

Regular rectilinear grid with variable cell sizes along each axis.

### 1D Tensor Mesh
```python
from discretize import TensorMesh
import numpy as np

# Uniform cells
hz = np.ones(50) * 10  # 50 cells, 10m each
mesh = TensorMesh([hz], origin='N')  # N = top at z=0 (depth positive down)

# Variable cell sizes (expanding with depth)
hz_core = np.ones(20) * 5      # Fine cells near surface
hz_pad = 5 * 1.3**np.arange(10)  # Expanding cells
hz = np.hstack([hz_core, hz_pad])
mesh = TensorMesh([hz], origin='N')
```

### 2D Tensor Mesh
```python
# Uniform mesh
hx = np.ones(100) * 20   # x: 100 cells, 20m
hz = np.ones(50) * 10    # z: 50 cells, 10m
mesh = TensorMesh([hx, hz], origin='CN')  # Centered x, top at 0

# With padding
def make_cells(core_n, core_size, pad_n, pad_factor):
    """Create cell widths with core and padding."""
    core = np.ones(core_n) * core_size
    pad = core_size * pad_factor**np.arange(1, pad_n+1)
    return np.hstack([pad[::-1], core, pad])

hx = make_cells(100, 10, 10, 1.3)
hz = np.hstack([np.ones(50)*5, 5*1.3**np.arange(1, 11)])  # Padding at depth only
mesh = TensorMesh([hx, hz], origin=['C', 'N'])
```

### 3D Tensor Mesh
```python
hx = np.ones(40) * 25
hy = np.ones(40) * 25
hz = np.ones(30) * 10
mesh = TensorMesh([hx, hy, hz], origin='CCN')

# Access properties
print(f"Number of cells: {mesh.nC}")
print(f"Number of nodes: {mesh.nN}")
print(f"Cell centers shape: {mesh.cell_centers.shape}")
```

### Origin Specification

| Code | Meaning |
|------|---------|
| `'0'` | Origin at 0 |
| `'C'` | Centered |
| `'N'` | Negative (max at 0) |

Example: `origin='CCN'` = centered in x, centered in y, top at z=0

## Tree Mesh

Adaptive octree (3D) or quadtree (2D) mesh for computational efficiency.

### Create and Refine
```python
from discretize import TreeMesh

# Base mesh (must be power of 2)
h = np.ones(64) * 25   # 64 cells per dimension
mesh = TreeMesh([h, h, h], origin='CCC')

# Refine around points
survey_locs = np.random.randn(50, 3) * 100
mesh.refine_points(survey_locs, padding_cells_by_level=[4, 4, 2], finalize=False)

# Refine in a box
mesh.refine_box(
    x0=[-200, -200, -300],
    x1=[200, 200, 0],
    levels=[2, 2],           # Refinement levels
    padding_cells_by_level=[2, 2],
    finalize=False
)

# Refine at surface
mesh.refine_surface(
    xyz=surface_points,      # Surface topography
    level=3,
    finalize=False
)

# Must finalize before use
mesh.finalize()
```

### Refinement Levels

| Level | Cell Size (base=25m) |
|-------|---------------------|
| 0 | 25m (base) |
| 1 | 12.5m |
| 2 | 6.25m |
| 3 | 3.125m |

### TreeMesh Tips

1. **Base cell size** should be coarsest acceptable resolution
2. **Dimensions must be 2^n** (e.g., 64, 128, 256)
3. **Refine before finalizing** - cannot modify after
4. **Memory efficient** for large 3D problems

## Cylindrical Mesh

For problems with cylindrical symmetry (e.g., borehole logging).

```python
from discretize import CylindricalMesh

# Radial cells (expanding outward)
hr = np.hstack([np.ones(10)*0.1, 0.1*1.2**np.arange(1, 21)])
# Vertical cells
hz = np.ones(100) * 1.0

mesh = CylindricalMesh([hr, 1, hz], origin=[0, 0, 'N'])  # 1 = single azimuthal cell
```

## Mesh Design Guidelines

### General Principles

| Aspect | Guideline |
|--------|-----------|
| Core region | Fine cells where data sensitivity is high |
| Padding | Expanding cells to absorb boundary effects |
| Aspect ratio | Keep cells roughly cubic when possible |
| Total size | Domain should be 3-5x larger than survey area |

### Method-Specific Guidelines

#### DC Resistivity
```python
# Core: survey area + 1-2 electrode spacings
# Depth: 2-3x maximum pseudo-depth
# Padding: 10+ cells expanding at 1.3x factor

electrode_spacing = 10
survey_length = 200
max_depth = survey_length / 2

hx_core = np.ones(int(survey_length/5)) * 5
hx_pad = 5 * 1.3**np.arange(1, 15)
hx = np.hstack([hx_pad[::-1], hx_core, hx_pad])

hz_core = np.ones(int(max_depth/5)) * 5
hz_pad = 5 * 1.3**np.arange(1, 10)
hz = np.hstack([hz_core, hz_pad])
```

#### Potential Fields (Magnetics/Gravity)
```python
# Core: covers anomaly region
# Padding: extensive (field extends to infinity)
# Depth extent: depends on expected source depth

core_extent = 1000  # meters
core_cell = 25
pad_factor = 1.4
n_pad = 15

h = np.hstack([
    core_cell * pad_factor**np.arange(n_pad, 0, -1),
    np.ones(int(core_extent/core_cell)) * core_cell,
    core_cell * pad_factor**np.arange(1, n_pad+1)
])
```

#### EM Methods
```python
# Skin depth consideration
import numpy as np

def skin_depth(resistivity, frequency):
    """Calculate EM skin depth in meters."""
    return 503 * np.sqrt(resistivity / frequency)

# Mesh depth should be 2-3 skin depths
rho_min = 10  # minimum expected resistivity
f_min = 1     # minimum frequency
depth_needed = 3 * skin_depth(rho_min, f_min)
```

## Cell Properties

### Accessing Cell Information
```python
# Cell centers (nC x dim array)
cc = mesh.cell_centers
x_centers = cc[:, 0]
z_centers = cc[:, 1] if mesh.dim >= 2 else None

# Cell volumes
volumes = mesh.cell_volumes

# Cell widths (for TensorMesh)
dx = mesh.h[0]  # x-direction cell widths
dz = mesh.h[-1]  # z-direction cell widths

# Number of cells
n_cells = mesh.nC
```

### Selecting Cells by Location
```python
# Find cells within a region
x_min, x_max = -50, 50
z_min, z_max = -100, -20

inds = (
    (mesh.cell_centers[:, 0] >= x_min) &
    (mesh.cell_centers[:, 0] <= x_max) &
    (mesh.cell_centers[:, 1] >= z_min) &
    (mesh.cell_centers[:, 1] <= z_max)
)

# Create model with anomaly
model = np.ones(mesh.nC) * background_value
model[inds] = anomaly_value
```

### Active Cells (for Topography)
```python
from discretize.utils import active_from_xyz

# Define topography
topo = np.c_[x_topo, z_topo]

# Get active cells (below topography)
active = active_from_xyz(mesh, topo)

# Number of active cells
n_active = np.sum(active)

# Create reduced model
model_reduced = np.ones(n_active) * value
```

### Mesh Interpolation
```python
# Interpolate model to different locations
from discretize import TensorMesh

# Query points
query_points = np.c_[x_query, z_query]

# Get interpolation matrix
P = mesh.get_interpolation_matrix(query_points, location_type='cell_centers')

# Interpolate
values_at_query = P @ model
```
