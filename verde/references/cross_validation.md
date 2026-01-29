# Verde Cross-Validation Reference

## Table of Contents
- [Basic Cross-Validation](#basic-cross-validation)
- [Spatial Cross-Validation](#spatial-cross-validation)
- [Grid Search](#grid-search)
- [Train-Test Split](#train-test-split)
- [Custom Scoring](#custom-scoring)

## Basic Cross-Validation

Evaluate gridder performance using K-fold cross-validation.

```python
import verde as vd

spline = vd.Spline()

# Basic 5-fold cross-validation
scores = vd.cross_val_score(
    spline,
    coordinates,
    values,
    cv=5  # Number of folds
)

print(f"R2 scores: {scores}")
print(f"Mean R2: {scores.mean():.3f} +/- {scores.std():.3f}")
```

**Parameters:**
| Parameter | Type | Description |
|-----------|------|-------------|
| `gridder` | verde gridder | Any verde gridder object |
| `coordinates` | tuple | (x, y) coordinate arrays |
| `data` | array | Values to grid |
| `cv` | int or CV splitter | Number of folds or sklearn CV object |
| `weights` | array | Optional data weights |

## Spatial Cross-Validation

Use spatial blocks for more realistic validation of spatial data.

```python
import verde as vd

# Create block cross-validator
block_cv = vd.BlockKFold(
    spacing=1.0,      # Block size
    n_splits=5,       # Number of folds
    shuffle=True,     # Shuffle blocks before splitting
    random_state=42
)

spline = vd.Spline()
scores = vd.cross_val_score(spline, coordinates, values, cv=block_cv)

print(f"Spatial CV Mean R2: {scores.mean():.3f}")
```

**Why use BlockKFold:**
- Standard K-fold can overestimate performance due to spatial autocorrelation
- Block CV removes entire spatial regions, giving more realistic error estimates
- Essential for spatially correlated geoscience data

**BlockKFold parameters:**
| Parameter | Type | Description |
|-----------|------|-------------|
| `spacing` | float | Size of spatial blocks |
| `n_splits` | int | Number of cross-validation folds |
| `shuffle` | bool | Whether to shuffle blocks |
| `random_state` | int | Random seed for reproducibility |

## Grid Search

Find optimal gridder parameters using cross-validation.

```python
import verde as vd
import numpy as np

# Define parameter grid
dampings = np.logspace(-5, -1, 5)

# Manual grid search
best_score = -np.inf
best_damping = None

for damping in dampings:
    spline = vd.Spline(damping=damping)
    scores = vd.cross_val_score(spline, coordinates, values, cv=5)
    mean_score = scores.mean()

    if mean_score > best_score:
        best_score = mean_score
        best_damping = damping

print(f"Best damping: {best_damping:.2e}, R2: {best_score:.3f}")
```

**Using sklearn GridSearchCV:**

```python
from sklearn.model_selection import GridSearchCV

# Verde gridders are sklearn-compatible
spline = vd.Spline()

param_grid = {
    'damping': [1e-5, 1e-4, 1e-3, 1e-2, 1e-1],
    'mindist': [None, 1e3, 1e4]
}

# Note: sklearn expects X, y format
X = np.column_stack(coordinates)

grid_search = GridSearchCV(
    spline,
    param_grid,
    cv=5,
    scoring='r2'
)

grid_search.fit(X, values)
print(f"Best params: {grid_search.best_params_}")
print(f"Best R2: {grid_search.best_score_:.3f}")
```

## Train-Test Split

Split data for simple train/test evaluation.

```python
import verde as vd

# Random split
train, test = vd.train_test_split(
    coordinates,
    values,
    test_size=0.2,      # 20% for testing
    random_state=42
)

# Unpack
train_coords, train_values = train
test_coords, test_values = test

# Fit and evaluate
spline = vd.Spline()
spline.fit(train_coords, train_values)
score = spline.score(test_coords, test_values)
print(f"Test R2: {score:.3f}")
```

**Spatial block split:**

```python
# Block-based split for spatial data
train, test = vd.train_test_split(
    coordinates,
    values,
    test_size=0.2,
    method='block',      # Use spatial blocks
    spacing=1.0,         # Block size
    random_state=42
)
```

## Custom Scoring

Use different scoring metrics.

```python
import numpy as np
from sklearn.metrics import mean_squared_error, mean_absolute_error

spline = vd.Spline()
spline.fit(train_coords, train_values)

# Predictions
predictions = spline.predict(test_coords)

# Different metrics
r2 = spline.score(test_coords, test_values)  # Built-in R2
rmse = np.sqrt(mean_squared_error(test_values, predictions))
mae = mean_absolute_error(test_values, predictions)

print(f"R2: {r2:.3f}")
print(f"RMSE: {rmse:.3f}")
print(f"MAE: {mae:.3f}")
```

## Workflow Example

Complete cross-validation workflow for parameter tuning:

```python
import verde as vd
import numpy as np

# 1. Load and prepare data
coordinates = (longitude, latitude)
values = elevation

# 2. Create spatial cross-validator
block_cv = vd.BlockKFold(spacing=0.5, n_splits=5, shuffle=True)

# 3. Test different configurations
configs = [
    {'name': 'Spline', 'gridder': vd.Spline()},
    {'name': 'Spline+damping', 'gridder': vd.Spline(damping=1e-3)},
    {'name': 'Chain', 'gridder': vd.Chain([
        ('trend', vd.Trend(degree=1)),
        ('spline', vd.Spline())
    ])},
]

results = []
for config in configs:
    scores = vd.cross_val_score(
        config['gridder'],
        coordinates,
        values,
        cv=block_cv
    )
    results.append({
        'name': config['name'],
        'mean_r2': scores.mean(),
        'std_r2': scores.std()
    })

# 4. Report results
for r in sorted(results, key=lambda x: -x['mean_r2']):
    print(f"{r['name']}: R2 = {r['mean_r2']:.3f} +/- {r['std_r2']:.3f}")
```

## Performance Tips

1. **Start with few folds** (cv=3) for quick iteration, increase for final evaluation
2. **Use BlockKFold** for spatially correlated data
3. **Log-scale parameter search** for damping/regularization parameters
4. **Cache expensive computations** when testing many configurations
5. **Use parallel processing** via sklearn's `n_jobs` parameter when available
