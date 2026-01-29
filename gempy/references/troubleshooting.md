# GemPy Troubleshooting Guide

## Table of Contents
- [Model Computation Errors](#model-computation-errors)
- [Data Input Issues](#data-input-issues)
- [Visualization Problems](#visualization-problems)
- [Performance Issues](#performance-issues)
- [Geological Artifacts](#geological-artifacts)

## Model Computation Errors

### Model Fails to Compute

**Problem**: `compute_model()` raises an error or returns empty results.

```python
# Check minimum data requirements
for surface in geo_model.structural_frame.surfaces:
    points = geo_model.surface_points.df[
        geo_model.surface_points.df['surface'] == surface.name
    ]
    orientations = geo_model.orientations.df[
        geo_model.orientations.df['surface'] == surface.name
    ]
    print(f"{surface.name}: {len(points)} points, {len(orientations)} orientations")
```

**Solutions**:
- Ensure each surface has at least 2 surface points
- Ensure each surface has at least 1 orientation
- Check that surfaces are mapped to series

### Interpolator Not Set

**Problem**: `AttributeError` when computing model.

```python
# Always set interpolator before computing
gp.set_interpolator(geo_model)
sol = gp.compute_model(geo_model)
```

### Surface Not Mapped

**Problem**: Surface data exists but not included in model.

```python
# Check mapping
print(geo_model.structural_frame)

# Ensure all surfaces are mapped
gp.map_stack_to_surfaces(
    geo_model,
    mapping={
        'Series1': ['Surface1', 'Surface2'],
        'Basement': ['Basement']  # Don't forget basement
    }
)
```

## Data Input Issues

### Data Outside Model Extent

**Problem**: Points are ignored because they fall outside the model bounds.

```python
# Check data vs extent
import numpy as np

extent = geo_model.grid.regular_grid.extent
points_df = geo_model.surface_points.df

outside = points_df[
    (points_df['X'] < extent[0]) | (points_df['X'] > extent[1]) |
    (points_df['Y'] < extent[2]) | (points_df['Y'] > extent[3]) |
    (points_df['Z'] < extent[4]) | (points_df['Z'] > extent[5])
]

if len(outside) > 0:
    print(f"Warning: {len(outside)} points outside extent")
    print(outside)
```

**Solution**: Extend model extent or remove outlier points.

### Wrong Orientation Convention

**Problem**: Surfaces dip in wrong direction.

```python
# Check azimuth convention (GemPy uses dip direction, not strike)
# Azimuth 0 = North, 90 = East, 180 = South, 270 = West

# If using strike instead of dip direction:
azimuth_dip_direction = (strike + 90) % 360
```

### Duplicate Surface Names

**Problem**: Unexpected behavior with surfaces.

```python
# Check for duplicates
surfaces = [s.name for s in geo_model.structural_frame.surfaces]
from collections import Counter
dups = [k for k, v in Counter(surfaces).items() if v > 1]
if dups:
    print(f"Duplicate surfaces: {dups}")
```

### Inconsistent Units

**Problem**: Model looks stretched or compressed.

```python
# Verify units are consistent (typically meters)
print("X range:", geo_model.surface_points.df['X'].min(),
      geo_model.surface_points.df['X'].max())
print("Y range:", geo_model.surface_points.df['Y'].min(),
      geo_model.surface_points.df['Y'].max())
print("Z range:", geo_model.surface_points.df['Z'].min(),
      geo_model.surface_points.df['Z'].max())

# Check for unit mismatches (e.g., X/Y in meters, Z in feet)
```

## Visualization Problems

### PyVista Not Available

**Problem**: 3D plotting fails with import error.

```python
# Check if PyVista is installed
try:
    import pyvista
    print("PyVista available")
except ImportError:
    print("Install PyVista: pip install pyvista")

# Use 2D plotting instead
gp.plot_2d(geo_model, cell_number=[25], direction='y')
```

### Empty or Black Plot

**Problem**: Plot appears but shows nothing.

```python
# Ensure model is computed
sol = gp.compute_model(geo_model)

# Check that results exist
if sol.raw_arrays.lith_block is None:
    print("Model not computed properly")

# Verify cross-section intersects geology
print("Model extent:", geo_model.grid.regular_grid.extent)
```

### Wrong Cross-Section Location

**Problem**: Cross-section doesn't show expected geology.

```python
# cell_number is index into grid (not coordinate)
resolution = geo_model.grid.regular_grid.resolution
extent = geo_model.grid.regular_grid.extent

# To get cross-section at Y=500:
y_cells = resolution[1]
y_range = extent[3] - extent[2]
cell_at_500 = int((500 - extent[2]) / y_range * y_cells)

gp.plot_2d(geo_model, cell_number=[cell_at_500], direction='y')
```

## Performance Issues

### Slow Computation

**Problem**: Model takes very long to compute.

```python
# Reduce resolution for testing
geo_model = gp.create_geomodel(
    project_name='Test',
    extent=[0, 1000, 0, 1000, 0, 500],
    resolution=[25, 25, 15]  # Low resolution for testing
)

# For production, increase resolution gradually
# resolution=[50, 50, 25]  # Medium
# resolution=[100, 100, 50]  # High (slower)
```

### Memory Errors

**Problem**: Out of memory during computation.

```python
# Reduce resolution
resolution = [50, 50, 25]  # Instead of [100, 100, 50]

# Clear previous models
import gc
del geo_model
gc.collect()

# Create new model with lower resolution
geo_model = gp.create_geomodel(
    project_name='Model',
    extent=extent,
    resolution=resolution
)
```

### Large File Exports

**Problem**: Exported files are very large.

```python
# Export at reduced resolution
import numpy as np

# Get lithology at model resolution
lith = sol.raw_arrays.lith_block
lith_3d = lith.reshape(geo_model.grid.regular_grid.resolution)

# Downsample for export
from scipy.ndimage import zoom
scale = 0.5  # Reduce to 50%
lith_small = zoom(lith_3d, scale, order=0)  # order=0 for nearest neighbor

np.save('lithology_small.npy', lith_small)
```

## Geological Artifacts

### Edge Effects

**Problem**: Strange geology at model boundaries.

```python
# Extend model extent beyond data
x_range = points_df['X'].max() - points_df['X'].min()
buffer = 0.2 * x_range  # 20% buffer

extent = [
    points_df['X'].min() - buffer,
    points_df['X'].max() + buffer,
    points_df['Y'].min() - buffer,
    points_df['Y'].max() + buffer,
    points_df['Z'].min() - buffer,
    points_df['Z'].max() + buffer,
]
```

### Fault Doesn't Offset Layers

**Problem**: Fault surface exists but doesn't cut stratigraphy.

```python
# Check fault is in separate series
# Check fault series is BEFORE stratigraphy in mapping order
gp.map_stack_to_surfaces(
    geo_model,
    mapping={
        'Fault_Series': ['Fault1'],  # FIRST
        'Stratigraphy': ['Layer1', 'Layer2'],  # AFTER
    }
)

# Ensure FAULT relation is set
geo_model.structural_frame.structural_groups[0].structural_relation = \
    gp.data.StackRelationType.FAULT
```

### Surfaces Crossing Incorrectly

**Problem**: Formations cross where they shouldn't.

```python
# Check surface order in series (youngest at top)
gp.map_stack_to_surfaces(
    geo_model,
    mapping={
        'Strata': [
            'Youngest',  # Top
            'Middle',
            'Oldest',    # Bottom
        ],
    }
)

# Check for conflicting data points
# Points from different surfaces at same location
```

### Unrealistic Geometries

**Problem**: Model shows geologically impossible shapes.

```python
# Add more constraint points
# Place orientations near surface points
# Check orientation consistency

# Visualize input data
gp.plot_2d(geo_model, show_data=True, show_results=False)
```

### Debugging Checklist

1. **Data check**: Min 2 points + 1 orientation per surface
2. **Mapping check**: All surfaces mapped to series
3. **Order check**: Correct series order (faults first, youngest up)
4. **Extent check**: Data within model bounds
5. **Interpolator check**: `set_interpolator()` called
6. **Relation check**: Correct structural relation types set
