# GemPy Data Requirements

## Table of Contents
- [Overview](#overview)
- [Surface Points](#surface-points)
- [Orientations](#orientations)
- [Model Extent](#model-extent)
- [CSV File Formats](#csv-file-formats)
- [Data Quality Guidelines](#data-quality-guidelines)

## Overview

GemPy requires two primary data types to build geological models:

| Data Type | Purpose | Minimum Required |
|-----------|---------|-----------------|
| Surface Points | Define where formation boundaries occur | 2 per surface |
| Orientations | Define surface attitude (dip/strike) | 1 per surface |

## Surface Points

### Definition
Surface points are XYZ coordinates where geological formation boundaries (contacts) are observed or interpreted.

### Adding Points Programmatically
```python
import gempy as gp

gp.add_surface_points(
    geo_model,
    x=[100, 200, 300],
    y=[500, 500, 500],
    z=[400, 380, 360],
    surface='TopFormation'
)
```

### Required Fields

| Field | Type | Description |
|-------|------|-------------|
| x | float | X coordinate |
| y | float | Y coordinate |
| z | float | Z coordinate (elevation/depth) |
| surface | string | Surface/formation name |

### Best Practices

- **Minimum 2 points per surface**: More points = better constraint
- **Spatial distribution**: Spread points across the model area
- **Avoid clustering**: Don't put all points in one location
- **Cover depth range**: Include points at different elevations

## Orientations

### Definition
Orientations define the attitude (dip and dip direction) of geological surfaces.

### Adding Orientations Programmatically

```python
# Using dip and azimuth
gp.add_orientations(
    geo_model,
    x=[500], y=[500], z=[375],
    dip=[30],           # Dip angle in degrees
    azimuth=[90],       # Dip direction (0=N, 90=E, 180=S, 270=W)
    surface='TopFormation'
)

# Using pole vector
gp.add_orientations(
    geo_model,
    x=[500], y=[500], z=[375],
    pole_vector=[0, 0, 1],  # Normal to surface (horizontal layer)
    surface='TopFormation'
)
```

### Required Fields

| Field | Type | Description |
|-------|------|-------------|
| x | float | X coordinate |
| y | float | Y coordinate |
| z | float | Z coordinate |
| surface | string | Surface name |
| dip | float | Dip angle (0-90 degrees) |
| azimuth | float | Dip direction (0-360 degrees) |

OR

| Field | Type | Description |
|-------|------|-------------|
| pole_vector | array | [Gx, Gy, Gz] normal vector to surface |

### Pole Vector Examples

| Geometry | Pole Vector | Description |
|----------|-------------|-------------|
| Horizontal | [0, 0, 1] | Flat-lying layer |
| Vertical N-S | [1, 0, 0] | Strikes N-S, dips E |
| Vertical E-W | [0, 1, 0] | Strikes E-W, dips N |
| 45 deg dip E | [0.71, 0, 0.71] | Dips 45 degrees to east |
| 30 deg dip N | [0, 0.5, 0.87] | Dips 30 degrees to north |

### Converting Dip/Azimuth to Pole Vector

```python
import numpy as np

def dip_azimuth_to_pole(dip, azimuth):
    """Convert dip and azimuth to pole vector."""
    dip_rad = np.radians(dip)
    az_rad = np.radians(azimuth)

    Gx = np.sin(dip_rad) * np.sin(az_rad)
    Gy = np.sin(dip_rad) * np.cos(az_rad)
    Gz = np.cos(dip_rad)

    return [Gx, Gy, Gz]
```

## Model Extent

### Definition
The model extent defines the 3D bounding box for computation.

```python
geo_model = gp.create_geomodel(
    project_name='Model',
    extent=[xmin, xmax, ymin, ymax, zmin, zmax],
    resolution=[nx, ny, nz]
)
```

### Guidelines

| Parameter | Recommendation |
|-----------|---------------|
| extent | Extend 10-20% beyond data limits |
| resolution | Start with [50, 50, 25], increase for detail |

### Example: Calculating Extent from Data
```python
import numpy as np

# From surface points DataFrame
buffer = 0.1  # 10% buffer
x_range = points_df['X'].max() - points_df['X'].min()
y_range = points_df['Y'].max() - points_df['Y'].min()
z_range = points_df['Z'].max() - points_df['Z'].min()

extent = [
    points_df['X'].min() - buffer * x_range,
    points_df['X'].max() + buffer * x_range,
    points_df['Y'].min() - buffer * y_range,
    points_df['Y'].max() + buffer * y_range,
    points_df['Z'].min() - buffer * z_range,
    points_df['Z'].max() + buffer * z_range,
]
```

## CSV File Formats

### Surface Points CSV

```csv
X,Y,Z,surface
100.0,500.0,400.0,TopFormation
200.0,500.0,380.0,TopFormation
300.0,500.0,360.0,TopFormation
100.0,500.0,300.0,BaseFormation
200.0,500.0,280.0,BaseFormation
```

### Orientations CSV (Dip/Azimuth)

```csv
X,Y,Z,dip,azimuth,surface
150.0,500.0,390.0,15,90,TopFormation
250.0,500.0,290.0,20,90,BaseFormation
```

### Orientations CSV (Pole Vector)

```csv
X,Y,Z,Gx,Gy,Gz,surface
150.0,500.0,390.0,0.26,0.0,0.97,TopFormation
250.0,500.0,290.0,0.34,0.0,0.94,BaseFormation
```

### Loading CSV Files

```python
import pandas as pd

# Load surface points
points_df = pd.read_csv('surface_points.csv')
gp.add_surface_points(
    geo_model,
    x=points_df['X'],
    y=points_df['Y'],
    z=points_df['Z'],
    surface=points_df['surface']
)

# Load orientations (dip/azimuth format)
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

## Data Quality Guidelines

### Surface Points

| Issue | Problem | Solution |
|-------|---------|----------|
| Too few points | Poor surface fit | Add more points (min 3-5 per surface) |
| Clustered points | Local fitting only | Spread points across area |
| Inconsistent Z | Wavy surface | Check data source/units |
| Outside extent | Points ignored | Extend model extent |

### Orientations

| Issue | Problem | Solution |
|-------|---------|----------|
| Missing orientation | Model fails | Add at least 1 per surface |
| Wrong azimuth convention | Flipped dip | Check N=0 or N=360 convention |
| Conflicting orientations | Unstable model | Review field measurements |
| Orientation far from points | Poor local fit | Place orientation near points |

### Coordinate System

- **Consistency**: All data must use same coordinate system
- **Units**: Typically meters (check Z especially)
- **Origin**: Consider using local coordinates for stability

```python
# Shift to local coordinates
x_offset = points_df['X'].min()
y_offset = points_df['Y'].min()

points_df['X_local'] = points_df['X'] - x_offset
points_df['Y_local'] = points_df['Y'] - y_offset
```
