---
name: mplstereonet
description: Stereonet plots for structural geology using matplotlib. Create lower-hemisphere stereographic projections for orientation data, contour pole densities, and calculate statistics.
---

# mplstereonet - Stereonets for Matplotlib

Help users create stereographic projections for structural geology data.

## Installation

```bash
pip install mplstereonet
```

## Core Concepts

### What mplstereonet Does
- Lower-hemisphere stereographic projections
- Plot planes as great circles
- Plot lines as points
- Density contours for pole distributions
- Calculate mean orientations and statistics
- Rake/plunge conversions

### Convention
- Uses **strike/dip** (right-hand rule) for planes
- Uses **trend/plunge** for lines
- Lower-hemisphere, equal-area projection

## Common Workflows

### 1. Basic Stereonet
```python
import mplstereonet
import matplotlib.pyplot as plt

# Create stereonet
fig, ax = mplstereonet.subplots()

# Plot a plane (strike/dip)
ax.plane(315, 45)  # Strike 315°, dip 45°

# Plot the pole to the plane
ax.pole(315, 45)

# Plot a line (trend/plunge)
ax.line(120, 30)  # Trend 120°, plunge 30°

ax.grid()
plt.show()
```

### 2. Multiple Measurements
```python
import mplstereonet
import matplotlib.pyplot as plt
import numpy as np

# Sample bedding data (strike, dip)
strikes = [45, 52, 38, 48, 55, 41, 50, 43]
dips = [25, 30, 22, 28, 35, 24, 32, 27]

fig, ax = mplstereonet.subplots()

# Plot all planes as great circles
for s, d in zip(strikes, dips):
    ax.plane(s, d, 'b-', linewidth=0.5)

# Plot poles
ax.pole(strikes, dips, 'ko', markersize=5)

ax.grid()
ax.set_title('Bedding Orientations')
plt.show()
```

### 3. Density Contours
```python
import mplstereonet
import matplotlib.pyplot as plt
import numpy as np

# Generate synthetic foliation data
np.random.seed(42)
strikes = np.random.normal(270, 15, 100)
dips = np.random.normal(60, 10, 100)

fig, ax = mplstereonet.subplots()

# Contour pole density
ax.density_contourf(strikes, dips, measurement='poles', cmap='Reds')
ax.pole(strikes, dips, 'k.', markersize=3, alpha=0.5)

ax.grid()
ax.set_title('Pole Density Contours')
plt.show()
```

### 4. Calculate Mean Orientation
```python
import mplstereonet
import matplotlib.pyplot as plt
import numpy as np

strikes = [45, 52, 38, 48, 55, 41, 50, 43]
dips = [25, 30, 22, 28, 35, 24, 32, 27]

# Calculate mean plane
mean_strike, mean_dip = mplstereonet.fit_girdle(strikes, dips)
print(f"Mean orientation: {mean_strike:.1f}/{mean_dip:.1f}")

# Or calculate mean pole (for clustered data)
lon, lat = mplstereonet.pole(strikes, dips)
mean_lon, mean_lat = mplstereonet.find_mean_vector(lon, lat)
mean_s, mean_d = mplstereonet.pole2strike(mean_lon, mean_lat)

fig, ax = mplstereonet.subplots()
ax.pole(strikes, dips, 'ko', markersize=5)
ax.pole(mean_strike, mean_dip, 'r^', markersize=10, label='Mean')
ax.legend()
ax.grid()
plt.show()
```

### 5. Lineations (Trend/Plunge)
```python
import mplstereonet
import matplotlib.pyplot as plt

# Lineation data (trend, plunge)
trends = [125, 130, 118, 135, 128, 122]
plunges = [15, 20, 12, 25, 18, 14]

fig, ax = mplstereonet.subplots()

# Plot lineations
ax.line(trends, plunges, 'b^', markersize=8)

# Contour lineation density
ax.density_contourf(trends, plunges, measurement='lines', cmap='Blues')

ax.grid()
ax.set_title('Lineation Orientations')
plt.show()
```

### 6. Fault Plane with Slip Direction
```python
import mplstereonet
import matplotlib.pyplot as plt

# Fault plane (strike/dip)
fault_strike = 45
fault_dip = 60

# Slickenline (rake on fault plane)
rake = 30  # Degrees from strike

# Convert rake to trend/plunge
slip_trend, slip_plunge = mplstereonet.rake(fault_strike, fault_dip, rake)

fig, ax = mplstereonet.subplots()

# Plot fault plane
ax.plane(fault_strike, fault_dip, 'r-', linewidth=2, label='Fault')

# Plot slip vector
ax.line(slip_trend, slip_plunge, 'r>', markersize=10, label='Slip direction')

ax.grid()
ax.legend()
plt.show()
```

### 7. Pi-Diagram (Fold Axis)
```python
import mplstereonet
import matplotlib.pyplot as plt
import numpy as np

# Bedding measurements around a fold
strikes = np.array([20, 35, 50, 70, 90, 110, 130, 150, 165, 180])
dips = np.array([45, 40, 35, 30, 25, 30, 35, 40, 45, 50])

fig, ax = mplstereonet.subplots()

# Plot poles to bedding
ax.pole(strikes, dips, 'ko', markersize=6)

# Fit a great circle (girdle) to the poles
girdle_strike, girdle_dip = mplstereonet.fit_girdle(strikes, dips)
ax.plane(girdle_strike, girdle_dip, 'r-', linewidth=2, label='Best-fit girdle')

# Fold axis is the pole to the girdle
fold_trend, fold_plunge = mplstereonet.pole(girdle_strike, girdle_dip)
ax.line(fold_trend, fold_plunge, 'r^', markersize=12, label='Fold axis')

print(f"Fold axis: {fold_trend:.0f}/{fold_plunge:.0f}")

ax.grid()
ax.legend()
plt.show()
```

### 8. Confidence Cone
```python
import mplstereonet
import matplotlib.pyplot as plt
import numpy as np

strikes = np.random.normal(90, 10, 50)
dips = np.random.normal(45, 5, 50)

# Calculate eigenvalues for confidence
lon, lat = mplstereonet.pole(strikes, dips)
eigenvecs, eigenvals = mplstereonet.eigenvectors(lon, lat)

# K value (measure of clustering)
K = np.log(eigenvals[0] / eigenvals[1])
print(f"K value (clustering): {K:.2f}")

fig, ax = mplstereonet.subplots()
ax.pole(strikes, dips, 'ko', markersize=4)
ax.density_contour(strikes, dips, measurement='poles')
ax.grid()
plt.show()
```

### 9. Multiple Datasets
```python
import mplstereonet
import matplotlib.pyplot as plt

# Two different joint sets
set1_strikes = [45, 50, 42, 48, 55]
set1_dips = [70, 75, 68, 72, 78]

set2_strikes = [135, 140, 130, 138, 142]
set2_dips = [60, 65, 58, 62, 68]

fig, ax = mplstereonet.subplots()

# Plot each set with different colors
ax.pole(set1_strikes, set1_dips, 'ro', markersize=8, label='Set 1')
ax.pole(set2_strikes, set2_dips, 'bs', markersize=8, label='Set 2')

# Plot mean planes
for strikes, dips, color in [(set1_strikes, set1_dips, 'r'),
                              (set2_strikes, set2_dips, 'b')]:
    mean_s, mean_d = mplstereonet.fit_girdle(strikes, dips)
    ax.plane(mean_s, mean_d, color + '-', linewidth=2)

ax.grid()
ax.legend()
plt.show()
```

### 10. Rose Diagram
```python
import mplstereonet
import matplotlib.pyplot as plt
import numpy as np

# Strike measurements
strikes = np.random.normal(45, 20, 100)

# Create rose diagram
fig = plt.figure()
ax = fig.add_subplot(111, projection='polar')

# Bin strikes
bins = np.arange(0, 361, 10)
counts, _ = np.histogram(strikes, bins=bins)

# Plot as bars
bars = ax.bar(np.radians(bins[:-1]), counts, width=np.radians(10),
              bottom=0, alpha=0.7)

ax.set_theta_zero_location('N')
ax.set_theta_direction(-1)
plt.title('Strike Rose Diagram')
plt.show()
```

### 11. Kamb Contours
```python
import mplstereonet
import matplotlib.pyplot as plt

fig, ax = mplstereonet.subplots()

# Kamb contouring (statistical significance)
ax.density_contourf(strikes, dips, measurement='poles',
                    method='kamb', cmap='Reds')
ax.pole(strikes, dips, 'k.', markersize=3)

ax.grid()
plt.show()
```

### 12. Convert Between Formats
```python
import mplstereonet

# Strike/dip to dip direction/dip
strike, dip = 45, 60
dip_direction = (strike + 90) % 360

# Pole to strike/dip
lon, lat = mplstereonet.pole(strike, dip)
back_strike, back_dip = mplstereonet.pole2strike(lon, lat)

# Trend/plunge to strike/dip (treating line as pole)
trend, plunge = 135, 45
strike, dip = mplstereonet.line(trend, plunge)
```

## Measurement Conventions

| Format | Description | Example |
|--------|-------------|---------|
| Strike/Dip | Right-hand rule | 045/60 |
| Dip Direction/Dip | Azimuth of dip | 135/60 |
| Trend/Plunge | Linear orientation | 180/30 |

## Contouring Methods

| Method | Description |
|--------|-------------|
| `kamb` | Statistical significance (default) |
| `schmidt` | Point counting |
| `exponential_kamb` | Smoothed Kamb |

## Tips

1. **Right-hand rule** - Dip is to the right of strike
2. **Convert dip direction** - Subtract 90° for strike
3. **Use density contours** for large datasets
4. **Fit girdle** for folded or dispersed data
5. **Calculate K value** to quantify clustering

## Resources

- GitHub: https://github.com/joferkington/mplstereonet
- Examples: https://github.com/joferkington/mplstereonet/tree/master/examples
- Matplotlib projections: https://matplotlib.org/stable/api/projections_api.html
