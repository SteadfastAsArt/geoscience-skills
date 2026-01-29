# Interpolation Methods

## Table of Contents
- [Overview](#overview)
- [PLI - Piecewise Linear Interpolation](#pli---piecewise-linear-interpolation)
- [FDI - Finite Difference Interpolation](#fdi---finite-difference-interpolation)
- [Surfe - Radial Basis Functions](#surfe---radial-basis-functions)
- [Choosing an Interpolator](#choosing-an-interpolator)
- [Common Parameters](#common-parameters)
- [Troubleshooting](#troubleshooting)

## Overview

LoopStructural uses implicit interpolation to build geological surfaces. The interpolator determines how scalar field values are calculated between data points.

| Interpolator | Speed | Memory | Sparse Data | Smoothness |
|-------------|-------|--------|-------------|------------|
| PLI | Medium | Medium | Good | Good |
| FDI | Fast | Low | Fair | Very Good |
| Surfe | Slow | High | Excellent | Excellent |

## PLI - Piecewise Linear Interpolation

Default general-purpose interpolator using tetrahedral meshes.

### When to Use
- General purpose modelling
- Irregular data distributions
- Most common choice for geological models

### Characteristics
- Uses tetrahedral mesh for interpolation
- Good balance of speed and accuracy
- Handles irregular data well
- Supports gradient constraints

### Usage

```python
model.create_and_add_foliation(
    'strat',
    interpolatortype='PLI',
    nelements=1000,      # Number of tetrahedra
    solver='cg',         # Conjugate gradient solver
    cgw=0.1              # Regularization weight
)
```

### Key Parameters

| Parameter | Default | Description |
|-----------|---------|-------------|
| `nelements` | 1000 | Number of mesh elements (higher = finer detail) |
| `solver` | 'cg' | Solver: 'cg' (conjugate gradient), 'lu' (direct) |
| `cgw` | 0.1 | Regularization weight for smoothness |
| `cpw` | 1.0 | Weight for interface constraints |
| `gpw` | 1.0 | Weight for gradient constraints |

### Resolution Guidelines

| Model Size | nelements | Use Case |
|------------|-----------|----------|
| 100-500 | Small test models |
| 1000-5000 | Regional models |
| 5000-20000 | Detailed local models |
| 20000+ | High-resolution models |

## FDI - Finite Difference Interpolation

Fast interpolator using regular grids.

### When to Use
- Large models where speed is critical
- Regular grid output required
- Simple geology without complex structures

### Characteristics
- Uses regular hexahedral grid
- Fastest interpolation method
- Lower memory usage
- Less flexible with irregular data

### Usage

```python
model.create_and_add_foliation(
    'strat',
    interpolatortype='FDI',
    nelements=1000,
    solver='cg'
)
```

### Key Parameters

| Parameter | Default | Description |
|-----------|---------|-------------|
| `nelements` | 1000 | Number of grid cells per axis |
| `solver` | 'cg' | Solver type |
| `step` | auto | Grid step size |

### Limitations
- Less accurate for complex geometries
- May struggle with steep gradients
- Requires more elements for equivalent PLI quality

## Surfe - Radial Basis Functions

RBF-based interpolation for sparse data.

### When to Use
- Very sparse data (few control points)
- Smooth surfaces required
- High-quality interpolation needed

### Characteristics
- Based on radial basis functions
- Best for sparse data
- Produces very smooth surfaces
- Computationally expensive

### Usage

```python
model.create_and_add_foliation(
    'strat',
    interpolatortype='Surfe',
    kernel='cubic'  # RBF kernel type
)
```

### Key Parameters

| Parameter | Default | Description |
|-----------|---------|-------------|
| `kernel` | 'cubic' | RBF kernel: 'cubic', 'gaussian', 'multiquadric' |
| `anisotropy` | 1.0 | Anisotropy ratio for directional smoothing |

### Kernel Types

| Kernel | Characteristics |
|--------|----------------|
| `cubic` | Default, good general smoothness |
| `gaussian` | Very smooth, good for continuous surfaces |
| `multiquadric` | Sharp features, good for discontinuities |

## Choosing an Interpolator

### Decision Flowchart

1. **Do you have sparse data (<50 points)?**
   - Yes: Use **Surfe**
   - No: Continue

2. **Is speed critical?**
   - Yes: Use **FDI**
   - No: Continue

3. **Do you have irregular data distribution?**
   - Yes: Use **PLI**
   - No: Either **PLI** or **FDI**

### Comparison by Scenario

| Scenario | Recommended | Reason |
|----------|-------------|--------|
| Regional model, many boreholes | PLI | Good balance, handles irregular data |
| Detailed mine model | PLI (high nelements) | Accuracy important |
| Quick visualization | FDI | Speed over accuracy |
| Sparse surface mapping | Surfe | Best for few points |
| Fault surfaces | PLI | Handles discontinuities |
| Folded geology | PLI | Works with fold frames |

## Common Parameters

These parameters apply to most interpolators.

### Constraint Weights

Control the influence of different data types:

```python
model.create_and_add_foliation(
    'strat',
    interpolatortype='PLI',
    cpw=1.0,   # Interface point weight
    gpw=1.0,   # Gradient constraint weight
    npw=1.0,   # Normal constraint weight
    cgw=0.1    # Regularization (smoothness) weight
)
```

| Weight | Purpose | Increase If |
|--------|---------|-------------|
| `cpw` | Interface points | Surfaces don't pass through contacts |
| `gpw` | Gradient/orientation | Orientations not honored |
| `npw` | Normal vectors | Surface normals incorrect |
| `cgw` | Smoothness | Surface too rough/noisy |

### Solver Options

```python
# Conjugate gradient (iterative, good for large systems)
model.create_and_add_foliation('strat', solver='cg')

# Direct solver (faster for small systems)
model.create_and_add_foliation('strat', solver='lu')

# PyAMG algebraic multigrid (if installed)
model.create_and_add_foliation('strat', solver='pyamg')
```

## Troubleshooting

### Surface Doesn't Pass Through Data Points

```python
# Increase interface point weight
model.create_and_add_foliation('strat', cpw=10.0)

# Or decrease regularization
model.create_and_add_foliation('strat', cgw=0.01)
```

### Surface Too Rough/Noisy

```python
# Increase regularization
model.create_and_add_foliation('strat', cgw=1.0)

# Or reduce mesh resolution
model.create_and_add_foliation('strat', nelements=500)
```

### Orientations Not Honored

```python
# Increase gradient weight
model.create_and_add_foliation('strat', gpw=10.0)
```

### Memory Issues

```python
# Use FDI instead of PLI
model.create_and_add_foliation('strat', interpolatortype='FDI')

# Or reduce resolution
model.create_and_add_foliation('strat', nelements=500)
```

### Solver Not Converging

```python
# Try different solver
model.create_and_add_foliation('strat', solver='lu')

# Or increase iterations for CG
model.create_and_add_foliation('strat', solver='cg', max_iterations=5000)
```

## Performance Tips

1. **Start with low resolution** - Test with `nelements=500`, then increase
2. **Use FDI for testing** - Switch to PLI for final model
3. **Balance weights** - Don't set weights too high (causes instability)
4. **Check data quality** - Bad data causes solver issues
5. **Profile memory** - Reduce nelements if running out of memory
