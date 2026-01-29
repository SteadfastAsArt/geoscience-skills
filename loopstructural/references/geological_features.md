# Geological Feature Types

## Table of Contents
- [Overview](#overview)
- [Foliation (Stratigraphic Surfaces)](#foliation-stratigraphic-surfaces)
- [Faults](#faults)
- [Fold Frames](#fold-frames)
- [Folded Foliations](#folded-foliations)
- [Intrusions](#intrusions)
- [Unconformities](#unconformities)

## Overview

LoopStructural models geology using implicit surfaces. Each geological feature is represented as a scalar field where isosurfaces define geological boundaries.

| Feature Type | Method | Use Case |
|-------------|--------|----------|
| Foliation | `create_and_add_foliation()` | Stratigraphic layers, flat-lying geology |
| Fault | `create_and_add_fault()` | Fault surfaces with displacement |
| Fold Frame | `create_and_add_fold_frame()` | Coordinate system for folded rocks |
| Folded Foliation | `create_and_add_folded_foliation()` | Folded stratigraphic layers |

## Foliation (Stratigraphic Surfaces)

Basic stratigraphic surfaces interpolated from contact points and orientations.

### When to Use
- Flat-lying or gently dipping stratigraphy
- Simple tilted sequences
- Any layered geology without significant folding

### Data Requirements

```python
# Interface points (on geological surfaces)
interfaces = pd.DataFrame({
    'X': [1000, 2000, 3000],
    'Y': [5000, 5000, 5000],
    'Z': [-200, -250, -300],
    'feature_name': ['strat', 'strat', 'strat'],
    'val': [0, 0, 0]  # Same value = same horizon
})

# Orientation data (optional but recommended)
orientations = pd.DataFrame({
    'X': [2000],
    'Y': [5000],
    'Z': [-200],
    'feature_name': ['strat'],
    'strike': [45],  # Strike direction in degrees
    'dip': [15],     # Dip angle in degrees
    'val': [np.nan]  # NaN for orientation points
})
```

### Creating Foliations

```python
model.create_and_add_foliation(
    'strat',
    interpolatortype='PLI',  # Interpolation method
    nelements=1000,          # Grid resolution
    solver='cg'              # Solver type
)
```

### Multiple Units

Use different `val` values to represent different stratigraphic levels:

```python
data = pd.DataFrame({
    'X': [5000, 5000, 5000],
    'Y': [5000, 5000, 5000],
    'Z': [-100, -300, -500],
    'feature_name': ['strat', 'strat', 'strat'],
    'val': [0, 1, 2]  # Top, middle, base units
})

# Extract specific horizons
viewer.add_isosurface(model['strat'], isovalue=0, name='unit_top')
viewer.add_isosurface(model['strat'], isovalue=1, name='unit_middle')
viewer.add_isosurface(model['strat'], isovalue=2, name='unit_base')
```

## Faults

Fault surfaces that offset other geological features.

### When to Use
- Normal, reverse, or strike-slip faults
- Fault networks with multiple faults
- Any displacement of geological surfaces

### Data Requirements

```python
# Fault surface points
fault_points = pd.DataFrame({
    'X': [5000, 5000, 5000],
    'Y': [2000, 5000, 8000],
    'Z': [-200, -500, -800],
    'feature_name': ['fault1', 'fault1', 'fault1'],
    'val': [0, 0, 0],      # On fault surface
    'coord': [0, 0, 0]     # Fault coordinate
})

# Fault orientation (normal vector)
fault_orient = pd.DataFrame({
    'X': [5000],
    'Y': [5000],
    'Z': [-500],
    'feature_name': ['fault1'],
    'gx': [1], 'gy': [0], 'gz': [0]  # Normal pointing East
})
```

### Creating Faults

```python
model.create_and_add_fault(
    'fault1',
    displacement=200,           # Displacement magnitude
    fault_slip_vector=[1, 0, 0] # Optional: slip direction
)
```

### Fault Networks

Add multiple faults in order of relative age (oldest first):

```python
# Older fault (gets cut by younger)
model.create_and_add_fault('fault_old', displacement=100)

# Younger fault (cuts the older)
model.create_and_add_fault('fault_young', displacement=150)

# Stratigraphy last (affected by all faults)
model.create_and_add_foliation('strat')
```

## Fold Frames

Coordinate systems for representing folded geology.

### When to Use
- Folded stratigraphy
- Complex structural domains
- Areas with multiple fold generations

### Data Requirements

Fold frame requires data defining the fold geometry:
- Fold axis orientations
- Axial surface orientations
- Limb orientations

```python
# Fold axis trend and plunge
fold_data = pd.DataFrame({
    'X': [5000, 5000],
    'Y': [2000, 8000],
    'Z': [-500, -500],
    'feature_name': ['fold_frame', 'fold_frame'],
    'fold_axis_x': [0, 0],
    'fold_axis_y': [1, 1],
    'fold_axis_z': [0, 0]
})
```

### Creating Fold Frames

```python
model.create_and_add_fold_frame(
    'fold_frame',
    nelements=2000  # Higher resolution for complex folds
)
```

## Folded Foliations

Stratigraphic surfaces that have been folded.

### When to Use
- After creating a fold frame
- Synclinal or anticlinal geometries
- Refolded folds

### Creating Folded Foliations

```python
# First create the fold frame
model.create_and_add_fold_frame('fold_frame')

# Then create folded stratigraphy using that frame
model.create_and_add_folded_foliation(
    'strat',
    fold_frame='fold_frame',
    fold=True
)
```

## Intrusions

Igneous intrusive bodies modelled as implicit surfaces.

### When to Use
- Plutons, stocks, batholiths
- Dikes and sills
- Any cross-cutting igneous body

### Data Requirements

```python
# Points on intrusion boundary
intrusion_data = pd.DataFrame({
    'X': [5000, 4500, 5500, 5000, 5000],
    'Y': [5000, 5000, 5000, 4500, 5500],
    'Z': [-500, -500, -500, -500, -500],
    'feature_name': ['intrusion', 'intrusion', 'intrusion', 'intrusion', 'intrusion'],
    'val': [0, 0, 0, 0, 0]  # All on boundary
})

# Points inside intrusion (optional)
inside_points = pd.DataFrame({
    'X': [5000], 'Y': [5000], 'Z': [-500],
    'feature_name': ['intrusion'],
    'val': [-1]  # Negative value = inside
})
```

### Creating Intrusions

```python
model.create_and_add_foliation(
    'intrusion',
    interpolatortype='PLI'
)

# The intrusion is where model['intrusion'] < 0
```

## Unconformities

Angular unconformities and erosional surfaces.

### When to Use
- Erosional contacts
- Angular unconformities
- Onlap/offlap relationships

### Modelling Approach

Model each stratigraphic package separately, then combine:

```python
# Package above unconformity
model.create_and_add_foliation('upper_package')

# Package below unconformity (may have different orientation)
model.create_and_add_foliation('lower_package')

# Unconformity surface itself
model.create_and_add_foliation('unconformity')
```

## Feature Order Best Practices

The order of feature creation matters:

1. **Faults** - Add from oldest to youngest
2. **Fold frames** - If modelling folded geology
3. **Unconformities** - Erosional surfaces
4. **Stratigraphy** - Affected by all above features

```python
# Correct order
model.create_and_add_fault('fault1', displacement=100)
model.create_and_add_fold_frame('fold_frame')
model.create_and_add_folded_foliation('strat', fold_frame='fold_frame')
model.update()
```
