---
name: harmonica
description: |
  Gravity and magnetic data processing and forward modelling using Fatiando a Terra.
  Use when Claude needs to: (1) Compute gravity forward models (point masses, prisms,
  tesseroids), (2) Apply terrain/Bouguer corrections, (3) Grid scattered potential
  field data with equivalent sources, (4) Perform upward/downward continuation,
  (5) Calculate magnetic anomalies from magnetized bodies, (6) Apply derivative
  filters (gradients, tilt angle), (7) Process regional or local gravity surveys.
---

# Harmonica - Gravity and Magnetics

## Quick Reference

```python
import harmonica as hm
import numpy as np

# Forward model - prism gravity
prism = [-500, 500, -500, 500, -2000, -500]  # (west, east, south, north, bottom, top)
gravity = hm.prism_gravity(coordinates, prism, density=500, field='g_z')

# Terrain correction
layer = hm.prism_layer((easting, northing), surface=topo, reference=0,
                        properties={'density': 2670})
terrain_effect = layer.gravity(coordinates, field='g_z')

# Equivalent source gridding
eqs = hm.EquivalentSources(depth=10000, damping=10)
eqs.fit(coordinates, gravity_data)
grid = eqs.grid(spacing=5000, data_names=['gravity'])

# Upward continuation (requires gridded xarray)
upward = hm.upward_continuation(gravity_grid, height_displacement=1000)
```

## Key Functions

| Function | Purpose |
|----------|---------|
| `point_gravity` | Gravity from point masses |
| `prism_gravity` | Gravity from rectangular prisms |
| `tesseroid_gravity` | Gravity from spherical prisms (regional/global) |
| `prism_magnetic` | Magnetic anomaly from prisms |
| `prism_layer` | Create layer of prisms from topography |
| `EquivalentSources` | Grid scattered data with equivalent sources |
| `upward_continuation` | FFT-based upward continuation |
| `bouguer_correction` | Simple Bouguer plate correction |

## Essential Operations

### Forward Model - Rectangular Prism
```python
# Define prism: (west, east, south, north, bottom, top) in meters
prism = [-500, 500, -500, 500, -2000, -500]
density = 500  # kg/m3 density contrast

# Observation grid
x_obs, y_obs = np.meshgrid(np.linspace(-5000, 5000, 100), np.linspace(-5000, 5000, 100))
z_obs = np.zeros_like(x_obs)

# Calculate gravity (mGal). Fields: 'g_z', 'g_north', 'g_east', 'potential'
gravity = hm.prism_gravity((x_obs.ravel(), y_obs.ravel(), z_obs.ravel()),
                           prism, density, field='g_z')
```

### Terrain Correction
```python
import xarray as xr

topo = xr.open_dataarray('dem.nc')
layer = hm.prism_layer((topo.easting.values, topo.northing.values),
                       surface=topo.values, reference=0,
                       properties={'density': 2670})
terrain_effect = layer.gravity((obs_easting, obs_northing, obs_height), field='g_z')
bouguer_anomaly = free_air_anomaly - terrain_effect
```

### Equivalent Source Gridding
```python
import verde as vd

# Project to Cartesian
projection = vd.get_projection(longitude, latitude)
easting, northing = projection(longitude, latitude)

eqs = hm.EquivalentSources(depth=10000, damping=10)
eqs.fit((easting, northing, altitude), gravity_mgal)
grid = eqs.grid(spacing=5000, data_names=['gravity'])
```

### Magnetic Forward Model
```python
prism = [-500, 500, -500, 500, -2000, -500]
magnetization = hm.magnetic_vector(intensity=5.0, inclination=60, declination=10)
b_total = hm.prism_magnetic(coordinates, prism, magnetization, field='b_total')
```

### Derivative Filters
```python
dx = hm.derivative_easting(gravity_grid)
dy = hm.derivative_northing(gravity_grid)
dz = hm.derivative_upward(gravity_grid)

thg = np.sqrt(dx**2 + dy**2)  # Total horizontal gradient
tilt = np.arctan2(dz, thg)     # Tilt angle
```

## Coordinate System

Harmonica uses a **right-handed coordinate system**:
- **Easting** (x): positive east
- **Northing** (y): positive north
- **Upward** (z): positive up (heights positive, depths negative)

Units are SI: meters for distance, kg/m3 for density, mGal for gravity.

## Tips

1. **Use projected coordinates** (meters) for local surveys
2. **Use tesseroids** for regional/global scale modelling
3. **Equivalent sources** handle irregular data spacing well
4. **Choose appropriate density** (2670 kg/m3 typical for upper crust)
5. **Check sign conventions** - depths are negative z values

## References

- **[Gravity/Magnetic Corrections](references/corrections.md)** - Standard corrections and anomalies
- **[Forward Modeling](references/forward_modeling.md)** - Detailed forward modeling methods

## Scripts

- **[scripts/gravity_processing.py](scripts/gravity_processing.py)** - Process gravity survey data
