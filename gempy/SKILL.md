---
name: gempy
description: 3D structural geological modeling using implicit methods. Create geological models with faults, folds, and unconformities from surface points and orientations.
---

# GemPy - 3D Geological Modelling

Help users create 3D structural geological models using implicit interpolation methods.

## Installation

```bash
pip install gempy
```

## Core Concepts

### Input Data Types
| Type | Description |
|------|-------------|
| Surface points | XYZ coordinates of formation contacts |
| Orientations | Dip direction and angle measurements |
| Surfaces | Geological horizons/faults to model |
| Series | Groups of surfaces with same deposition order |

### Key Classes
- `GeoModel` - Main model container
- `StructuralFrame` - Geological relationships
- `Grid` - Computation mesh
- `Solutions` - Model results

## Common Workflows

### 1. Create Basic Model
```python
import gempy as gp
import numpy as np

# Initialize model
geo_model = gp.create_geomodel(
    project_name='BasicModel',
    extent=[0, 1000, 0, 1000, 0, 500],  # [xmin, xmax, ymin, ymax, zmin, zmax]
    resolution=[50, 50, 25]  # Grid resolution
)

# Add surface points
gp.add_surface_points(
    geo_model,
    x=[100, 500, 900],
    y=[500, 500, 500],
    z=[400, 350, 400],
    surface='TopFormation'
)

# Add orientations
gp.add_orientations(
    geo_model,
    x=[500],
    y=[500],
    z=[375],
    pole_vector=[0, 0, 1],  # Horizontal layer
    surface='TopFormation'
)
```

### 2. Define Geological Relationships
```python
# Define surfaces
gp.map_stack_to_surfaces(
    geo_model,
    mapping={
        'Strata1': ['TopFormation', 'BaseFormation'],
        'Basement': ['Basement']
    }
)

# Set surface types
geo_model.structural_frame.structural_groups[0].structural_relation = \
    gp.data.StackRelationType.ERODE
```

### 3. Compute Model
```python
# Set interpolator
gp.set_interpolator(geo_model)

# Compute
sol = gp.compute_model(geo_model)

# Access results
lithology = sol.raw_arrays.lith_block  # Lithology values
scalar_field = sol.raw_arrays.scalar_field_matrix  # Scalar fields
```

### 4. Visualize Model
```python
# 2D Cross-sections
gp.plot_2d(geo_model, section_names=['section1'])

# 3D Visualization (requires PyVista)
gp.plot_3d(geo_model, show_data=True, show_surfaces=True)

# Custom cross-section
gp.plot_2d(
    geo_model,
    cell_number=[25],  # Slice at cell 25
    direction='y',
    show_data=True
)
```

### 5. Add Faults
```python
# Add fault surface points
gp.add_surface_points(
    geo_model,
    x=[300, 300, 300],
    y=[200, 500, 800],
    z=[100, 250, 400],
    surface='Fault1'
)

# Add fault orientations
gp.add_orientations(
    geo_model,
    x=[300],
    y=[500],
    z=[250],
    pole_vector=[1, 0, 0.5],  # Fault plane normal
    surface='Fault1'
)

# Define fault relationship
gp.map_stack_to_surfaces(
    geo_model,
    mapping={
        'Fault_Series': ['Fault1'],
        'Strata1': ['Layer1', 'Layer2'],
    }
)

# Set fault relation
geo_model.structural_frame.structural_groups[0].structural_relation = \
    gp.data.StackRelationType.FAULT
```

### 6. Model with Unconformity
```python
gp.map_stack_to_surfaces(
    geo_model,
    mapping={
        'Younger': ['Surface1', 'Surface2'],
        'Older': ['Surface3', 'Surface4'],
    }
)

# Set unconformity (younger erodes older)
geo_model.structural_frame.structural_groups[0].structural_relation = \
    gp.data.StackRelationType.ERODE
```

### 7. Load Data from Files
```python
import pandas as pd

# Load surface points from CSV
# CSV columns: X, Y, Z, surface
points_df = pd.read_csv('surface_points.csv')
gp.add_surface_points(
    geo_model,
    x=points_df['X'],
    y=points_df['Y'],
    z=points_df['Z'],
    surface=points_df['surface']
)

# Load orientations from CSV
# CSV columns: X, Y, Z, dip, azimuth, surface
ori_df = pd.read_csv('orientations.csv')
gp.add_orientations(
    geo_model,
    x=ori_df['X'],
    y=ori_df['Y'],
    z=ori_df['Z'],
    dip=ori_df['dip'],
    azimuth=ori_df['azimuth'],
    surface=ori_df['surface']
)
```

### 8. Export Model
```python
# Export to VTK for visualization
gp.save_model(geo_model, path='./saved_model')

# Get model as numpy array
lith_block = sol.raw_arrays.lith_block
lith_3d = lith_block.reshape(geo_model.grid.regular_grid.resolution)

# Export lithology grid
np.save('lithology_grid.npy', lith_3d)
```

### 9. Topography
```python
# Add topography from DEM
gp.set_topography_from_arrays(
    geo_model,
    dem_zval=dem_array  # 2D array of elevations
)

# Or random topography for testing
gp.set_topography_from_random(
    geo_model,
    fractal_dimension=2.0,
    d_z=np.array([300, 500])  # Elevation range
)

# Compute with topography
sol = gp.compute_model(geo_model, compute_mesh=True)

# Plot with topography
gp.plot_3d(geo_model, show_topography=True)
```

### 10. Gravity Forward Model
```python
# Add gravity grid (receiver locations)
gp.set_centered_grid(
    geo_model,
    centers=receiver_xyz,  # (n, 3) array
    resolution=[10, 10, 15],
    radius=5000
)

# Set densities for each surface
geo_model.set_density_by_surface({
    'Surface1': 2.5,
    'Surface2': 2.7,
    'Basement': 2.9
})

# Compute gravity
sol = gp.compute_model(geo_model, compute_gravity=True)

# Get gravity values
gravity = sol.gravity
```

## Data Requirements

### Surface Points
- XYZ coordinates where formation boundaries intersect
- Need multiple points per surface (minimum 2)
- Better coverage = better model

### Orientations
- Structural measurements (dip/dip direction)
- At least 1 per surface required
- More orientations constrain geometry

## Tips

1. **Start simple** - Begin with few surfaces, add complexity
2. **Check data consistency** - Ensure orientations match expected geometry
3. **Use appropriate resolution** - Higher = slower but more detail
4. **Visualize incrementally** - Plot after each addition
5. **Fault order matters** - Youngest faults should be modeled first

## Structural Relations

| Type | Description |
|------|-------------|
| `ERODE` | Younger surface erodes older (unconformity) |
| `ONLAP` | Younger onlaps onto older |
| `FAULT` | Surface is a fault |
| `INTRUSION` | Intrusive body |

## Resources

- Documentation: https://docs.gempy.org/
- GitHub: https://github.com/cgre-aachen/gempy
- Tutorials: https://docs.gempy.org/tutorials/
- Paper: de la Varga et al. (2019) GemPy 1.0
