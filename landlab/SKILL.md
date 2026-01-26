---
name: landlab
description: Landscape evolution and surface process modelling. Build 2D numerical models for erosion, hydrology, soil transport, and geomorphology.
---

# Landlab - Surface Process Modelling

Help users build landscape evolution models and simulate surface processes.

## Installation

```bash
pip install landlab
```

## Core Concepts

### Grid Types
| Grid | Use Case |
|------|----------|
| `RasterModelGrid` | Regular rectangular grids |
| `HexModelGrid` | Hexagonal grids |
| `VoronoiDelaunayGrid` | Irregular point distributions |
| `NetworkModelGrid` | Channel networks |

### Components
Landlab uses modular components that can be combined:
- Erosion models
- Flow routing
- Weathering
- Sediment transport
- Precipitation

### Fields
Data is stored as "fields" attached to grid elements (nodes, links, cells).

## Common Workflows

### 1. Create a Basic Grid
```python
from landlab import RasterModelGrid
import numpy as np

# Create 100x100 grid with 10m spacing
grid = RasterModelGrid((100, 100), xy_spacing=10.0)

# Add topography field
z = grid.add_zeros('topography', at='node')

# Add random initial topography
z += np.random.rand(grid.number_of_nodes) * 0.1

# Set boundary conditions
grid.set_closed_boundaries_at_grid_edges(
    right_is_closed=False,  # Open right edge
    top_is_closed=True,
    left_is_closed=True,
    bottom_is_closed=True
)

print(f"Grid shape: {grid.shape}")
print(f"Number of nodes: {grid.number_of_nodes}")
```

### 2. Simple Diffusion Model
```python
from landlab import RasterModelGrid
from landlab.components import LinearDiffuser
import numpy as np

# Create grid
grid = RasterModelGrid((50, 50), xy_spacing=10.0)
z = grid.add_zeros('topography', at='node')

# Initial hill
z[grid.node_y > 250] = 100.0

# Set boundaries
grid.set_closed_boundaries_at_grid_edges(True, True, True, False)

# Create diffuser component
diffuser = LinearDiffuser(
    grid,
    linear_diffusivity=0.01  # m²/yr
)

# Run for 10000 years
dt = 100  # years
for t in range(100):
    diffuser.run_one_step(dt)

# Plot result
import matplotlib.pyplot as plt
grid.imshow('topography')
plt.title('Diffused Topography')
plt.show()
```

### 3. Stream Power Erosion
```python
from landlab import RasterModelGrid
from landlab.components import (
    FlowAccumulator,
    StreamPowerEroder
)
import numpy as np

# Create grid with initial topography
grid = RasterModelGrid((100, 100), xy_spacing=100.0)
z = grid.add_zeros('topography', at='node')
z += grid.node_y / 1000 + np.random.rand(grid.number_of_nodes) * 0.1

# Set outlet at bottom edge
grid.set_closed_boundaries_at_grid_edges(True, True, True, False)

# Create components
fa = FlowAccumulator(grid, flow_director='D8')
sp = StreamPowerEroder(
    grid,
    K_sp=1e-5,      # Erodibility
    m_sp=0.5,       # Drainage area exponent
    n_sp=1.0        # Slope exponent
)

# Run model
dt = 1000  # years
for i in range(200):
    fa.run_one_step()
    sp.run_one_step(dt)

    # Apply uplift
    z[grid.core_nodes] += 0.001 * dt  # 1 mm/yr

grid.imshow('topography', cmap='terrain')
```

### 4. Flow Routing
```python
from landlab import RasterModelGrid
from landlab.components import FlowAccumulator
import numpy as np

# Create grid
grid = RasterModelGrid((50, 50), xy_spacing=10.0)
z = grid.add_field('topography',
                   grid.node_y + np.random.rand(grid.number_of_nodes),
                   at='node')

# Set boundaries
grid.set_closed_boundaries_at_grid_edges(True, True, True, False)

# Route flow
fa = FlowAccumulator(
    grid,
    flow_director='D8',  # or 'Steepest', 'MFD'
    runoff_rate=1.0      # m/yr
)
fa.run_one_step()

# Access results
drainage_area = grid.at_node['drainage_area']
flow_receiver = grid.at_node['flow__receiver_node']

# Plot drainage area
import matplotlib.pyplot as plt
grid.imshow('drainage_area', cmap='Blues')
plt.title('Drainage Area')
plt.show()
```

### 5. Weathering and Soil Production
```python
from landlab import RasterModelGrid
from landlab.components import ExponentialWeatherer
import numpy as np

# Create grid
grid = RasterModelGrid((50, 50), xy_spacing=10.0)
z = grid.add_zeros('topography', at='node')
soil = grid.add_zeros('soil__depth', at='node')
soil += 0.5  # Initial 0.5m soil

# Weathering component
weatherer = ExponentialWeatherer(
    grid,
    max_soil_production_rate=0.001,  # m/yr
    soil_production_decay_depth=0.5   # m
)

# Run
dt = 100  # years
for t in range(100):
    weatherer.run_one_step(dt)

print(f"Soil depth range: {soil.min():.2f} - {soil.max():.2f} m")
```

### 6. Load DEM Data
```python
from landlab import RasterModelGrid
from landlab.io import read_esri_ascii
import numpy as np

# Load ESRI ASCII grid
grid, z = read_esri_ascii('dem.asc', name='topography')

# Or from NetCDF
from landlab.io.netcdf import read_netcdf
grid = read_netcdf('dem.nc')

# Access topography
z = grid.at_node['topography']
```

### 7. Save Results
```python
from landlab import RasterModelGrid
from landlab.io import write_esri_ascii
from landlab.io.netcdf import write_netcdf
import numpy as np

# After running model
grid = RasterModelGrid((50, 50), xy_spacing=10.0)
z = grid.add_field('topography', np.random.rand(grid.number_of_nodes), at='node')

# Save as ESRI ASCII
write_esri_ascii('output.asc', grid, names='topography')

# Save as NetCDF
write_netcdf('output.nc', grid)
```

### 8. Precipitation and Runoff
```python
from landlab import RasterModelGrid
from landlab.components import (
    PrecipitationDistribution,
    FlowAccumulator
)

# Create grid
grid = RasterModelGrid((100, 100), xy_spacing=100.0)
z = grid.add_zeros('topography', at='node')
z += grid.node_y / 100

# Precipitation component
precip = PrecipitationDistribution(
    grid,
    mean_storm_duration=2.0,      # hours
    mean_interstorm_duration=24.0, # hours
    mean_storm_depth=0.01          # m
)

# Run with variable precipitation
fa = FlowAccumulator(grid)

for i in range(100):
    precip.update()
    intensity = precip.intensity
    fa.run_one_step()
```

### 9. Multi-Component Model
```python
from landlab import RasterModelGrid
from landlab.components import (
    FlowAccumulator,
    StreamPowerEroder,
    LinearDiffuser
)
import numpy as np

# Create grid
grid = RasterModelGrid((100, 100), xy_spacing=100.0)
z = grid.add_zeros('topography', at='node')
z += grid.node_y / 1000 + np.random.rand(grid.number_of_nodes) * 0.1

grid.set_closed_boundaries_at_grid_edges(True, True, True, False)

# Initialize components
fa = FlowAccumulator(grid, flow_director='D8')
sp = StreamPowerEroder(grid, K_sp=1e-5, m_sp=0.5, n_sp=1.0)
ld = LinearDiffuser(grid, linear_diffusivity=0.01)

# Time stepping
dt = 1000
uplift_rate = 0.001  # m/yr

for i in range(500):
    # Route flow
    fa.run_one_step()

    # Erode by rivers
    sp.run_one_step(dt)

    # Hillslope diffusion
    ld.run_one_step(dt)

    # Apply uplift to core nodes
    z[grid.core_nodes] += uplift_rate * dt

grid.imshow('topography', cmap='terrain')
```

### 10. Extract Channel Profile
```python
from landlab import RasterModelGrid
from landlab.components import (
    FlowAccumulator,
    ChannelProfiler
)

# After running model
fa = FlowAccumulator(grid, flow_director='D8')
fa.run_one_step()

# Create profiler
profiler = ChannelProfiler(
    grid,
    number_of_watersheds=1,
    minimum_channel_threshold=1e6  # m² drainage area
)
profiler.run_one_step()

# Plot profile
import matplotlib.pyplot as plt
for i, (segment, d) in enumerate(profiler.data_structure.items()):
    for j, ids in d.items():
        plt.plot(grid.at_node['drainage_area'][ids],
                 z[ids], 'k-')
plt.xlabel('Drainage Area (m²)')
plt.ylabel('Elevation (m)')
plt.xscale('log')
plt.show()
```

## Available Components

| Category | Components |
|----------|------------|
| Flow | FlowAccumulator, FlowDirectorD8, FlowDirectorSteepest |
| Erosion | StreamPowerEroder, FastscapeEroder, SedimentPulser |
| Diffusion | LinearDiffuser, PerronNLDiffuse |
| Weathering | ExponentialWeatherer, DepthDependentDiffuser |
| Hydrology | KinwaveOverlandFlow, GroundwaterDupuitPercolator |

## Tips

1. **Set boundaries first** before adding components
2. **Use core_nodes** for operations (excludes boundaries)
3. **Check component requirements** - some need specific fields
4. **Start simple** - add components incrementally
5. **Monitor conservation** - check mass balance

## Resources

- Documentation: https://landlab.readthedocs.io/
- GitHub: https://github.com/landlab/landlab
- Tutorials: https://landlab.readthedocs.io/en/latest/user_guide/tutorials.html
- Component list: https://landlab.readthedocs.io/en/latest/reference/components/index.html
