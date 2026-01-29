# Landlab Grids Reference

## Table of Contents
- [Grid Types Overview](#grid-types-overview)
- [RasterModelGrid](#rastermodelgrid)
- [HexModelGrid](#hexmodelgrid)
- [VoronoiDelaunayGrid](#voronoidelaunaygrid)
- [NetworkModelGrid](#networkmodelgrid)
- [Grid Elements](#grid-elements)
- [Boundary Conditions](#boundary-conditions)
- [Field Operations](#field-operations)

## Grid Types Overview

| Grid Type | Best For | Pros | Cons |
|-----------|----------|------|------|
| `RasterModelGrid` | General use, DEMs | Fast, simple, compatible with raster data | Anisotropic flow directions |
| `HexModelGrid` | Isotropic processes | More uniform neighbor distances | Cannot load standard DEMs |
| `VoronoiDelaunayGrid` | Variable resolution | Adaptive resolution | Complex setup |
| `NetworkModelGrid` | Channel networks | Efficient for 1D channels | No 2D surface processes |

## RasterModelGrid

Most common grid type for landscape evolution modeling.

### Creation
```python
from landlab import RasterModelGrid

# Basic grid (rows, cols)
grid = RasterModelGrid((100, 100), xy_spacing=10.0)

# Non-square cells
grid = RasterModelGrid((100, 200), xy_spacing=(10.0, 5.0))

# With origin offset
grid = RasterModelGrid((100, 100), xy_spacing=10.0, xy_of_lower_left=(500000, 4000000))
```

### Properties
```python
grid.shape                    # (nrows, ncols)
grid.number_of_nodes          # Total nodes
grid.number_of_cells          # Interior cells only
grid.number_of_links          # Connections between nodes
grid.dx, grid.dy              # Cell spacing

grid.node_x                   # X coordinates of all nodes
grid.node_y                   # Y coordinates of all nodes
grid.x_of_node                # Same as node_x
grid.y_of_node                # Same as node_y
```

### Node Subsets
```python
grid.core_nodes               # Interior nodes (not boundaries)
grid.boundary_nodes           # All boundary nodes
grid.open_boundary_nodes      # Open boundary nodes
grid.closed_boundary_nodes    # Closed boundary nodes

grid.nodes_at_top_edge        # Top row nodes
grid.nodes_at_bottom_edge     # Bottom row nodes
grid.nodes_at_left_edge       # Left column nodes
grid.nodes_at_right_edge      # Right column nodes
```

## HexModelGrid

Hexagonal grids with more isotropic flow properties.

### Creation
```python
from landlab import HexModelGrid

# Horizontal hex orientation
grid = HexModelGrid((50, 50), spacing=10.0, node_layout='hex')

# Rectangular boundary shape
grid = HexModelGrid((50, 50), spacing=10.0, shape='rect')
```

### Properties
```python
grid.number_of_nodes
grid.number_of_links          # 6 per interior node
grid.spacing                  # Distance between nodes
```

## VoronoiDelaunayGrid

Irregular grids from point distributions.

### Creation
```python
from landlab import VoronoiDelaunayGrid
import numpy as np

# From random points
np.random.seed(42)
x = np.random.rand(100) * 1000
y = np.random.rand(100) * 1000
grid = VoronoiDelaunayGrid(x, y)

# With boundary points
x_boundary = [0, 1000, 1000, 0]
y_boundary = [0, 0, 1000, 1000]
# Add boundary to x, y arrays
```

### Use Cases
- Variable resolution (dense near features)
- Matching irregular measurement locations
- Adaptive mesh refinement

## NetworkModelGrid

For 1D channel network modeling.

### Creation
```python
from landlab import NetworkModelGrid

# Define network topology
y_of_node = [0, 100, 200, 200, 300]
x_of_node = [0, 0, -50, 50, 0]
nodes_at_link = [(0, 1), (1, 2), (1, 3), (2, 4), (3, 4)]

grid = NetworkModelGrid((y_of_node, x_of_node), links=nodes_at_link)
```

### Properties
```python
grid.number_of_nodes          # Network nodes
grid.number_of_links          # Channel segments
grid.length_of_link           # Segment lengths
```

## Grid Elements

Landlab grids have four element types:

| Element | Description | Count Property |
|---------|-------------|----------------|
| **Nodes** | Points where values are stored | `number_of_nodes` |
| **Links** | Connections between nodes | `number_of_links` |
| **Cells** | Areas around interior nodes | `number_of_cells` |
| **Faces** | Boundaries between cells | `number_of_faces` |

### Element Relationships
```python
# Nodes around a cell
grid.nodes_at_cell[cell_id]

# Links connected to a node
grid.links_at_node[node_id]

# Nodes at ends of a link
grid.nodes_at_link[link_id]

# Adjacent nodes
grid.adjacent_nodes_at_node[node_id]
```

## Boundary Conditions

### Setting Boundaries
```python
# Close all edges except one (create outlet)
grid.set_closed_boundaries_at_grid_edges(
    right_is_closed=True,
    top_is_closed=True,
    left_is_closed=True,
    bottom_is_closed=False  # Open outlet
)

# Set specific nodes
grid.status_at_node[node_ids] = grid.BC_NODE_IS_CLOSED
grid.status_at_node[outlet_id] = grid.BC_NODE_IS_FIXED_VALUE
```

### Boundary Status Values
```python
grid.BC_NODE_IS_CORE           # 0: Interior node
grid.BC_NODE_IS_FIXED_VALUE    # 1: Fixed value (open)
grid.BC_NODE_IS_FIXED_GRADIENT # 2: Fixed gradient
grid.BC_NODE_IS_LOOPED         # 3: Periodic boundary
grid.BC_NODE_IS_CLOSED         # 4: No flux
```

### Check Boundaries
```python
# Boolean arrays
grid.node_is_boundary(node_id)
grid.core_nodes               # All interior nodes
grid.open_boundary_nodes      # All open boundary nodes
```

## Field Operations

### Creating Fields
```python
# Add zeros
z = grid.add_zeros('topographic__elevation', at='node')

# Add with initial value
z = grid.add_ones('soil__depth', at='node') * 0.5

# Add existing array
z = grid.add_field('topographic__elevation', elevation_array, at='node')

# Add empty (uninitialized)
z = grid.add_empty('temp_field', at='node')
```

### Accessing Fields
```python
# Get field array
z = grid.at_node['topographic__elevation']

# Check if field exists
'drainage_area' in grid.at_node

# List all fields
grid.at_node.keys()
grid.at_link.keys()
grid.at_cell.keys()
```

### Field Locations
```python
grid.at_node['field_name']    # At grid nodes
grid.at_link['field_name']    # At links between nodes
grid.at_cell['field_name']    # At cell centers
grid.at_face['field_name']    # At faces between cells
```

### Removing Fields
```python
grid.delete_field('node', 'field_name')
# or
del grid.at_node['field_name']
```

## Visualization

### Quick Plot
```python
import matplotlib.pyplot as plt

# Plot field
grid.imshow('topographic__elevation', cmap='terrain')
plt.colorbar(label='Elevation (m)')
plt.show()
```

### Custom Plot
```python
import matplotlib.pyplot as plt
from landlab.plot import imshow_grid

fig, ax = plt.subplots(figsize=(10, 8))
imshow_grid(
    grid,
    'topographic__elevation',
    cmap='terrain',
    colorbar_label='Elevation (m)',
    plot_name='Topography'
)
plt.savefig('topography.png', dpi=150)
```

### 3D Visualization
```python
from landlab.plot import plot_surface

plot_surface(grid, 'topographic__elevation')
```

## Loading/Saving Grids

### ESRI ASCII
```python
from landlab.io import read_esri_ascii, write_esri_ascii

# Load
grid, z = read_esri_ascii('dem.asc', name='topographic__elevation')

# Save
write_esri_ascii('output.asc', grid, names='topographic__elevation')
```

### NetCDF
```python
from landlab.io.netcdf import read_netcdf, write_netcdf

# Load
grid = read_netcdf('dem.nc')

# Save (includes all fields)
write_netcdf('output.nc', grid)
```

### GeoTIFF (via rasterio)
```python
import numpy as np
import rasterio
from landlab import RasterModelGrid

# Load GeoTIFF
with rasterio.open('dem.tif') as src:
    data = src.read(1)
    transform = src.transform
    dx = transform[0]

# Create grid
grid = RasterModelGrid(data.shape, xy_spacing=dx)
z = grid.add_field('topographic__elevation', data.flatten(), at='node')
```
