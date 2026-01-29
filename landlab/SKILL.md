---
name: landlab
description: |
  Landscape evolution and surface process modelling in Python. Build 2D numerical
  models for erosion, hydrology, soil transport, and geomorphology. Use when Claude
  needs to: (1) Model landscape evolution over time, (2) Simulate river/stream erosion,
  (3) Route water flow across terrain, (4) Model hillslope diffusion processes,
  (5) Simulate weathering and soil production, (6) Analyze drainage networks,
  (7) Combine multiple geomorphic processes, (8) Load/save DEM data for modeling.
---

# Landlab - Surface Process Modelling

## Quick Reference

```python
from landlab import RasterModelGrid
from landlab.components import FlowAccumulator, StreamPowerEroder
import numpy as np

# Create grid
grid = RasterModelGrid((100, 100), xy_spacing=10.0)
z = grid.add_zeros('topographic__elevation', at='node')
z += np.random.rand(grid.number_of_nodes) * 0.1

# Set boundaries (open bottom edge)
grid.set_closed_boundaries_at_grid_edges(True, True, True, False)

# Create and run components
fa = FlowAccumulator(grid, flow_director='D8')
sp = StreamPowerEroder(grid, K_sp=1e-5)

for _ in range(100):
    fa.run_one_step()
    sp.run_one_step(dt=1000)
    z[grid.core_nodes] += 0.001 * 1000  # Uplift

grid.imshow('topographic__elevation', cmap='terrain')
```

## Grid Types

| Grid | Use Case |
|------|----------|
| `RasterModelGrid` | Regular rectangular grids (most common) |
| `HexModelGrid` | Hexagonal grids (isotropic flow) |
| `VoronoiDelaunayGrid` | Irregular point distributions |
| `NetworkModelGrid` | Channel networks only |

## Key Concepts

### Fields and Boundaries
```python
# Fields: data stored at grid elements (nodes, links, cells)
z = grid.add_zeros('topographic__elevation', at='node')
grid.at_node['drainage_area']  # Access existing field

# Boundaries: close all edges except outlet
grid.set_closed_boundaries_at_grid_edges(True, True, True, False)
z[grid.core_nodes] += uplift * dt  # Core nodes exclude boundaries
```

## Essential Operations

### Flow Routing
```python
from landlab.components import FlowAccumulator

fa = FlowAccumulator(grid, flow_director='D8')  # or 'Steepest', 'MFD'
fa.run_one_step()
drainage_area = grid.at_node['drainage_area']
```

### Stream Power Erosion
```python
from landlab.components import StreamPowerEroder

sp = StreamPowerEroder(grid, K_sp=1e-5, m_sp=0.5, n_sp=1.0)
sp.run_one_step(dt=1000)  # dt in years
```

### Hillslope Diffusion
```python
from landlab.components import LinearDiffuser

ld = LinearDiffuser(grid, linear_diffusivity=0.01)  # m^2/yr
ld.run_one_step(dt=100)
```

### Load/Save DEM Data
```python
from landlab.io import read_esri_ascii, write_esri_ascii
from landlab.io.netcdf import read_netcdf, write_netcdf

grid, z = read_esri_ascii('dem.asc', name='topographic__elevation')
write_esri_ascii('output.asc', grid, names='topographic__elevation')
write_netcdf('output.nc', grid)  # Save all fields
```

## Multi-Component Model

```python
from landlab import RasterModelGrid
from landlab.components import FlowAccumulator, StreamPowerEroder, LinearDiffuser

grid = RasterModelGrid((100, 100), xy_spacing=100.0)
z = grid.add_zeros('topographic__elevation', at='node')
z += grid.node_y / 1000 + np.random.rand(grid.number_of_nodes) * 0.1
grid.set_closed_boundaries_at_grid_edges(True, True, True, False)

fa = FlowAccumulator(grid, flow_director='D8')
sp = StreamPowerEroder(grid, K_sp=1e-5)
ld = LinearDiffuser(grid, linear_diffusivity=0.01)

dt, uplift_rate = 1000, 0.001
for _ in range(500):
    fa.run_one_step()
    sp.run_one_step(dt)
    ld.run_one_step(dt)
    z[grid.core_nodes] += uplift_rate * dt
```

## Tips

1. **Set boundaries first** - before adding components
2. **Use core_nodes** - excludes boundary nodes for operations
3. **Check field names** - components expect specific names (e.g., 'topographic__elevation')
4. **Start simple** - add components incrementally and verify each

## References

- **[Components Reference](references/components.md)** - Available components by category
- **[Grids Reference](references/grids.md)** - Grid types and configuration

## Scripts

- **[scripts/erosion_model.py](scripts/erosion_model.py)** - Basic erosion model template
