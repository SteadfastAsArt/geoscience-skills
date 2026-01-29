# Stereonet Projection Types

## Table of Contents
- [Overview](#overview)
- [Equal-Area (Schmidt Net)](#equal-area-schmidt-net)
- [Equal-Angle (Wulff Net)](#equal-angle-wulff-net)
- [Choosing a Projection](#choosing-a-projection)
- [Implementation in mplstereonet](#implementation-in-mplstereonet)

## Overview

Stereonets project 3D orientations onto a 2D circular plot. The two main projection types preserve different geometric properties:

| Property | Equal-Area | Equal-Angle |
|----------|------------|-------------|
| Preserves | Area ratios | Angular relationships |
| Distorts | Angles | Areas |
| Best for | Statistical analysis | Geometric constructions |
| Common name | Schmidt net | Wulff net |

## Equal-Area (Schmidt Net)

The default projection in mplstereonet. Also called Lambert azimuthal equal-area projection.

### Properties
- Areas on the sphere map to equal areas on the stereonet
- Density contours accurately represent concentration
- Preferred for statistical analysis of orientation data
- Standard in structural geology

### Mathematical Basis
```
For a point at spherical coordinates (azimuth, inclination):
  r = sqrt(2) * sin(inclination / 2)
  x = r * sin(azimuth)
  y = r * cos(azimuth)
```

### When to Use
- Pole density analysis
- Contour diagrams
- Statistical treatment of orientations
- Most structural geology applications

## Equal-Angle (Wulff Net)

Also called stereographic projection. Preserves angles at the cost of area distortion.

### Properties
- Circles on the sphere project as circles on the stereonet
- Great circles and small circles remain circular
- Angles measured on the stereonet equal angles on the sphere
- Areas are distorted (poles near rim appear dispersed)

### Mathematical Basis
```
For a point at spherical coordinates (azimuth, inclination):
  r = tan(inclination / 2)
  x = r * sin(azimuth)
  y = r * cos(azimuth)
```

### When to Use
- Geometric constructions
- Measuring angles between planes/lines
- Educational demonstrations
- Historical/traditional applications

## Choosing a Projection

### Use Equal-Area When:
- Analyzing pole distributions
- Creating density contours
- Comparing concentrations in different parts of the stereonet
- Performing statistical analysis (eigenvectors, mean vectors)
- Publishing in structural geology journals (standard practice)

### Use Equal-Angle When:
- Measuring angles between features
- Performing geometric constructions
- Teaching stereonet fundamentals
- Working with historical data plotted on Wulff nets

## Implementation in mplstereonet

### Default (Equal-Area)
```python
import mplstereonet
import matplotlib.pyplot as plt

# Default is equal-area (lower hemisphere)
fig, ax = mplstereonet.subplots()
```

### Explicit Projection Selection
```python
# Equal-area projection (default)
fig = plt.figure()
ax = fig.add_subplot(111, projection='stereonet')

# Or using the convenience function
fig, ax = mplstereonet.subplots(projection='equal_area_stereonet')
```

### Upper vs Lower Hemisphere
```python
# Lower hemisphere (default, standard in structural geology)
fig, ax = mplstereonet.subplots()

# Upper hemisphere (less common)
# Note: mplstereonet uses lower hemisphere by convention
```

## Comparison Example

```python
import mplstereonet
import matplotlib.pyplot as plt
import numpy as np

# Sample data
np.random.seed(42)
strikes = np.random.normal(90, 20, 50)
dips = np.random.normal(45, 10, 50)

fig, ax = mplstereonet.subplots()

# Plot poles and contours
ax.density_contourf(strikes, dips, measurement='poles', cmap='Reds')
ax.pole(strikes, dips, 'k.', markersize=4)

ax.grid()
ax.set_title('Equal-Area Projection (Standard)')
plt.savefig('projection_comparison.png', dpi=150)
```

## Visual Differences

### Equal-Area
- Density contours are directly proportional to data concentration
- Uniform distribution appears uniform on plot
- Standard for quantitative analysis

### Equal-Angle
- Poles near the rim appear more spread out
- Same density of poles covers larger area near rim
- Can mislead statistical interpretation

## Best Practices

1. **Always use equal-area** for density analysis and statistics
2. **State projection type** in figure captions
3. **Use lower hemisphere** convention (standard in structural geology)
4. **mplstereonet default** is equal-area lower hemisphere - no changes needed
