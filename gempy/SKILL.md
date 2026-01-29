---
name: gempy
description: |
  3D structural geological modeling using implicit methods. Create geological
  models with faults, folds, and unconformities from surface points and
  orientations. Use when Claude needs to: (1) Build 3D geological models from
  surface contacts and orientations, (2) Model faults, unconformities, or
  intrusions, (3) Compute and visualize subsurface geology, (4) Export models
  to VTK or numpy arrays, (5) Generate gravity forward models, (6) Create
  cross-sections or 3D visualizations.
---

# GemPy - 3D Geological Modelling

## Quick Reference

```python
import gempy as gp

# Create model
geo_model = gp.create_geomodel(
    project_name='Model',
    extent=[0, 1000, 0, 1000, 0, 500],  # [xmin, xmax, ymin, ymax, zmin, zmax]
    resolution=[50, 50, 25]
)

# Add surface points and orientations
gp.add_surface_points(geo_model, x=[100, 500, 900], y=[500, 500, 500],
                      z=[400, 350, 400], surface='TopFormation')
gp.add_orientations(geo_model, x=[500], y=[500], z=[375],
                    pole_vector=[0, 0, 1], surface='TopFormation')

# Compute and visualize
gp.set_interpolator(geo_model)
sol = gp.compute_model(geo_model)
gp.plot_2d(geo_model, cell_number=[25], direction='y')
```

## Key Classes

| Class | Purpose |
|-------|---------|
| `GeoModel` | Main container - holds all model data |
| `StructuralFrame` | Manages geological relationships |
| `Grid` | Computation mesh for interpolation |
| `Solutions` | Model results (lithology, scalar fields) |

## Essential Operations

### Define Geological Relationships
```python
gp.map_stack_to_surfaces(geo_model, mapping={
    'Strata1': ['TopFormation', 'BaseFormation'],
    'Basement': ['Basement']
})
geo_model.structural_frame.structural_groups[0].structural_relation = \
    gp.data.StackRelationType.ERODE
```

### Add Faults
```python
gp.add_surface_points(geo_model, x=[300, 300, 300], y=[200, 500, 800],
                      z=[100, 250, 400], surface='Fault1')
gp.add_orientations(geo_model, x=[300], y=[500], z=[250],
                    pole_vector=[1, 0, 0.5], surface='Fault1')
gp.map_stack_to_surfaces(geo_model, mapping={
    'Fault_Series': ['Fault1'],
    'Strata1': ['Layer1', 'Layer2'],
})
geo_model.structural_frame.structural_groups[0].structural_relation = \
    gp.data.StackRelationType.FAULT
```

### Load Data from Files
```python
import pandas as pd

points_df = pd.read_csv('surface_points.csv')  # Columns: X, Y, Z, surface
gp.add_surface_points(geo_model, x=points_df['X'], y=points_df['Y'],
                      z=points_df['Z'], surface=points_df['surface'])

ori_df = pd.read_csv('orientations.csv')  # Columns: X, Y, Z, dip, azimuth, surface
gp.add_orientations(geo_model, x=ori_df['X'], y=ori_df['Y'], z=ori_df['Z'],
                    dip=ori_df['dip'], azimuth=ori_df['azimuth'],
                    surface=ori_df['surface'])
```

### Visualization
```python
gp.plot_2d(geo_model, cell_number=[25], direction='y', show_data=True)
gp.plot_3d(geo_model, show_data=True, show_surfaces=True)  # Requires PyVista
```

### Access Results
```python
sol = gp.compute_model(geo_model)
lithology = sol.raw_arrays.lith_block
lith_3d = lithology.reshape(geo_model.grid.regular_grid.resolution)
```

## Structural Relation Types

| Type | Description |
|------|-------------|
| `ERODE` | Younger surface erodes older (unconformity) |
| `ONLAP` | Younger onlaps onto older |
| `FAULT` | Surface is a fault plane |
| `INTRUSION` | Intrusive body |

## Common Issues

| Issue | Solution |
|-------|----------|
| Model not computing | Check min 2 points + 1 orientation per surface |
| Artifacts at edges | Extend model extent beyond data |
| Wrong fault offset | Check pole_vector direction |
| Memory errors | Reduce grid resolution |

## References

- **[Structural Relations](references/structural_relations.md)** - Detailed guide on ERODE, ONLAP, FAULT
- **[Data Requirements](references/data_requirements.md)** - Input data formats and constraints
- **[Troubleshooting](references/troubleshooting.md)** - Common problems and solutions

## Scripts

- **[scripts/validate_input.py](scripts/validate_input.py)** - Validate input data files
- **[scripts/export_model.py](scripts/export_model.py)** - Export model to VTK, numpy, or CSV
