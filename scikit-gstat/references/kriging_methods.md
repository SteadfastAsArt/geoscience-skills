# Kriging Methods Reference

## Table of Contents
- [Kriging Overview](#kriging-overview)
- [Ordinary Kriging](#ordinary-kriging)
- [Kriging Variance](#kriging-variance)
- [Prediction Grid Setup](#prediction-grid-setup)
- [Performance Optimization](#performance-optimization)
- [Common Issues](#common-issues)

## Kriging Overview

Kriging is a geostatistical interpolation method that provides:
- **Best Linear Unbiased Estimator (BLUE)** of unknown values
- **Estimation variance** at each prediction location
- **Exact interpolation** (predictions match observations at data points)

### Available Methods in SciKit-GStat

| Class | Description | Use Case |
|-------|-------------|----------|
| `OrdinaryKriging` | Assumes constant unknown mean | Most common choice |
| `SimpleKriging` | Assumes known constant mean | When mean is well-established |

## Ordinary Kriging

The most widely used kriging variant.

### Basic Usage

```python
import skgstat as skg
import numpy as np

# Fit variogram first
V = skg.Variogram(coords, values, model='spherical')

# Create kriging estimator
ok = skg.OrdinaryKriging(V)

# Predict at new locations
predictions = ok.transform(new_coords)
```

### Parameters

| Parameter | Description | Default |
|-----------|-------------|---------|
| `variogram` | Fitted Variogram object | Required |
| `min_points` | Minimum neighbors for estimation | 5 |
| `max_points` | Maximum neighbors (None = all) | 15 |
| `mode` | 'exact' or 'estimate' | 'exact' |

### Setting Parameters

```python
ok = skg.OrdinaryKriging(
    variogram=V,
    min_points=5,
    max_points=20
)
```

## Kriging Variance

Kriging provides uncertainty estimates at each prediction location.

### Get Predictions and Variance

```python
ok = skg.OrdinaryKriging(V)

# Enable variance output
ok.return_variance = True

# Transform returns tuple
predictions, variance = ok.transform(grid_coords)

# Standard error
std_error = np.sqrt(variance)
```

### Interpret Variance

| Variance Level | Interpretation |
|----------------|----------------|
| Low | Close to data points, reliable estimate |
| High | Far from data points, uncertain estimate |
| Equal to sill | No spatial correlation, similar to mean |

### Plot Uncertainty

```python
import matplotlib.pyplot as plt

fig, axes = plt.subplots(1, 2, figsize=(12, 5))

# Predictions
ax1 = axes[0]
im1 = ax1.contourf(xx, yy, predictions.reshape(xx.shape), levels=20)
ax1.scatter(coords[:, 0], coords[:, 1], c='k', s=10)
plt.colorbar(im1, ax=ax1, label='Predicted Value')
ax1.set_title('Kriging Predictions')

# Variance
ax2 = axes[1]
im2 = ax2.contourf(xx, yy, variance.reshape(xx.shape), levels=20, cmap='Reds')
ax2.scatter(coords[:, 0], coords[:, 1], c='k', s=10)
plt.colorbar(im2, ax=ax2, label='Kriging Variance')
ax2.set_title('Estimation Uncertainty')

plt.tight_layout()
plt.show()
```

## Prediction Grid Setup

### Regular Grid

```python
import numpy as np

# Define extent
x_min, x_max = coords[:, 0].min(), coords[:, 0].max()
y_min, y_max = coords[:, 1].min(), coords[:, 1].max()

# Create grid
resolution = 50  # grid cells per dimension
x = np.linspace(x_min, x_max, resolution)
y = np.linspace(y_min, y_max, resolution)
xx, yy = np.meshgrid(x, y)

# Flatten for kriging
grid_coords = np.column_stack([xx.ravel(), yy.ravel()])

# Predict and reshape
predictions = ok.transform(grid_coords)
Z = predictions.reshape(xx.shape)
```

### Irregular Points

```python
# Predict at specific locations
target_coords = np.array([
    [50, 50],
    [75, 25],
    [25, 75]
])

predictions = ok.transform(target_coords)
```

### Mask Invalid Areas

```python
from scipy.spatial import ConvexHull
from matplotlib.path import Path

# Create convex hull of data points
hull = ConvexHull(coords)
hull_path = Path(coords[hull.vertices])

# Mask points outside hull
mask = hull_path.contains_points(grid_coords)
predictions[~mask] = np.nan
```

## Performance Optimization

### Limit Search Neighbors

```python
# Use only nearest neighbors for large datasets
ok = skg.OrdinaryKriging(
    V,
    max_points=20  # Limit to 20 nearest points
)
```

### Reduce Grid Resolution

```python
# Start with coarse grid for testing
resolution = 25  # instead of 100+
```

### Batch Processing

```python
# For very large grids, process in chunks
chunk_size = 1000
predictions = []

for i in range(0, len(grid_coords), chunk_size):
    chunk = grid_coords[i:i+chunk_size]
    pred = ok.transform(chunk)
    predictions.extend(pred)

predictions = np.array(predictions)
```

## Cross-Validation

### K-Fold Cross-Validation

```python
from sklearn.model_selection import cross_val_score
import numpy as np

V = skg.Variogram(coords, values, model='spherical')
ok = skg.OrdinaryKriging(V)

# Use sklearn's cross-validation
scores = cross_val_score(
    ok, coords, values,
    cv=5,
    scoring='neg_mean_squared_error'
)

rmse = np.sqrt(-scores.mean())
print(f"Cross-validation RMSE: {rmse:.4f}")
```

### Leave-One-Out Cross-Validation

```python
from sklearn.model_selection import LeaveOneOut

loo = LeaveOneOut()
scores = cross_val_score(ok, coords, values, cv=loo, scoring='neg_mean_squared_error')
rmse = np.sqrt(-scores.mean())
```

## Common Issues

### Singular Matrix Error

**Cause:** Duplicate points or purely Gaussian model

**Solution:**
```python
# Add small nugget to variogram
V = skg.Variogram(coords, values, model='gaussian')
# If nugget is 0, manually add small value
if V.parameters[2] < 1e-10:
    V.nugget = 0.01 * V.parameters[1]  # 1% of sill
```

### Poor Predictions at Edges

**Cause:** Extrapolation beyond data extent

**Solution:**
- Limit prediction grid to data extent
- Use convex hull masking
- Increase max_points for edge regions

### Memory Error with Large Grids

**Cause:** Creating full distance matrix

**Solution:**
```python
# Reduce grid resolution
# Use max_points to limit neighbors
# Process in chunks
```

### Unrealistic Variance

**Cause:** Poor variogram fit

**Solution:**
- Check variogram model visually
- Try different models
- Use robust estimators for noisy data

## Workflow Checklist

1. **Exploratory analysis** - Check for trends, outliers
2. **Compute experimental variogram** - Set appropriate lags and maxlag
3. **Fit variogram model** - Compare multiple models
4. **Validate model** - Cross-validation
5. **Setup prediction grid** - Appropriate resolution
6. **Run kriging** - Get predictions and variance
7. **Post-process** - Mask, visualize, export
