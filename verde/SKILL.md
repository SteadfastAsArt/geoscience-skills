---
name: verde
description: Spatial data gridding and interpolation with a machine-learning style API. Process geographic and Cartesian point data onto regular grids.
---

# Verde - Spatial Data Gridding

Help users grid and interpolate scattered spatial data using machine-learning style workflows.

## Installation

```bash
pip install verde
```

## Core Concepts

### ML-Style API
Verde follows scikit-learn conventions:
- `fit()` - Learn from data
- `predict()` - Estimate at new locations
- `grid()` - Create regular grid
- `score()` - Evaluate fit quality

### Key Classes
| Class | Description |
|-------|-------------|
| `Spline` | Bi-harmonic spline interpolation |
| `Linear` | Linear interpolation |
| `Cubic` | Cubic interpolation |
| `Chain` | Pipeline of operations |
| `BlockReduce` | Decimate to block means/medians |
| `Trend` | Polynomial trend fitting |
| `Vector` | 2-component vector gridding |

## Common Workflows

### 1. Basic Gridding with Spline
```python
import verde as vd
import numpy as np

# Sample data
coordinates = (longitude, latitude)  # Tuple of arrays
values = elevation  # 1D array

# Create and fit spline
spline = vd.Spline()
spline.fit(coordinates, values)

# Grid the data
grid = spline.grid(
    spacing=0.1,  # Grid spacing in degrees
    data_names=['elevation']
)

# Access result (xarray Dataset)
print(grid.elevation)
```

### 2. Project to Cartesian Coordinates
```python
import verde as vd
import pyproj

# Define projection
projection = pyproj.Proj(proj='merc', lat_ts=data_lat.mean())

# Project coordinates
proj_coords = projection(longitude, latitude)

# Fit in projected coordinates
spline = vd.Spline()
spline.fit(proj_coords, values)

# Grid
grid = spline.grid(spacing=1000)  # 1000m spacing
```

### 3. Chain Processing Pipeline
```python
import verde as vd

# Create processing chain
chain = vd.Chain([
    ('trend', vd.Trend(degree=1)),      # Remove linear trend
    ('reduce', vd.BlockReduce(          # Decimate
        reduction=np.median,
        spacing=0.05
    )),
    ('spline', vd.Spline())             # Interpolate
])

# Fit entire chain
chain.fit(coordinates, values)

# Grid
grid = chain.grid(spacing=0.01)
```

### 4. Block Reduce for Large Datasets
```python
import verde as vd
import numpy as np

# Reduce to block medians
reducer = vd.BlockReduce(
    reduction=np.median,
    spacing=0.1  # Block size
)

# Fit and get reduced data
reducer.fit(coordinates, values)
coords_reduced, values_reduced = reducer.filter(coordinates, values)

print(f"Original: {len(values)} points")
print(f"Reduced: {len(values_reduced)} points")
```

### 5. Remove Trend Before Gridding
```python
import verde as vd

# Fit polynomial trend
trend = vd.Trend(degree=2)  # Quadratic trend
trend.fit(coordinates, values)

# Get residuals
residuals = values - trend.predict(coordinates)

# Grid residuals
spline = vd.Spline()
spline.fit(coordinates, residuals)
grid_residuals = spline.grid(spacing=0.05)

# Add trend back
grid_full = grid_residuals + trend.grid(spacing=0.05)
```

### 6. Cross-Validation
```python
import verde as vd
from sklearn.model_selection import cross_val_score

# Create spline gridder
spline = vd.Spline()

# Cross-validate
scores = vd.cross_val_score(
    spline,
    coordinates,
    values,
    cv=5  # 5-fold cross-validation
)

print(f"R² scores: {scores}")
print(f"Mean R²: {scores.mean():.3f}")
```

### 7. Grid to Specific Region
```python
import verde as vd

spline = vd.Spline()
spline.fit(coordinates, values)

# Define region
region = (-10, 10, -5, 5)  # (west, east, south, north)

# Grid within region
grid = spline.grid(
    region=region,
    spacing=0.1,
    adjust='spacing'  # Adjust spacing to fit region exactly
)
```

### 8. Vector Data (e.g., GPS velocities)
```python
import verde as vd

# East and north velocity components
velocity_east = ve
velocity_north = vn

# Create vector spline
vector = vd.Vector([
    vd.Spline(),  # For east component
    vd.Spline()   # For north component
])

# Fit
vector.fit(coordinates, (velocity_east, velocity_north))

# Grid
grid = vector.grid(spacing=0.1, data_names=['v_east', 'v_north'])
```

### 9. Mask with Distance
```python
import verde as vd

spline = vd.Spline()
spline.fit(coordinates, values)

# Grid with masking
grid = spline.grid(spacing=0.1)

# Create distance mask
mask = vd.distance_mask(
    coordinates,
    maxdist=0.2,  # Max distance from data
    grid=grid
)

# Apply mask
grid_masked = grid.where(mask)
```

### 10. Profile Extraction
```python
import verde as vd
import numpy as np

spline = vd.Spline()
spline.fit(coordinates, values)

# Define profile endpoints
point1 = (-5, -5)
point2 = (5, 5)

# Create profile coordinates
profile = vd.profile_coordinates(
    point1,
    point2,
    size=100  # Number of points
)

# Predict along profile
values_profile = spline.predict(profile)
```

### 11. Scipy-based Gridding
```python
import verde as vd

# Linear interpolation (Delaunay triangulation)
linear = vd.Linear()
linear.fit(coordinates, values)
grid = linear.grid(spacing=0.1)

# Cubic interpolation
cubic = vd.Cubic()
cubic.fit(coordinates, values)
grid = cubic.grid(spacing=0.1)
```

### 12. Save Grid to File
```python
import verde as vd

spline = vd.Spline()
spline.fit(coordinates, values)
grid = spline.grid(spacing=0.1)

# Save to NetCDF
grid.to_netcdf('output.nc')

# Save to GeoTIFF (requires rioxarray)
grid.rio.to_raster('output.tif')
```

## Gridder Comparison

| Gridder | Speed | Smoothness | Extrapolation |
|---------|-------|------------|---------------|
| `Spline` | Medium | High | Good |
| `Linear` | Fast | Low | Poor |
| `Cubic` | Fast | Medium | Poor |
| `KNeighbors` | Fast | Variable | Poor |

## Tips

1. **Project geographic data** - Use meters for physical interpretation
2. **Block reduce first** - Speeds up gridding for large datasets
3. **Remove trends** - Improves interpolation for regional data
4. **Cross-validate** - Choose optimal parameters
5. **Mask extrapolation** - Don't trust values far from data
6. **Check units** - Spacing should match coordinate units

## Common Parameters

| Parameter | Description |
|-----------|-------------|
| `spacing` | Grid cell size (same units as coordinates) |
| `region` | (west, east, south, north) bounds |
| `shape` | (n_north, n_east) grid dimensions |
| `adjust` | How to fit region ('spacing' or 'region') |

## Resources

- Documentation: https://www.fatiando.org/verde/
- GitHub: https://github.com/fatiando/verde
- Tutorials: https://www.fatiando.org/verde/latest/tutorials/
- Gallery: https://www.fatiando.org/verde/latest/gallery/
