---
name: harmonica
description: Gravity and magnetic data processing and forward modelling. Compute terrain corrections, upward continuation, equivalent sources, and potential field inversions.
---

# Harmonica - Gravity and Magnetics

Help users process and model gravity and magnetic data.

## Installation

```bash
pip install harmonica
```

## Core Concepts

### What Harmonica Does
- Forward modelling of gravity and magnetic fields
- Terrain corrections
- Upward/downward continuation
- Equivalent source processing
- Data transformations (derivatives, reduction to pole)

### Key Functions
| Function | Purpose |
|----------|---------|
| `point_gravity` | Gravity from point masses |
| `prism_gravity` | Gravity from rectangular prisms |
| `tesseroid_gravity` | Gravity from spherical prisms |
| `EquivalentSources` | Gridding with equivalent sources |

## Common Workflows

### 1. Load Gravity Data
```python
import harmonica as hm
import pandas as pd

# Load sample South Africa gravity data
data = hm.datasets.fetch_south_africa_gravity()

# Access coordinates and gravity
longitude = data.longitude
latitude = data.latitude
gravity = data.gravity_mgal

print(f"Data range: {gravity.min():.1f} to {gravity.max():.1f} mGal")
```

### 2. Forward Model - Point Masses
```python
import harmonica as hm
import numpy as np

# Define point masses
# Coordinates: easting, northing, upward (positive up)
points = [
    [0, 0, -1000],      # Mass at 1 km depth
    [5000, 5000, -500]  # Mass at 500 m depth
]
masses = [1e12, 5e11]  # kg

# Observation points (surface grid)
x = np.linspace(-10000, 10000, 100)
y = np.linspace(-10000, 10000, 100)
x_obs, y_obs = np.meshgrid(x, y)
z_obs = np.zeros_like(x_obs)  # Surface

# Calculate gravity
coords = (points[0][0], points[0][1], points[0][2])
gravity = hm.point_gravity(
    (x_obs.ravel(), y_obs.ravel(), z_obs.ravel()),
    coords,
    masses[0],
    field='g_z'  # Vertical component
)

# Reshape to grid
gravity_grid = gravity.reshape(x_obs.shape)
```

### 3. Forward Model - Rectangular Prisms
```python
import harmonica as hm
import numpy as np

# Define prism: (west, east, south, north, bottom, top)
prism = [-500, 500, -500, 500, -2000, -500]  # meters
density = 500  # kg/m³ (density contrast)

# Observation grid
x = np.linspace(-5000, 5000, 100)
y = np.linspace(-5000, 5000, 100)
x_obs, y_obs = np.meshgrid(x, y)
z_obs = np.zeros_like(x_obs)

# Calculate gravity
gravity = hm.prism_gravity(
    (x_obs.ravel(), y_obs.ravel(), z_obs.ravel()),
    prism,
    density,
    field='g_z'  # 'g_z', 'g_north', 'g_east', or 'potential'
)

import matplotlib.pyplot as plt
plt.contourf(x_obs, y_obs, gravity.reshape(x_obs.shape), levels=20)
plt.colorbar(label='Gravity (mGal)')
plt.title('Gravity from Rectangular Prism')
plt.xlabel('Easting (m)')
plt.ylabel('Northing (m)')
plt.show()
```

### 4. Terrain Correction
```python
import harmonica as hm
import xarray as xr

# Load DEM (xarray DataArray with 'easting', 'northing' coords)
topography = xr.open_dataarray('dem.nc')

# Observation points
coordinates = (data.easting, data.northing, data.height)

# Terrain correction using prisms
terrain_effect = hm.prism_layer(
    topography,
    density=2670,  # Rock density kg/m³
    reference=0    # Reference surface
).gravity(
    coordinates,
    field='g_z'
)

# Complete Bouguer anomaly
bouguer_anomaly = data.gravity - terrain_effect
```

### 5. Equivalent Source Gridding
```python
import harmonica as hm
import verde as vd

# Load scattered gravity data
data = hm.datasets.fetch_south_africa_gravity()

# Project to Cartesian
projection = vd.get_projection(data.longitude, data.latitude)
easting, northing = projection(data.longitude, data.latitude)
coordinates = (easting, northing, data.altitude)

# Create equivalent sources
eqs = hm.EquivalentSources(
    depth=10000,       # Source depth (m)
    damping=10         # Regularization
)

# Fit to data
eqs.fit(coordinates, data.gravity_mgal)

# Grid the data
grid = eqs.grid(
    spacing=5000,
    data_names=['gravity']
)

# Plot gridded result
grid.gravity.plot()
```

### 6. Upward Continuation
```python
import harmonica as hm
import xarray as xr

# Load gridded gravity data
gravity_grid = xr.open_dataarray('gravity.nc')

# Upward continue using FFT
# Data must be on regular grid
upward = hm.upward_continuation(
    gravity_grid,
    height_displacement=1000  # Continue 1000 m upward
)

upward.plot()
```

### 7. Spherical Prisms (Tesseroids)
```python
import harmonica as hm
import numpy as np

# Define tesseroid (for global/regional data)
# (west, east, south, north, bottom, top) in degrees/meters
tesseroid = (-10, 10, -10, 10, -50000, -5000)
density = 500  # kg/m³

# Observation points (longitude, latitude, height)
lon = np.linspace(-20, 20, 50)
lat = np.linspace(-20, 20, 50)
lon_obs, lat_obs = np.meshgrid(lon, lat)
height = np.full_like(lon_obs, 10000)  # 10 km altitude

# Calculate gravity
gravity = hm.tesseroid_gravity(
    (lon_obs.ravel(), lat_obs.ravel(), height.ravel()),
    tesseroid,
    density,
    field='g_z'
)
```

### 8. Magnetic Forward Modelling
```python
import harmonica as hm
import numpy as np

# Define magnetized prism
prism = [-500, 500, -500, 500, -2000, -500]

# Magnetization (A/m) - direction from inclination/declination
magnetization = hm.magnetic_vector(
    intensity=5.0,      # A/m
    inclination=60,     # degrees
    declination=10      # degrees
)

# Observation grid
x = np.linspace(-5000, 5000, 100)
y = np.linspace(-5000, 5000, 100)
x_obs, y_obs = np.meshgrid(x, y)
z_obs = np.zeros_like(x_obs)

# Calculate magnetic anomaly
b_total = hm.prism_magnetic(
    (x_obs.ravel(), y_obs.ravel(), z_obs.ravel()),
    prism,
    magnetization,
    field='b_total'  # Total field anomaly
)
```

### 9. Bouguer Correction
```python
import harmonica as hm

# Simple Bouguer plate correction
bouguer_correction = hm.bouguer_correction(
    data.height,           # Observation height (m)
    density=2670           # Assumed density kg/m³
)

# Free-air anomaly to Bouguer
bouguer_anomaly = free_air_anomaly - bouguer_correction
```

### 10. Normal Gravity
```python
import harmonica as hm
import boule as bl

# Use WGS84 ellipsoid
ellipsoid = bl.WGS84

# Calculate normal gravity at observation points
normal_gravity = ellipsoid.normal_gravity(
    latitude,
    height
)

# Calculate gravity disturbance
disturbance = observed_gravity - normal_gravity
```

### 11. Derivative Filters
```python
import harmonica as hm
import xarray as xr

# Load gridded data
gravity_grid = xr.open_dataarray('gravity.nc')

# Horizontal derivatives (edge detection)
dx = hm.derivative_easting(gravity_grid)
dy = hm.derivative_northing(gravity_grid)

# Vertical derivative
dz = hm.derivative_upward(gravity_grid)

# Total horizontal gradient
thg = np.sqrt(dx**2 + dy**2)

# Tilt angle
tilt = np.arctan2(dz, thg)
```

### 12. Layer of Prisms from Topography
```python
import harmonica as hm
import xarray as xr

# Load topography grid
topo = xr.open_dataarray('topography.nc')

# Create layer of prisms representing terrain
layer = hm.prism_layer(
    (topo.easting.values, topo.northing.values),
    surface=topo.values,
    reference=0,  # Reference level
    properties={'density': 2670}
)

# Forward model gravity effect
coordinates = (obs_easting, obs_northing, obs_height)
terrain_gravity = layer.gravity(coordinates, field='g_z')
```

## Gravity Corrections Summary

| Correction | Purpose |
|------------|---------|
| Free-air | Altitude effect |
| Bouguer | Infinite slab |
| Terrain | Topography variations |
| Isostatic | Crustal thickness variations |

## Tips

1. **Use projected coordinates** for local surveys (meters)
2. **Use tesseroids** for regional/global modelling
3. **Equivalent sources** handle irregular data well
4. **Choose appropriate density** for terrain corrections
5. **Check units** - Harmonica uses SI (m, kg, mGal)

## Resources

- Documentation: https://www.fatiando.org/harmonica/
- GitHub: https://github.com/fatiando/harmonica
- Tutorials: https://www.fatiando.org/harmonica/latest/tutorials/
- Gallery: https://www.fatiando.org/harmonica/latest/gallery/
