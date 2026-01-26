---
name: scikit-gstat
description: Geostatistical analysis with scikit-learn style API. Compute variograms, kriging interpolation, and spatial correlation analysis.
---

# SciKit-GStat - Geostatistics

Help users with variogram analysis and kriging using a scikit-learn style API.

## Installation

```bash
pip install scikit-gstat
```

## Core Concepts

### What SciKit-GStat Does
- Variogram estimation and modelling
- Ordinary and Universal Kriging
- Cross-validation of spatial models
- Space-time variograms
- Integration with scikit-learn

### Key Classes
| Class | Purpose |
|-------|---------|
| `Variogram` | Empirical and theoretical variograms |
| `OrdinaryKriging` | Interpolation with spatial correlation |
| `DirectionalVariogram` | Anisotropic variograms |
| `SpaceTimeVariogram` | Spatio-temporal analysis |

## Common Workflows

### 1. Basic Variogram
```python
import skgstat as skg
import numpy as np

# Sample data
np.random.seed(42)
coords = np.random.rand(100, 2) * 100
values = np.sin(coords[:, 0] / 10) + np.random.normal(0, 0.5, 100)

# Create variogram
V = skg.Variogram(
    coordinates=coords,
    values=values,
    n_lags=15,
    maxlag='median'  # or specific distance
)

# Plot variogram
V.plot()
```

### 2. Fit Variogram Model
```python
import skgstat as skg

# Create variogram
V = skg.Variogram(coords, values)

# Available models: 'spherical', 'exponential', 'gaussian', 'matern', 'stable'
V.model = 'spherical'

# Get fitted parameters
print(f"Range: {V.parameters[0]:.2f}")
print(f"Sill: {V.parameters[1]:.2f}")
print(f"Nugget: {V.parameters[2]:.2f}")

# Plot with model
V.plot()
```

### 3. Compare Models
```python
import skgstat as skg

V = skg.Variogram(coords, values)

# Compare different models
models = ['spherical', 'exponential', 'gaussian', 'matern']
for model in models:
    V.model = model
    rmse = V.rmse
    print(f"{model}: RMSE = {rmse:.4f}")

# Use best model
V.model = 'spherical'
```

### 4. Ordinary Kriging
```python
import skgstat as skg
import numpy as np

# Create variogram
V = skg.Variogram(coords, values, model='spherical')

# Create kriging instance
ok = skg.OrdinaryKriging(V)

# Define prediction grid
x = np.linspace(0, 100, 50)
y = np.linspace(0, 100, 50)
xx, yy = np.meshgrid(x, y)
grid_coords = np.column_stack([xx.ravel(), yy.ravel()])

# Predict
predictions = ok.transform(grid_coords)

# Reshape to grid
Z = predictions.reshape(xx.shape)

# Plot
import matplotlib.pyplot as plt
plt.contourf(xx, yy, Z, levels=20)
plt.scatter(coords[:, 0], coords[:, 1], c=values, edgecolor='k')
plt.colorbar()
plt.show()
```

### 5. Get Kriging Variance
```python
import skgstat as skg

V = skg.Variogram(coords, values, model='spherical')
ok = skg.OrdinaryKriging(V)

# Transform returns predictions only by default
predictions = ok.transform(grid_coords)

# Get both predictions and variance
ok.return_variance = True
predictions, variance = ok.transform(grid_coords)

# Plot uncertainty
Z_var = variance.reshape(xx.shape)
plt.contourf(xx, yy, Z_var, levels=20, cmap='Reds')
plt.colorbar(label='Kriging Variance')
plt.show()
```

### 6. Cross-Validation
```python
import skgstat as skg
from sklearn.model_selection import cross_val_score

V = skg.Variogram(coords, values, model='spherical')
ok = skg.OrdinaryKriging(V)

# Use sklearn cross-validation
scores = cross_val_score(
    ok,
    coords,
    values,
    cv=5,
    scoring='neg_mean_squared_error'
)

print(f"CV RMSE: {np.sqrt(-scores.mean()):.4f}")
```

### 7. Directional Variogram
```python
import skgstat as skg

# Create directional variogram
DV = skg.DirectionalVariogram(
    coordinates=coords,
    values=values,
    azimuth=45,          # Direction in degrees
    tolerance=22.5,      # Angular tolerance
    bandwidth='q33'      # Perpendicular bandwidth
)

DV.plot()

# Check for anisotropy by comparing directions
azimuths = [0, 45, 90, 135]
for az in azimuths:
    DV.azimuth = az
    print(f"Azimuth {az}°: Range = {DV.parameters[0]:.2f}")
```

### 8. Space-Time Variogram
```python
import skgstat as skg
import numpy as np

# Spatio-temporal data
n_points = 50
n_times = 10

# Coordinates (x, y) for each time step
space_coords = np.random.rand(n_points, 2) * 100
time_coords = np.arange(n_times)

# Values at each point and time
values = np.random.rand(n_points, n_times)

# Create space-time variogram
STV = skg.SpaceTimeVariogram(
    coordinates=space_coords,
    values=values,
    x_lags=15,
    t_lags=n_times - 1
)

STV.plot()
```

### 9. Custom Bin Edges
```python
import skgstat as skg
import numpy as np

# Custom lag bins
bin_edges = [0, 5, 10, 20, 30, 50, 75, 100]

V = skg.Variogram(
    coords, values,
    bin_func=bin_edges  # Custom bins
)

# Or use a binning function
V = skg.Variogram(
    coords, values,
    bin_func='kmeans',  # 'even', 'uniform', 'kmeans', 'ward', 'sturges'
    n_lags=10
)
```

### 10. Variogram Cloud
```python
import skgstat as skg

V = skg.Variogram(coords, values)

# Get the variogram cloud (all point pairs)
lags = V.lag_groups()
cloud = V.experimental

# Plot cloud with binned variogram
import matplotlib.pyplot as plt

fig, ax = plt.subplots()
ax.scatter(lags, cloud, alpha=0.3, s=5, label='Cloud')
ax.plot(V.bins, V.experimental, 'ro-', label='Binned')
ax.legend()
plt.show()
```

### 11. Robust Variogram Estimators
```python
import skgstat as skg

# Cressie-Hawkins robust estimator
V = skg.Variogram(
    coords, values,
    estimator='cressie'  # 'matheron', 'cressie', 'dowd', 'genton', 'minmax', 'entropy'
)

# Compare estimators
estimators = ['matheron', 'cressie', 'dowd']
for est in estimators:
    V.estimator = est
    V.model = 'spherical'
    print(f"{est}: Range = {V.parameters[0]:.2f}, Sill = {V.parameters[1]:.2f}")
```

### 12. Export Variogram Parameters
```python
import skgstat as skg

V = skg.Variogram(coords, values, model='spherical')

# Get parameters
params = {
    'model': V.model.__name__,
    'range': V.parameters[0],
    'sill': V.parameters[1],
    'nugget': V.parameters[2],
    'rmse': V.rmse
}

print(params)

# For use in other software
# range, sill, nugget format
```

## Variogram Models

| Model | Parameters | Description |
|-------|------------|-------------|
| `spherical` | range, sill, nugget | Most common, linear near origin |
| `exponential` | range, sill, nugget | Never reaches sill |
| `gaussian` | range, sill, nugget | Parabolic near origin |
| `matern` | range, sill, nugget, smoothness | Flexible, controls smoothness |
| `stable` | range, sill, nugget, shape | Between exponential and gaussian |

## Estimator Methods

| Estimator | Robustness | Description |
|-----------|------------|-------------|
| `matheron` | Low | Classical, sensitive to outliers |
| `cressie` | Medium | Cressie-Hawkins robust |
| `dowd` | High | Median-based |
| `genton` | High | Quantile-based |

## Tips

1. **Check for outliers** before variogram analysis
2. **Use robust estimators** (cressie, dowd) with noisy data
3. **Maxlag should be ~50%** of the study area diagonal
4. **Test multiple models** and compare RMSE
5. **Check anisotropy** with directional variograms
6. **Cross-validate** to assess prediction quality

## Resources

- Documentation: https://scikit-gstat.readthedocs.io/
- GitHub: https://github.com/mmaelicke/scikit-gstat
- Tutorials: https://scikit-gstat.readthedocs.io/en/latest/tutorials/
