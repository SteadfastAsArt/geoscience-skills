# Plotting Options and Customization

## Table of Contents
- [Basic Styling](#basic-styling)
- [Plane Plotting](#plane-plotting)
- [Pole Plotting](#pole-plotting)
- [Line Plotting](#line-plotting)
- [Density Contours](#density-contours)
- [Grid and Labels](#grid-and-labels)
- [Multiple Datasets](#multiple-datasets)
- [Figure Layout](#figure-layout)
- [Export Options](#export-options)

## Basic Styling

All plotting functions accept standard matplotlib styling parameters.

```python
import mplstereonet
import matplotlib.pyplot as plt

fig, ax = mplstereonet.subplots(figsize=(8, 8))

# Common style parameters
ax.plane(45, 60, color='red', linewidth=2, linestyle='--', alpha=0.7)
ax.pole(45, 60, color='blue', marker='o', markersize=10, label='Bedding')

ax.grid()
ax.legend()
plt.savefig('styled_stereonet.png', dpi=150, bbox_inches='tight')
```

## Plane Plotting

### Line Styles
```python
# Solid line (default)
ax.plane(45, 60, 'b-')

# Dashed line
ax.plane(90, 45, 'r--')

# Dotted line
ax.plane(135, 30, 'g:')

# Custom styling
ax.plane(180, 50, color='purple', linewidth=3, linestyle='-.')
```

### Multiple Planes
```python
strikes = [45, 90, 135, 180]
dips = [30, 45, 60, 75]

# Plot each with same style
for s, d in zip(strikes, dips):
    ax.plane(s, d, 'b-', linewidth=0.5, alpha=0.5)

# Or use different colors
colors = ['red', 'blue', 'green', 'orange']
for s, d, c in zip(strikes, dips, colors):
    ax.plane(s, d, color=c, linewidth=2)
```

## Pole Plotting

### Marker Styles
```python
# Circle (default)
ax.pole(45, 60, 'ko')

# Triangle
ax.pole(90, 45, 'r^')

# Square
ax.pole(135, 30, 'bs')

# Diamond
ax.pole(180, 50, 'gD')

# Custom
ax.pole(225, 40, marker='*', color='purple', markersize=15,
        markeredgecolor='black', markeredgewidth=1)
```

### Common Marker Options
| Marker | Symbol | Description |
|--------|--------|-------------|
| `o` | Circle | Default for poles |
| `^` | Triangle up | Lineations |
| `v` | Triangle down | Alternate |
| `s` | Square | Joint sets |
| `D` | Diamond | Special features |
| `*` | Star | Mean orientations |
| `+` | Plus | Cross-cutting |
| `x` | X | Alternate |

## Line Plotting

### Lineation Markers
```python
# Trend/plunge data
trends = [120, 125, 118, 130]
plunges = [15, 20, 12, 25]

# Triangle markers (common for lineations)
ax.line(trends, plunges, 'r^', markersize=8)

# With arrows (indicate direction)
ax.line(trends, plunges, marker='>', markersize=10, color='red')
```

## Density Contours

### Contour Types
```python
# Filled contours (default)
ax.density_contourf(strikes, dips, measurement='poles', cmap='Reds')

# Line contours only
ax.density_contour(strikes, dips, measurement='poles', colors='black')

# Both together
ax.density_contourf(strikes, dips, measurement='poles', cmap='Blues', alpha=0.7)
ax.density_contour(strikes, dips, measurement='poles', colors='black', linewidths=0.5)
```

### Contouring Methods
```python
# Kamb (default) - statistical significance
ax.density_contourf(strikes, dips, measurement='poles', method='kamb')

# Schmidt - point counting
ax.density_contourf(strikes, dips, measurement='poles', method='schmidt')

# Exponential Kamb - smoothed
ax.density_contourf(strikes, dips, measurement='poles', method='exponential_kamb')
```

### Measurement Types
```python
# Poles to planes (default)
ax.density_contourf(strikes, dips, measurement='poles')

# Lines (for lineation data)
ax.density_contourf(trends, plunges, measurement='lines')
```

### Colormap Options
```python
# Sequential colormaps (good for density)
ax.density_contourf(strikes, dips, cmap='Reds')
ax.density_contourf(strikes, dips, cmap='Blues')
ax.density_contourf(strikes, dips, cmap='Greys')
ax.density_contourf(strikes, dips, cmap='YlOrRd')

# With colorbar
cax = ax.density_contourf(strikes, dips, cmap='Reds')
fig.colorbar(cax, label='Density')
```

### Contour Levels
```python
# Specific number of levels
ax.density_contourf(strikes, dips, levels=10)

# Custom levels
ax.density_contourf(strikes, dips, levels=[1, 2, 3, 5, 8, 13])
```

## Grid and Labels

### Grid Options
```python
# Default grid
ax.grid()

# Custom grid
ax.grid(color='gray', linestyle=':', linewidth=0.5, alpha=0.5)

# No grid
# Simply don't call ax.grid()
```

### Title and Labels
```python
ax.set_title('Bedding Orientations', fontsize=14, fontweight='bold')

# Azimuth labels are automatic
# To customize compass directions, use matplotlib text
ax.text(0, 1.05, 'N', ha='center', va='bottom', transform=ax.transAxes)
```

## Multiple Datasets

### Color-Coded Sets
```python
datasets = {
    'Bedding': {'strikes': [45, 50, 42], 'dips': [30, 35, 28], 'color': 'blue'},
    'Joint Set 1': {'strikes': [135, 140, 130], 'dips': [70, 75, 68], 'color': 'red'},
    'Joint Set 2': {'strikes': [225, 230, 220], 'dips': [60, 65, 58], 'color': 'green'},
}

fig, ax = mplstereonet.subplots()

for name, data in datasets.items():
    ax.pole(data['strikes'], data['dips'],
            marker='o', color=data['color'], markersize=8, label=name)

ax.grid()
ax.legend(loc='upper left')
```

### Subplots
```python
fig, axes = plt.subplots(1, 3, figsize=(15, 5),
                         subplot_kw={'projection': 'stereonet'})

# Plot different datasets on each
axes[0].pole(bedding_s, bedding_d, 'bo')
axes[0].set_title('Bedding')

axes[1].pole(joints1_s, joints1_d, 'ro')
axes[1].set_title('Joint Set 1')

axes[2].pole(joints2_s, joints2_d, 'go')
axes[2].set_title('Joint Set 2')

for ax in axes:
    ax.grid()

plt.tight_layout()
```

## Figure Layout

### Figure Size
```python
# Square (standard)
fig, ax = mplstereonet.subplots(figsize=(8, 8))

# For publications
fig, ax = mplstereonet.subplots(figsize=(6, 6))
```

### Tight Layout
```python
plt.tight_layout()
# or
plt.savefig('output.png', bbox_inches='tight')
```

## Export Options

### File Formats
```python
# PNG (raster, good for presentations)
plt.savefig('stereonet.png', dpi=300, bbox_inches='tight')

# PDF (vector, good for publications)
plt.savefig('stereonet.pdf', bbox_inches='tight')

# SVG (vector, good for editing)
plt.savefig('stereonet.svg', bbox_inches='tight')
```

### Resolution
```python
# Screen/web (72-150 dpi)
plt.savefig('stereonet_web.png', dpi=150)

# Print/publication (300+ dpi)
plt.savefig('stereonet_print.png', dpi=300)
```

### Transparent Background
```python
plt.savefig('stereonet.png', transparent=True, dpi=300)
```

## Complete Example

```python
import mplstereonet
import matplotlib.pyplot as plt
import numpy as np

# Data
np.random.seed(42)
bedding_strikes = np.random.normal(45, 10, 30)
bedding_dips = np.random.normal(35, 5, 30)

fig, ax = mplstereonet.subplots(figsize=(8, 8))

# Density contours
cax = ax.density_contourf(bedding_strikes, bedding_dips,
                          measurement='poles', cmap='Reds', alpha=0.7)

# Poles
ax.pole(bedding_strikes, bedding_dips, 'ko', markersize=5, alpha=0.7)

# Mean orientation
mean_s, mean_d = mplstereonet.fit_girdle(bedding_strikes, bedding_dips)
ax.pole(mean_s, mean_d, 'r*', markersize=15, label='Mean pole')
ax.plane(mean_s, mean_d, 'r-', linewidth=2, label='Mean plane')

# Formatting
ax.grid(color='gray', linestyle=':', linewidth=0.5)
ax.legend(loc='upper left')
ax.set_title('Bedding Orientations\nn=30', fontsize=12)

# Colorbar
cbar = fig.colorbar(cax, ax=ax, shrink=0.7, label='Density')

plt.savefig('complete_stereonet.png', dpi=300, bbox_inches='tight')
```
