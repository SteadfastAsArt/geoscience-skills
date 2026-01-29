# Verde Gridders Reference

## Table of Contents
- [Spline](#spline)
- [Linear](#linear)
- [Cubic](#cubic)
- [KNeighbors](#kneighbors)
- [Vector](#vector)
- [Chain](#chain)
- [BlockReduce](#blockreduce)
- [Trend](#trend)

## Spline

Bi-harmonic spline interpolation. Best for smooth fields with good extrapolation.

```python
import verde as vd

spline = vd.Spline(
    mindist=None,      # Minimum distance between points (regularization)
    damping=None,      # Damping factor for regularization
    force_coords=None  # Force source locations (advanced)
)

spline.fit(coordinates, values, weights=None)
grid = spline.grid(spacing=0.1)
```

**Parameters:**
| Parameter | Type | Description |
|-----------|------|-------------|
| `mindist` | float | Minimum distance for regularization. Helps with clustered data |
| `damping` | float | Smoothing parameter. Higher = smoother but less accurate |

**When to use:**
- Smooth continuous fields (elevation, gravity, magnetics)
- Need reasonable extrapolation beyond data
- Moderate dataset sizes (< 10,000 points without BlockReduce)

## Linear

Delaunay triangulation with linear interpolation. Fast but no extrapolation.

```python
linear = vd.Linear()
linear.fit(coordinates, values)
grid = linear.grid(spacing=0.1)
```

**When to use:**
- Fast interpolation needed
- Data covers entire region (no extrapolation needed)
- Discontinuous or rapidly varying fields

## Cubic

Delaunay triangulation with cubic interpolation. Smoother than Linear.

```python
cubic = vd.Cubic()
cubic.fit(coordinates, values)
grid = cubic.grid(spacing=0.1)
```

**When to use:**
- Need smoother results than Linear
- Still need fast interpolation
- Data covers region well

## KNeighbors

K-nearest neighbors interpolation. Uses sklearn under the hood.

```python
from verde import KNeighbors

knn = KNeighbors(
    k=10,           # Number of neighbors
    reduction=np.mean  # How to combine neighbors
)
knn.fit(coordinates, values)
```

**Parameters:**
| Parameter | Type | Description |
|-----------|------|-------------|
| `k` | int | Number of nearest neighbors to use |
| `reduction` | callable | Function to combine neighbor values (mean, median) |

## Vector

Grid 2-component vector data (e.g., GPS velocities, wind).

```python
vector = vd.Vector([
    vd.Spline(),  # For east component
    vd.Spline()   # For north component
])

# Data must be tuple of components
velocity_data = (velocity_east, velocity_north)
vector.fit(coordinates, velocity_data)

grid = vector.grid(spacing=0.1, data_names=['v_east', 'v_north'])
```

## Chain

Pipeline of processing steps. Applies operations in sequence.

```python
import numpy as np

chain = vd.Chain([
    ('trend', vd.Trend(degree=1)),           # Remove linear trend
    ('reduce', vd.BlockReduce(               # Decimate data
        reduction=np.median,
        spacing=0.05
    )),
    ('spline', vd.Spline(damping=1e-4))      # Interpolate
])

chain.fit(coordinates, values)
grid = chain.grid(spacing=0.01)

# Access individual components
trend_component = chain.named_steps['trend']
```

**Common Chain Patterns:**

```python
# Trend removal + interpolation
chain = vd.Chain([
    ('trend', vd.Trend(degree=2)),
    ('spline', vd.Spline())
])

# Decimate + interpolate (for large datasets)
chain = vd.Chain([
    ('reduce', vd.BlockReduce(np.median, spacing=0.1)),
    ('spline', vd.Spline())
])
```

## BlockReduce

Decimate data by computing block statistics. Essential for large datasets.

```python
import numpy as np

reducer = vd.BlockReduce(
    reduction=np.median,  # Can be mean, median, std, etc.
    spacing=0.1,          # Block size
    adjust='spacing',     # How to adjust blocks to fit region
    center_coordinates=True  # Return block centers
)

# Filter data
coords_reduced, values_reduced = reducer.filter(coordinates, values)

# Or use in a Chain
chain = vd.Chain([
    ('reduce', reducer),
    ('spline', vd.Spline())
])
```

**Parameters:**
| Parameter | Type | Description |
|-----------|------|-------------|
| `reduction` | callable | numpy function (mean, median, std) |
| `spacing` | float | Block size in coordinate units |
| `center_coordinates` | bool | Return block centers (True) or original coords (False) |

## Trend

Fit and remove polynomial trends from data.

```python
trend = vd.Trend(degree=2)  # Quadratic trend
trend.fit(coordinates, values)

# Get trend values
trend_values = trend.predict(coordinates)

# Get residuals
residuals = values - trend_values

# Grid the trend
trend_grid = trend.grid(spacing=0.1)

# Access coefficients
print(trend.coefs_)
```

**Degree examples:**
| Degree | Type | Equation |
|--------|------|----------|
| 1 | Linear/planar | ax + by + c |
| 2 | Quadratic | ax^2 + bxy + by^2 + cx + dy + e |
| 3 | Cubic | Full 3rd order polynomial |

## Grid Method Parameters

All gridders share these `grid()` parameters:

```python
grid = gridder.grid(
    region=None,       # (west, east, south, north) or infer from data
    spacing=None,      # Grid cell size
    shape=None,        # (n_north, n_east) - alternative to spacing
    adjust='spacing',  # 'spacing' or 'region'
    dims=['northing', 'easting'],  # Dimension names
    data_names=['scalars'],        # Data variable name
    projection=None    # pyproj projection for unprojecting
)
```

**Region specification:**
```python
# Explicit region
grid = spline.grid(region=(-10, 10, -5, 5), spacing=0.1)

# Infer from data (default)
grid = spline.grid(spacing=0.1)

# Use shape instead of spacing
grid = spline.grid(shape=(100, 200))
```
