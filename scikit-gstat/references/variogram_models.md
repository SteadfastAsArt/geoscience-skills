# Variogram Models Reference

## Table of Contents
- [Model Overview](#model-overview)
- [Spherical Model](#spherical-model)
- [Exponential Model](#exponential-model)
- [Gaussian Model](#gaussian-model)
- [Matern Model](#matern-model)
- [Stable Model](#stable-model)
- [Model Selection](#model-selection)

## Model Overview

| Model | Parameters | Near-Origin Behavior | Sill Behavior |
|-------|------------|---------------------|---------------|
| `spherical` | range, sill, nugget | Linear | Reaches exactly |
| `exponential` | range, sill, nugget | Linear | Approaches asymptotically |
| `gaussian` | range, sill, nugget | Parabolic | Approaches asymptotically |
| `matern` | range, sill, nugget, smoothness | Configurable | Approaches asymptotically |
| `stable` | range, sill, nugget, shape | Configurable | Approaches asymptotically |

## Spherical Model

The most commonly used variogram model in geostatistics.

```python
V.model = 'spherical'
```

**Equation:**
```
gamma(h) = nugget + sill * [1.5*(h/range) - 0.5*(h/range)^3]  for h <= range
gamma(h) = nugget + sill                                       for h > range
```

**Characteristics:**
- Linear behavior near the origin
- Reaches the sill exactly at the range
- Suitable for most geological phenomena
- Good default choice when unsure

**Best for:**
- Soil properties
- Geological layers
- Most spatial data without strong smoothness

## Exponential Model

Gradual approach to the sill, never quite reaching it.

```python
V.model = 'exponential'
```

**Equation:**
```
gamma(h) = nugget + sill * [1 - exp(-h/range)]
```

**Characteristics:**
- Linear behavior near origin
- Practical range is ~3x the range parameter
- Never reaches the sill exactly
- Rougher interpolation than Gaussian

**Best for:**
- Groundwater levels
- Contamination plumes
- Data with gradual spatial transitions

## Gaussian Model

Parabolic behavior near origin, very smooth interpolation.

```python
V.model = 'gaussian'
```

**Equation:**
```
gamma(h) = nugget + sill * [1 - exp(-(h/range)^2)]
```

**Characteristics:**
- Parabolic (flat) behavior at origin
- Very smooth interpolation
- Can cause numerical instability in kriging
- Often combined with small nugget for stability

**Best for:**
- Smooth, continuous phenomena
- Topographic surfaces
- Temperature fields
- Data known to be differentiable

**Caution:** Pure Gaussian models can cause singular kriging matrices. Add a small nugget if issues occur.

## Matern Model

Flexible model with controllable smoothness.

```python
V.model = 'matern'
# Smoothness is automatically fitted or can be set
```

**Parameters:**
- `range`: Correlation distance
- `sill`: Total variance
- `nugget`: Measurement error/micro-variability
- `smoothness` (nu): Controls differentiability

**Smoothness values:**
| nu | Equivalent Model |
|----|-----------------|
| 0.5 | Exponential |
| 1.5 | Intermediate |
| inf | Gaussian |

**Best for:**
- When model flexibility is needed
- Unknown smoothness characteristics
- Scientific applications requiring explicit smoothness

## Stable Model

Generalization between exponential and Gaussian.

```python
V.model = 'stable'
```

**Parameters:**
- `range`, `sill`, `nugget`: Standard parameters
- `shape` (alpha): Between 0 and 2

**Shape values:**
| alpha | Behavior |
|-------|----------|
| 1 | Exponential-like |
| 2 | Gaussian-like |

## Model Selection

### Compare Models Programmatically

```python
import skgstat as skg

V = skg.Variogram(coords, values)

models = ['spherical', 'exponential', 'gaussian', 'matern']
results = []

for model in models:
    V.model = model
    results.append({
        'model': model,
        'rmse': V.rmse,
        'range': V.parameters[0],
        'sill': V.parameters[1]
    })

# Sort by RMSE
results.sort(key=lambda x: x['rmse'])
for r in results:
    print(f"{r['model']}: RMSE={r['rmse']:.4f}")
```

### Visual Comparison

```python
import matplotlib.pyplot as plt

fig, axes = plt.subplots(2, 2, figsize=(10, 8))
models = ['spherical', 'exponential', 'gaussian', 'matern']

for ax, model in zip(axes.flat, models):
    V.model = model
    V.plot(ax=ax)
    ax.set_title(f"{model} (RMSE: {V.rmse:.4f})")

plt.tight_layout()
plt.show()
```

### Selection Guidelines

1. **Start with spherical** - Good default for most cases
2. **Try exponential** if data shows gradual transitions
3. **Use Gaussian** only for known smooth phenomena
4. **Use Matern** when flexibility and physical interpretation matter

### Physical Interpretation

| Parameter | Meaning |
|-----------|---------|
| **Range** | Distance at which spatial correlation disappears |
| **Sill** | Total variance of the spatial process |
| **Nugget** | Measurement error + micro-scale variability |
| **Nugget/Sill ratio** | Proportion of unexplained variance (aim for < 0.5) |

### Common Issues

| Issue | Possible Cause | Solution |
|-------|----------------|----------|
| High RMSE all models | Trend in data | Detrend before analysis |
| Nugget > Sill | Poor fit | Try different binning or estimator |
| Range > study area | Insufficient extent | Increase maxlag or collect more data |
| Singular kriging matrix | Gaussian model without nugget | Add small nugget |
