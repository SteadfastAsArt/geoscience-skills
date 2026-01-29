# Forward Modeling Methods

## Table of Contents
- [Point Sources](#point-sources)
- [Rectangular Prisms](#rectangular-prisms)
- [Tesseroids](#tesseroids)
- [Prism Layers](#prism-layers)
- [Magnetic Modeling](#magnetic-modeling)
- [Computational Considerations](#computational-considerations)

## Point Sources

Simplest model: gravity from point masses.

```python
import harmonica as hm
import numpy as np

# Single point mass
# Coordinates: (easting, northing, upward)
point = (0, 0, -1000)  # 1 km depth
mass = 1e12  # kg

# Observation grid
x = np.linspace(-5000, 5000, 50)
y = np.linspace(-5000, 5000, 50)
xx, yy = np.meshgrid(x, y)
zz = np.zeros_like(xx)  # Surface

# Calculate gravity
gravity = hm.point_gravity(
    (xx.ravel(), yy.ravel(), zz.ravel()),
    point,
    mass,
    field='g_z'  # Options: 'g_z', 'g_north', 'g_east', 'potential'
)
```

### Multiple Point Sources

```python
# Array of point sources
points = np.array([
    [0, 0, -1000],
    [2000, 0, -1500],
    [0, 2000, -800]
])
masses = np.array([1e12, 5e11, 8e11])

# Calculate for each source and sum
total_gravity = np.zeros(xx.size)
for i in range(len(masses)):
    g = hm.point_gravity(
        (xx.ravel(), yy.ravel(), zz.ravel()),
        tuple(points[i]),
        masses[i],
        field='g_z'
    )
    total_gravity += g
```

## Rectangular Prisms

Most common model for local surveys. Analytical solution.

```python
import harmonica as hm

# Prism definition: (west, east, south, north, bottom, top)
# All coordinates in meters
prism = [-500, 500, -500, 500, -2000, -500]
density = 500  # kg/m3 (density contrast)

# Calculate gravity
gravity = hm.prism_gravity(
    coordinates,
    prism,
    density,
    field='g_z'
)
```

### Multiple Prisms

```python
# Define multiple prisms
prisms = [
    [-1000, 0, -500, 500, -2000, -500],    # Prism 1
    [0, 1000, -500, 500, -1500, -300],     # Prism 2
    [-500, 500, -1500, -500, -3000, -1000] # Prism 3
]
densities = [500, -200, 300]  # Different density contrasts

# Sum contributions
total_gravity = np.zeros(coordinates[0].size)
for prism, density in zip(prisms, densities):
    g = hm.prism_gravity(coordinates, prism, density, field='g_z')
    total_gravity += g
```

### Available Fields

| Field | Description |
|-------|-------------|
| `g_z` | Vertical gravity component (mGal) |
| `g_north` | North component (mGal) |
| `g_east` | East component (mGal) |
| `potential` | Gravitational potential (m2/s2) |

## Tesseroids

Spherical prisms for regional/global scale. Account for Earth curvature.

```python
import harmonica as hm
import numpy as np

# Tesseroid definition: (west, east, south, north, bottom, top)
# Horizontal in degrees, vertical in meters
tesseroid = (-5, 5, -5, 5, -50000, 0)  # 10x10 degree, 50 km thick
density = 500  # kg/m3

# Observation points (longitude, latitude, height)
lon = np.linspace(-10, 10, 50)
lat = np.linspace(-10, 10, 50)
lon_obs, lat_obs = np.meshgrid(lon, lat)
height = np.full_like(lon_obs, 50000)  # 50 km altitude

gravity = hm.tesseroid_gravity(
    (lon_obs.ravel(), lat_obs.ravel(), height.ravel()),
    tesseroid,
    density,
    field='g_z'
)
```

### When to Use Tesseroids

| Scale | Model | Notes |
|-------|-------|-------|
| < 100 km | Prisms | Earth curvature negligible |
| 100-500 km | Either | Consider curvature effects |
| > 500 km | Tesseroids | Curvature essential |

## Prism Layers

Create layer of prisms from topography or surface.

```python
import harmonica as hm
import xarray as xr
import numpy as np

# Create topography grid
easting = np.linspace(0, 10000, 100)
northing = np.linspace(0, 10000, 100)
ee, nn = np.meshgrid(easting, northing)

# Synthetic topography
topo = 500 * np.sin(ee/2000) * np.cos(nn/2000)

# Create prism layer
layer = hm.prism_layer(
    (easting, northing),
    surface=topo,
    reference=0,       # Reference level
    properties={'density': 2670}
)

# Calculate gravity at observation points
obs_coords = (obs_easting, obs_northing, obs_height)
gravity = layer.gravity(obs_coords, field='g_z')
```

### Layer with Variable Density

```python
# Create density grid (same shape as surface)
density_grid = 2670 + 100 * np.random.randn(*topo.shape)

layer = hm.prism_layer(
    (easting, northing),
    surface=topo,
    reference=0,
    properties={'density': density_grid}
)
```

### Two-Surface Layer

```python
# Layer between two surfaces (e.g., sediment layer)
layer = hm.prism_layer(
    (easting, northing),
    surface=top_surface,
    reference=bottom_surface,  # Can be array
    properties={'density': sediment_density}
)
```

## Magnetic Modeling

### Prism Magnetic Anomaly

```python
import harmonica as hm

# Magnetized prism
prism = [-500, 500, -500, 500, -2000, -500]

# Define magnetization vector
magnetization = hm.magnetic_vector(
    intensity=5.0,      # A/m (susceptibility * field strength)
    inclination=60,     # degrees from horizontal
    declination=10      # degrees from north
)

# Calculate magnetic field
b_total = hm.prism_magnetic(
    coordinates,
    prism,
    magnetization,
    field='b_total'  # Total field anomaly
)
```

### Available Magnetic Fields

| Field | Description |
|-------|-------------|
| `b_total` | Total field anomaly (nT) |
| `b_north` | North component (nT) |
| `b_east` | East component (nT) |
| `b_down` | Down component (nT) |

### Induced vs Remanent Magnetization

```python
# Induced magnetization (parallel to ambient field)
susceptibility = 0.01  # SI units
ambient_field = 50000  # nT
induced_intensity = susceptibility * ambient_field / 1e9 * 1e6  # A/m

induced_mag = hm.magnetic_vector(
    intensity=induced_intensity,
    inclination=ambient_inclination,
    declination=ambient_declination
)

# Remanent magnetization (fixed direction)
remanent_mag = hm.magnetic_vector(
    intensity=2.0,       # A/m
    inclination=45,      # Ancient field direction
    declination=-30
)

# Total magnetization
total_mag = induced_mag + remanent_mag
```

## Computational Considerations

### Memory Usage

```python
# Number of observations
n_obs = len(coordinates[0])

# Number of sources (prisms, points, etc.)
n_src = len(prisms)

# Memory scales as n_obs * n_src for direct calculation
# Use chunking for large problems

chunk_size = 10000
results = []
for i in range(0, n_obs, chunk_size):
    chunk_coords = (
        coordinates[0][i:i+chunk_size],
        coordinates[1][i:i+chunk_size],
        coordinates[2][i:i+chunk_size]
    )
    g = hm.prism_gravity(chunk_coords, prisms, densities, field='g_z')
    results.append(g)
gravity = np.concatenate(results)
```

### Parallel Computation

```python
# Harmonica uses numba for JIT compilation
# First call compiles, subsequent calls are faster

# For very large problems, consider:
# 1. Reduce grid resolution
# 2. Use equivalent sources for interpolation
# 3. Use adaptive algorithms (tesseroids)
```

### Accuracy vs Speed

| Method | Speed | Accuracy | Best For |
|--------|-------|----------|----------|
| Point sources | Fast | Low (far field) | Quick estimates |
| Prisms | Medium | High | Local surveys |
| Tesseroids | Slow | High | Regional/global |
| Equivalent sources | Fast (after fit) | Medium | Gridding |

### Equivalent Sources for Efficiency

```python
import harmonica as hm

# Fit equivalent sources once
eqs = hm.EquivalentSources(depth=10000, damping=10)
eqs.fit(scattered_coords, scattered_data)

# Fast prediction at any points
predicted = eqs.predict(new_coords)

# Or grid directly
grid = eqs.grid(spacing=1000, data_names=['gravity'])
```
