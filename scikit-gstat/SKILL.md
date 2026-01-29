---
name: scikit-gstat
description: |
  Geostatistical analysis with scikit-learn style API. Compute variograms, kriging
  interpolation, and spatial correlation analysis. Use when Claude needs to: (1) Compute
  experimental variograms from spatial data, (2) Fit variogram models (spherical,
  exponential, gaussian, matern), (3) Perform Ordinary or Universal Kriging interpolation,
  (4) Assess spatial anisotropy with directional variograms, (5) Cross-validate spatial
  models, (6) Analyze spatio-temporal data, (7) Export variogram parameters for other
  geostatistical software.
---

# SciKit-GStat - Geostatistics

## Quick Reference

```python
import skgstat as skg
import numpy as np

# Create variogram
V = skg.Variogram(coordinates=coords, values=values, n_lags=15)

# Fit model
V.model = 'spherical'
print(f"Range: {V.parameters[0]:.2f}, Sill: {V.parameters[1]:.2f}")

# Kriging interpolation
ok = skg.OrdinaryKriging(V)
predictions = ok.transform(grid_coords)
```

## Key Classes

| Class | Purpose |
|-------|---------|
| `Variogram` | Empirical and theoretical variograms |
| `OrdinaryKriging` | Interpolation with spatial correlation |
| `DirectionalVariogram` | Anisotropic variograms |
| `SpaceTimeVariogram` | Spatio-temporal analysis |

## Essential Operations

### Create and Fit Variogram
```python
import skgstat as skg

V = skg.Variogram(
    coordinates=coords,      # (n, 2) array of x, y
    values=values,           # (n,) array of measurements
    n_lags=15,
    maxlag='median'          # or specific distance
)

# Fit model: 'spherical', 'exponential', 'gaussian', 'matern', 'stable'
V.model = 'spherical'

# Get parameters
print(f"Range: {V.parameters[0]:.2f}")
print(f"Sill: {V.parameters[1]:.2f}")
print(f"Nugget: {V.parameters[2]:.2f}")
print(f"RMSE: {V.rmse:.4f}")
```

### Ordinary Kriging
```python
import skgstat as skg
import numpy as np

V = skg.Variogram(coords, values, model='spherical')
ok = skg.OrdinaryKriging(V)

# Create prediction grid
x = np.linspace(0, 100, 50)
y = np.linspace(0, 100, 50)
xx, yy = np.meshgrid(x, y)
grid_coords = np.column_stack([xx.ravel(), yy.ravel()])

# Predict
predictions = ok.transform(grid_coords)
Z = predictions.reshape(xx.shape)

# Get variance
ok.return_variance = True
predictions, variance = ok.transform(grid_coords)
```

### Directional Variogram
```python
import skgstat as skg

DV = skg.DirectionalVariogram(
    coordinates=coords,
    values=values,
    azimuth=45,          # Direction in degrees
    tolerance=22.5,      # Angular tolerance
    bandwidth='q33'      # Perpendicular bandwidth
)

# Check anisotropy
for az in [0, 45, 90, 135]:
    DV.azimuth = az
    print(f"Azimuth {az}: Range = {DV.parameters[0]:.2f}")
```

### Cross-Validation
```python
import skgstat as skg
from sklearn.model_selection import cross_val_score

V = skg.Variogram(coords, values, model='spherical')
ok = skg.OrdinaryKriging(V)

scores = cross_val_score(ok, coords, values, cv=5, scoring='neg_mean_squared_error')
print(f"CV RMSE: {np.sqrt(-scores.mean()):.4f}")
```

### Robust Estimators
```python
import skgstat as skg

# Use robust estimator for noisy data
V = skg.Variogram(
    coords, values,
    estimator='cressie'  # 'matheron', 'cressie', 'dowd', 'genton'
)
```

## Quick Model Reference

| Model | Behavior |
|-------|----------|
| `spherical` | Most common, linear near origin |
| `exponential` | Never reaches sill, gradual approach |
| `gaussian` | Parabolic near origin, smooth |
| `matern` | Flexible smoothness control |

## Tips

1. **Maxlag** should be ~50% of study area diagonal
2. **Use robust estimators** (cressie, dowd) with noisy data
3. **Test multiple models** and compare RMSE
4. **Check anisotropy** with directional variograms before kriging

## References

- **[Variogram Models](references/variogram_models.md)** - Model equations and parameters
- **[Kriging Methods](references/kriging_methods.md)** - Kriging types and configuration

## Scripts

- **[scripts/variogram_analysis.py](scripts/variogram_analysis.py)** - Complete variogram analysis workflow
