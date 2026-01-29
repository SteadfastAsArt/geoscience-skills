# PyVista Plotting and Rendering Options

## Table of Contents
- [Plotter Setup](#plotter-setup)
- [add_mesh Options](#add_mesh-options)
- [Camera Control](#camera-control)
- [Lighting](#lighting)
- [Color Maps](#color-maps)
- [Annotations](#annotations)
- [Export Options](#export-options)
- [Multi-View Plots](#multi-view-plots)

## Plotter Setup

### Basic Plotter
```python
import pyvista as pv

# Interactive window
plotter = pv.Plotter()

# Off-screen rendering (for scripts)
plotter = pv.Plotter(off_screen=True)

# Window size
plotter = pv.Plotter(window_size=[1920, 1080])

# Background color
plotter = pv.Plotter()
plotter.set_background('white')
plotter.set_background('white', top='lightblue')  # Gradient
```

### Plotter Parameters
| Parameter | Description | Default |
|-----------|-------------|---------|
| `off_screen` | No display window | `False` |
| `window_size` | [width, height] in pixels | `[1024, 768]` |
| `shape` | Grid of subplots (rows, cols) | `(1, 1)` |
| `border` | Show subplot borders | `False` |
| `lighting` | Enable lighting | `'light_kit'` |

## add_mesh Options

### Basic Options
```python
plotter.add_mesh(
    mesh,
    color='white',           # Solid color
    scalars='property',      # Color by data array
    cmap='viridis',          # Color map
    clim=[0, 100],           # Color limits
    opacity=1.0,             # 0-1 transparency
    style='surface',         # 'surface', 'wireframe', 'points'
    show_edges=False,        # Show mesh edges
    edge_color='black',
    line_width=1,
    point_size=5,
    label='Layer 1',         # For legend
)
```

### Surface Options
| Parameter | Description | Values |
|-----------|-------------|--------|
| `style` | Rendering style | `'surface'`, `'wireframe'`, `'points'` |
| `show_edges` | Display mesh edges | `True`/`False` |
| `smooth_shading` | Interpolate colors | `True`/`False` |
| `pbr` | Physically based rendering | `True`/`False` |
| `metallic` | PBR metallic factor | 0.0-1.0 |
| `roughness` | PBR roughness factor | 0.0-1.0 |

### Point Cloud Options
```python
plotter.add_mesh(
    cloud,
    render_points_as_spheres=True,
    point_size=10,
    scalars='depth',
)
```

### Scalar Bar Options
```python
plotter.add_mesh(
    mesh,
    scalars='values',
    scalar_bar_args={
        'title': 'Porosity (%)',
        'vertical': True,
        'position_x': 0.85,
        'position_y': 0.1,
        'width': 0.1,
        'height': 0.8,
        'n_labels': 5,
        'fmt': '%.2f',
    }
)
```

## Camera Control

### Preset Views
```python
plotter.view_xy()        # Top-down
plotter.view_xz()        # Front
plotter.view_yz()        # Side
plotter.view_isometric() # Isometric
plotter.camera_position = 'iso'  # Same as isometric
```

### Custom Camera
```python
# Set camera position
plotter.camera_position = [
    (x, y, z),           # Camera location
    (fx, fy, fz),        # Focal point
    (ux, uy, uz),        # View up vector
]

# Example: View from above looking at center
plotter.camera_position = [
    (500, 500, 1000),    # Camera above
    (500, 500, 0),       # Looking at origin
    (0, 1, 0),           # Y is up
]

# Zoom
plotter.camera.zoom(1.5)

# Reset to fit all
plotter.reset_camera()
```

### Save/Restore Camera
```python
# Save position
pos = plotter.camera_position

# Restore later
plotter.camera_position = pos
```

## Lighting

### Light Kit (Default)
```python
plotter = pv.Plotter(lighting='light_kit')
```

### Custom Lights
```python
# Add directional light
light = pv.Light(
    position=(1, 1, 1),
    focal_point=(0, 0, 0),
    color='white',
    intensity=0.5,
)
plotter.add_light(light)

# Remove all lights
plotter.remove_all_lights()
```

### Ambient/Diffuse
```python
plotter.add_mesh(
    mesh,
    ambient=0.3,     # Ambient lighting
    diffuse=0.7,     # Diffuse lighting
    specular=0.5,    # Specular highlights
    specular_power=20,
)
```

## Color Maps

### Geoscience Color Maps
| Map | Use Case |
|-----|----------|
| `terrain` | Topography, elevation |
| `gist_earth` | Earth tones |
| `seismic` | Seismic amplitudes (diverging) |
| `RdBu`, `RdYlBu` | Diverging data |
| `viridis` | General scientific |
| `plasma`, `magma` | Perceptually uniform |
| `Set1`, `Set2`, `tab10` | Categorical data |

### Custom Color Map
```python
import matplotlib.pyplot as plt
from matplotlib.colors import LinearSegmentedColormap

# Create custom colormap
colors = ['blue', 'white', 'red']
cmap = LinearSegmentedColormap.from_list('custom', colors)

plotter.add_mesh(mesh, cmap=cmap)
```

### Categorical Colors
```python
# For lithology codes
plotter.add_mesh(
    mesh,
    scalars='lithology',
    cmap='Set1',
    n_colors=8,  # Number of categories
)
```

## Annotations

### Axes
```python
# Simple axes
plotter.add_axes()

# Customized axes
plotter.add_axes(
    xlabel='Easting (m)',
    ylabel='Northing (m)',
    zlabel='Depth (m)',
    line_width=2,
)

# Axes widget (interactive)
plotter.show_axes()
```

### Bounds/Grid
```python
# Show bounding box with labels
plotter.show_bounds(
    grid='front',
    location='outer',
    xlabel='X (m)',
    ylabel='Y (m)',
    zlabel='Z (m)',
)
```

### Text
```python
# Title
plotter.add_title('Geological Model', font_size=16)

# Text annotation
plotter.add_text('Well A', position='upper_left', font_size=12)

# 3D text at point
plotter.add_point_labels(
    points,
    labels,
    font_size=12,
    point_color='red',
    point_size=10,
)
```

### Legend
```python
plotter.add_mesh(mesh1, color='red', label='Fault')
plotter.add_mesh(mesh2, color='blue', label='Horizon')
plotter.add_legend()
```

### Scale Bar
```python
plotter.add_scalar_bar(title='Porosity', vertical=True)
```

## Export Options

### Screenshots
```python
# Basic screenshot
plotter.screenshot('output.png')

# High resolution
plotter.screenshot('output.png', scale=3)

# Transparent background
plotter.screenshot('output.png', transparent_background=True)
```

### Vector Graphics
```python
# SVG export
plotter.save_graphic('output.svg')

# PDF export
plotter.save_graphic('output.pdf')

# EPS export
plotter.save_graphic('output.eps')
```

### Interactive HTML
```python
# Export to standalone HTML
plotter.export_html('model.html')
```

### Animation/GIF
```python
plotter = pv.Plotter(off_screen=True)
plotter.add_mesh(mesh)
plotter.open_gif('animation.gif')

for angle in range(0, 360, 5):
    plotter.camera.azimuth = angle
    plotter.write_frame()

plotter.close()
```

### Movie
```python
plotter.open_movie('animation.mp4', framerate=24)
# ... write frames ...
plotter.close()
```

## Multi-View Plots

### Subplots
```python
plotter = pv.Plotter(shape=(2, 2))

plotter.subplot(0, 0)
plotter.add_mesh(mesh1)
plotter.add_title('View 1')

plotter.subplot(0, 1)
plotter.add_mesh(mesh2)
plotter.add_title('View 2')

plotter.subplot(1, 0)
plotter.add_mesh(mesh3)
plotter.add_title('View 3')

plotter.subplot(1, 1)
plotter.add_mesh(mesh4)
plotter.add_title('View 4')

plotter.link_views()  # Sync camera across subplots
plotter.show()
```

### Different Shapes
```python
# 1 row, 3 columns
plotter = pv.Plotter(shape=(1, 3))

# Custom layout
plotter = pv.Plotter(shape='1|2')  # 1 on left, 2 stacked on right
```

## Jupyter Integration

```python
# Enable Jupyter backend
pv.set_jupyter_backend('trame')

# Or use static images
pv.set_jupyter_backend('static')

# Interactive in notebook
plotter = pv.Plotter(notebook=True)
plotter.add_mesh(mesh)
plotter.show()
```
