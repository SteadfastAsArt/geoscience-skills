# PyVista Mesh Types

## Table of Contents
- [Overview](#overview)
- [PolyData](#polydata)
- [StructuredGrid](#structuredgrid)
- [UnstructuredGrid](#unstructuredgrid)
- [ImageData](#imagedata)
- [RectilinearGrid](#rectilineargrid)
- [Choosing the Right Type](#choosing-the-right-type)

## Overview

PyVista provides several mesh types, each optimized for different data structures. All are subclasses of `pyvista.DataSet`.

| Class | Structure | Use Case |
|-------|-----------|----------|
| `PolyData` | Points + polygons | Surfaces, point clouds, lines |
| `StructuredGrid` | Curvilinear 3D grid | Mapped surfaces, warped grids |
| `UnstructuredGrid` | Arbitrary cells | Finite element meshes |
| `ImageData` | Regular voxels | Seismic volumes, CT scans |
| `RectilinearGrid` | Axis-aligned variable spacing | Non-uniform grids |

## PolyData

Most versatile type for surfaces and point clouds.

### Create Point Cloud
```python
import pyvista as pv
import numpy as np

points = np.random.rand(1000, 3)
cloud = pv.PolyData(points)
cloud['values'] = np.random.rand(1000)
```

### Create Surface from Points
```python
# Delaunay triangulation
surface = cloud.delaunay_2d()

# Or create manually with faces
faces = np.array([3, 0, 1, 2, 3, 1, 2, 3])  # Two triangles
mesh = pv.PolyData(points, faces)
```

### Create Lines (Well Paths)
```python
points = np.array([[0, 0, 0], [1, 0, -1], [2, 0, -2]])
lines = pv.lines_from_points(points)
tube = lines.tube(radius=0.1)
```

### Common Operations
```python
# Compute normals
mesh.compute_normals(inplace=True)

# Smooth surface
smoothed = mesh.smooth(n_iter=100)

# Decimate (reduce triangles)
decimated = mesh.decimate(0.5)

# Extract edges
edges = mesh.extract_feature_edges()
```

## StructuredGrid

For curvilinear grids where connectivity is implicit from array shape.

### Create from Coordinates
```python
import pyvista as pv
import numpy as np

# Create coordinate arrays
x = np.arange(-10, 10, 0.5)
y = np.arange(-10, 10, 0.5)
x, y = np.meshgrid(x, y)
z = np.sin(np.sqrt(x**2 + y**2))

# Create grid
grid = pv.StructuredGrid(x, y, z)
grid['elevation'] = z.ravel()
```

### 3D Structured Grid
```python
# Define 3D coordinates
x = np.arange(0, 10, 1)
y = np.arange(0, 10, 1)
z = np.arange(0, 5, 1)
x, y, z = np.meshgrid(x, y, z, indexing='ij')

# Warp z coordinates
z = z - 0.1 * (x + y)

grid = pv.StructuredGrid(x, y, z)
```

### Common Operations
```python
# Extract surface
surface = grid.extract_surface()

# Slice
sliced = grid.slice(normal='z')

# Warp by scalar
warped = grid.warp_by_scalar('elevation', factor=2)
```

## UnstructuredGrid

For arbitrary cell types and connectivity (finite element meshes).

### Create from Cells
```python
import pyvista as pv
import numpy as np

# Define points
points = np.array([
    [0, 0, 0], [1, 0, 0], [1, 1, 0], [0, 1, 0],
    [0, 0, 1], [1, 0, 1], [1, 1, 1], [0, 1, 1]
])

# Define hexahedral cell
cells = np.array([8, 0, 1, 2, 3, 4, 5, 6, 7])
cell_types = np.array([pv.CellType.HEXAHEDRON])

grid = pv.UnstructuredGrid(cells, cell_types, points)
```

### Common Cell Types
```python
pv.CellType.TRIANGLE      # 5
pv.CellType.QUAD          # 9
pv.CellType.TETRA         # 10
pv.CellType.HEXAHEDRON    # 12
pv.CellType.WEDGE         # 13
pv.CellType.PYRAMID       # 14
```

### Load from File
```python
# VTK unstructured grid files
mesh = pv.read('mesh.vtu')

# FLAC3D, TOUGH2, etc. often export to VTK
```

## ImageData

Regular 3D voxel grids (uniform spacing).

### Create Volume
```python
import pyvista as pv
import numpy as np

# Create empty grid
grid = pv.ImageData()
grid.dimensions = (100, 100, 50)  # Number of points
grid.spacing = (25, 25, 10)       # Cell size in meters
grid.origin = (0, 0, -500)        # Origin position

# Add data (cells = dimensions - 1)
nx, ny, nz = 99, 99, 49
data = np.random.randn(nx * ny * nz)
grid.cell_data['amplitude'] = data
```

### From NumPy Array
```python
# 3D numpy array
volume = np.random.rand(50, 100, 100)

# Wrap as ImageData
grid = pv.ImageData()
grid.dimensions = np.array(volume.shape) + 1
grid.cell_data['values'] = volume.ravel(order='F')
```

### Common Operations
```python
# Volume rendering
plotter.add_volume(grid, cmap='seismic', opacity='sigmoid')

# Slice through volume
slice_xy = grid.slice(normal='z', origin=grid.center)

# Extract isosurface
contour = grid.contour([0.5, 1.0])

# Threshold by value
subset = grid.threshold([0.2, 0.8])
```

## RectilinearGrid

Non-uniform spacing along axes (still axis-aligned).

### Create Grid
```python
import pyvista as pv
import numpy as np

# Variable spacing
x = np.array([0, 1, 3, 6, 10, 15])
y = np.array([0, 2, 4, 6, 8, 10])
z = np.array([0, -100, -300, -600, -1000])

grid = pv.RectilinearGrid(x, y, z)
grid.cell_data['property'] = np.random.rand(grid.n_cells)
```

## Choosing the Right Type

| Data Type | Recommended Mesh |
|-----------|------------------|
| Point cloud (scattered) | `PolyData` |
| Surface mesh | `PolyData` |
| Well trajectories | `PolyData` (lines/tubes) |
| Topographic surface | `StructuredGrid` |
| Mapped horizon | `StructuredGrid` |
| Seismic cube | `ImageData` |
| CT/Medical scan | `ImageData` |
| Finite element mesh | `UnstructuredGrid` |
| Reservoir simulation grid | `UnstructuredGrid` or `RectilinearGrid` |

## Converting Between Types

```python
# StructuredGrid to PolyData (surface only)
surface = structured_grid.extract_surface()

# ImageData to UnstructuredGrid
ugrid = image_data.cast_to_unstructured_grid()

# Any mesh to PolyData triangles
triangulated = mesh.triangulate()
```

## Data Arrays

All mesh types support point and cell data:

```python
# Point data (values at vertices)
mesh.point_data['temperature'] = temp_values

# Cell data (values for each cell)
mesh.cell_data['porosity'] = poro_values

# Access data
temps = mesh['temperature']  # Shortcut
temps = mesh.point_data['temperature']
```
