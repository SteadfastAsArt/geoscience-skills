# Mesh Generation in pyGIMLi

## Table of Contents
- [Overview](#overview)
- [Structured Meshes](#structured-meshes)
- [Unstructured Meshes](#unstructured-meshes)
- [Parameter Meshes](#parameter-meshes)
- [Geometry Building](#geometry-building)
- [Mesh Quality](#mesh-quality)
- [Import and Export](#import-and-export)

## Overview

pyGIMLi uses finite element meshes for forward modelling and inversion. The mesh defines:
- Domain geometry and boundaries
- Cell discretization for model parameters
- Node positions for FEM calculations

```python
import pygimli as pg
from pygimli import meshtools as mt
```

## Structured Meshes

### Regular Grid
```python
import pygimli as pg
import numpy as np

# 2D regular grid
mesh = pg.createGrid(
    x=np.linspace(0, 100, 51),   # 50 cells in x
    y=np.linspace(-50, 0, 26)    # 25 cells in y
)
print(f"Cells: {mesh.cellCount()}")
print(f"Nodes: {mesh.nodeCount()}")
pg.show(mesh)
```

### Refined Grid
```python
# Non-uniform spacing for refinement
x = np.concatenate([
    np.linspace(0, 20, 21),      # Fine near surface
    np.linspace(22, 100, 40)     # Coarser at depth
])
y = np.concatenate([
    np.linspace(-5, 0, 11),      # Fine at top
    np.linspace(-7, -50, 22)     # Coarser at depth
])
mesh = pg.createGrid(x=x, y=y)
```

## Unstructured Meshes

### From Polygon World
```python
from pygimli import meshtools as mt

# Create rectangular domain
world = mt.createWorld(
    start=[-50, 0],
    end=[50, -30],
    worldMarker=True
)

# Generate triangular mesh
mesh = mt.createMesh(
    world,
    quality=33,      # Minimum angle (degrees)
    area=5           # Maximum cell area
)
pg.show(mesh)
```

### With Anomalies
```python
from pygimli import meshtools as mt

# Background domain
world = mt.createWorld(start=[-50, 0], end=[50, -30])

# Add circular anomaly
circle = mt.createCircle(
    pos=[0, -10],
    radius=5,
    marker=2         # Different region marker
)

# Add rectangular block
block = mt.createRectangle(
    start=[-20, -15],
    end=[-10, -5],
    marker=3
)

# Combine geometries
geometry = world + circle + block

# Generate mesh
mesh = mt.createMesh(geometry, quality=33, area=2)

# Visualize with markers
pg.show(mesh, mesh.cellMarkers())
```

### Layered Model
```python
from pygimli import meshtools as mt

# Create layered structure
world = mt.createWorld(start=[-50, 0], end=[50, -30])

# Add horizontal layers
layer1 = mt.createPolygon(
    [[-50, -5], [50, -5], [50, 0], [-50, 0]],
    isClosed=True,
    marker=1
)
layer2 = mt.createPolygon(
    [[-50, -15], [50, -15], [50, -5], [-50, -5]],
    isClosed=True,
    marker=2
)

geometry = world + layer1 + layer2
mesh = mt.createMesh(geometry, quality=33)
```

## Parameter Meshes

For ERT/SRT inversions, use specialized parameter meshes.

### From Sensor Positions
```python
import pygimli as pg
from pygimli.physics import ert

# Load data to get electrode positions
data = ert.load("survey.ohm")

# Create parameter mesh
mesh = pg.meshtools.createParaMesh(
    data.sensors(),       # Sensor positions
    quality=34.0,         # Mesh quality
    paraMaxCellSize=5,    # Max cell size in parameter region
    boundary=2,           # Boundary extension factor
    paraDX=0.3,          # Horizontal refinement
    paraDepth=20         # Depth of parameter region
)
pg.show(mesh)
```

### Parameter Mesh Options

| Parameter | Description | Typical Value |
|-----------|-------------|---------------|
| `quality` | Minimum triangle angle | 30-34 |
| `paraMaxCellSize` | Max cell area in param region | 1-10 |
| `boundary` | Boundary extension factor | 1-3 |
| `paraDX` | Horizontal cell width at surface | 0.2-1.0 |
| `paraDepth` | Depth of investigation | Survey-dependent |

### Custom Boundaries
```python
# Add topography
import numpy as np

# Topography points
topo_x = np.linspace(-50, 50, 21)
topo_y = np.sin(topo_x / 10) * 3  # Example undulating surface

# Create mesh with topography
mesh = pg.meshtools.createParaMesh(
    data.sensors(),
    quality=34,
    surface=np.column_stack([topo_x, topo_y])
)
```

## Geometry Building

### Basic Shapes
```python
from pygimli import meshtools as mt

# Circle
circle = mt.createCircle(pos=[0, -10], radius=5, marker=2)

# Rectangle
rect = mt.createRectangle(start=[-5, -5], end=[5, -15], marker=3)

# Polygon
poly = mt.createPolygon(
    [[0, 0], [10, 0], [10, -10], [5, -15], [0, -10]],
    isClosed=True,
    marker=4
)

# Line (for boundaries/constraints)
line = mt.createLine(start=[0, 0], end=[50, 0])
```

### Boolean Operations
```python
# Combine geometries
combined = world + circle + rect

# Note: Overlapping regions take the marker of the last added shape
```

### Refinement Regions
```python
from pygimli import meshtools as mt

world = mt.createWorld(start=[-50, 0], end=[50, -30])

# Add refinement region (smaller cells near target)
refine = mt.createCircle(pos=[0, -10], radius=8, marker=0)
refine.setMarker(0)  # Same marker as background

geometry = world + refine
mesh = mt.createMesh(
    geometry,
    quality=33,
    area={"0": 1, "1": 10}  # Different areas by marker
)
```

## Mesh Quality

### Quality Metrics
```python
mesh = mt.createMesh(geometry, quality=33)

# Cell quality (0-1, higher is better)
qualities = mesh.cellQuality()
print(f"Min quality: {min(qualities):.3f}")
print(f"Mean quality: {np.mean(qualities):.3f}")

# Visualize quality
pg.show(mesh, qualities, label='Quality')
```

### Quality Parameters

| Quality Angle | Effect |
|---------------|--------|
| < 30 | May have numerical issues |
| 30-33 | Acceptable for most applications |
| 33-34 | Good quality |
| > 34 | Very high quality (slower generation) |

### Fix Poor Quality
```python
# If mesh has poor quality cells
mesh = mt.createMesh(
    geometry,
    quality=34,        # Increase quality threshold
    smooth=True,       # Apply smoothing
    area=2             # Reduce max cell size
)
```

## Import and Export

### Save Mesh
```python
# Native format
mesh.save("mesh.bms")

# With cell data
pg.save(mesh, "mesh_with_data.bms")
```

### Load Mesh
```python
mesh = pg.load("mesh.bms")
```

### Export Formats
```python
# VTK for ParaView
mesh.exportVTK("mesh")

# With model data
mesh.exportVTK("mesh_model", {"resistivity": model})

# ASCII format
mesh.exportBoundaryVTU("mesh_boundary")
```

### Import External Mesh
```python
# From Gmsh
mesh = pg.load("mesh.msh")

# From VTK
mesh = pg.load("mesh.vtk")
```

## Common Mesh Patterns

### ERT Survey Mesh
```python
from pygimli.physics import ert

# Standard approach
data = ert.load("survey.ohm")
mesh = pg.meshtools.createParaMesh(
    data.sensors(),
    quality=34,
    paraMaxCellSize=5,
    boundary=2
)
```

### SRT Survey Mesh
```python
from pygimli.physics import srt

data = srt.load("survey.sgt")
mesh = pg.meshtools.createParaMesh(
    data.sensors(),
    quality=34,
    paraMaxCellSize=2,
    paraDX=0.5
)
```

### 3D Mesh (Experimental)
```python
# 3D structured grid
mesh3d = pg.createGrid(
    x=np.linspace(0, 50, 26),
    y=np.linspace(0, 50, 26),
    z=np.linspace(-20, 0, 11)
)
```
