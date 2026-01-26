---
name: pyvista
description: 3D visualization and mesh analysis for geoscience data. Create publication-quality 3D plots of geological models, seismic volumes, point clouds, and geophysical data.
---

# PyVista - 3D Visualization

Help users create 3D visualizations of geoscience data using PyVista.

## Installation

```bash
pip install pyvista
# For Jupyter support
pip install pyvista[jupyter]
```

## Core Concepts

### What PyVista Does
- 3D mesh visualization and analysis
- Volume rendering for seismic/CT data
- Point cloud visualization
- Surface and grid plotting
- Export to VTK, STL, OBJ formats

### Key Classes
| Class | Purpose |
|-------|---------|
| `pv.Plotter` | Main visualization window |
| `pv.PolyData` | Surface meshes, point clouds |
| `pv.StructuredGrid` | Regular 3D grids |
| `pv.UnstructuredGrid` | Irregular meshes |
| `pv.ImageData` | 3D voxel data (seismic) |

## Common Workflows

### 1. Basic 3D Plot
```python
import pyvista as pv
import numpy as np

# Create a simple surface
x = np.arange(-10, 10, 0.5)
y = np.arange(-10, 10, 0.5)
x, y = np.meshgrid(x, y)
z = np.sin(np.sqrt(x**2 + y**2))

# Create structured grid
grid = pv.StructuredGrid(x, y, z)

# Plot
plotter = pv.Plotter()
plotter.add_mesh(grid, scalars=z.ravel(), cmap='terrain')
plotter.show()
```

### 2. Visualize Point Cloud
```python
import pyvista as pv
import numpy as np

# Sample points (e.g., well locations, earthquake locations)
points = np.random.rand(1000, 3) * 100
values = points[:, 2]  # Color by depth

# Create point cloud
cloud = pv.PolyData(points)
cloud['depth'] = values

# Plot
plotter = pv.Plotter()
plotter.add_mesh(cloud,
                 scalars='depth',
                 point_size=5,
                 render_points_as_spheres=True,
                 cmap='viridis')
plotter.show()
```

### 3. Load and Display Geological Model
```python
import pyvista as pv

# Load VTK file (from GemPy, LoopStructural, etc.)
mesh = pv.read('geological_model.vtk')

# Plot with geological colors
plotter = pv.Plotter()
plotter.add_mesh(mesh, scalars='lithology', cmap='Set1')
plotter.add_axes()
plotter.show_bounds(grid='front')
plotter.show()
```

### 4. Volume Rendering (Seismic Cube)
```python
import pyvista as pv
import numpy as np

# Create 3D seismic volume
nx, ny, nz = 100, 100, 50
data = np.random.randn(nx, ny, nz)

# Create ImageData (uniform grid)
grid = pv.ImageData()
grid.dimensions = (nx + 1, ny + 1, nz + 1)
grid.spacing = (25, 25, 10)  # Cell size in meters
grid.origin = (0, 0, -500)   # Top of volume
grid.cell_data['amplitude'] = data.ravel(order='F')

# Volume render
plotter = pv.Plotter()
plotter.add_volume(grid,
                   scalars='amplitude',
                   cmap='seismic',
                   opacity='sigmoid')
plotter.show()
```

### 5. Slice Through Volume
```python
import pyvista as pv

# Load volume
volume = pv.read('seismic_volume.vti')

# Create slices
slice_x = volume.slice(normal='x', origin=volume.center)
slice_y = volume.slice(normal='y', origin=volume.center)
slice_z = volume.slice(normal='z', origin=volume.center)

# Plot
plotter = pv.Plotter()
plotter.add_mesh(slice_x, cmap='seismic')
plotter.add_mesh(slice_y, cmap='seismic')
plotter.add_mesh(slice_z, cmap='seismic')
plotter.show()
```

### 6. Contour Surfaces (Isosurfaces)
```python
import pyvista as pv

# Load 3D data
grid = pv.read('model.vti')

# Extract isosurfaces
contours = grid.contour([0.5, 1.0, 1.5], scalars='values')

# Plot
plotter = pv.Plotter()
plotter.add_mesh(contours, opacity=0.5, cmap='coolwarm')
plotter.show()
```

### 7. Well Path Visualization
```python
import pyvista as pv
import numpy as np

# Well path coordinates
md = np.linspace(0, 3000, 100)  # Measured depth
x = np.sin(md / 500) * 100
y = np.cos(md / 500) * 100
z = -md

# Create spline through points
points = np.column_stack([x, y, z])
spline = pv.Spline(points, 500)

# Add as tube for visibility
tube = spline.tube(radius=5)

# Plot
plotter = pv.Plotter()
plotter.add_mesh(tube, color='brown', label='Well')
plotter.add_legend()
plotter.show()
```

### 8. Combine Multiple Surfaces
```python
import pyvista as pv

# Load geological horizons
horizon1 = pv.read('top_reservoir.vtk')
horizon2 = pv.read('base_reservoir.vtk')
fault = pv.read('fault_surface.vtk')

# Plot together
plotter = pv.Plotter()
plotter.add_mesh(horizon1, color='gold', opacity=0.7, label='Top')
plotter.add_mesh(horizon2, color='blue', opacity=0.7, label='Base')
plotter.add_mesh(fault, color='red', opacity=0.5, label='Fault')
plotter.add_legend()
plotter.show_axes()
plotter.show()
```

### 9. Export for Publication
```python
import pyvista as pv

mesh = pv.read('model.vtk')

plotter = pv.Plotter(off_screen=True)
plotter.add_mesh(mesh, cmap='terrain')
plotter.camera_position = 'iso'
plotter.add_axes()

# Save high-resolution image
plotter.screenshot('figure.png', scale=3)

# Save interactive HTML
plotter.export_html('interactive_model.html')
```

### 10. Clip and Threshold
```python
import pyvista as pv

grid = pv.read('model.vti')

# Clip with plane
clipped = grid.clip(normal='z', origin=(0, 0, -100))

# Threshold by value
thresholded = grid.threshold([0.5, 1.5], scalars='porosity')

plotter = pv.Plotter()
plotter.add_mesh(thresholded, cmap='viridis')
plotter.show()
```

### 11. Create Geological Cross-Section
```python
import pyvista as pv
import numpy as np

# Define section line
point_a = [0, 0, 0]
point_b = [1000, 500, 0]

# Load 3D model
model = pv.read('geological_model.vtk')

# Slice along line
section = model.slice(normal='y', origin=model.center)

# Plot as 2D view
plotter = pv.Plotter()
plotter.add_mesh(section, scalars='lithology', cmap='Set2')
plotter.view_xz()  # View as cross-section
plotter.show()
```

### 12. Animate Rotation
```python
import pyvista as pv

mesh = pv.read('model.vtk')

plotter = pv.Plotter(off_screen=True)
plotter.add_mesh(mesh, cmap='terrain')
plotter.open_gif('rotation.gif')

# Rotate and capture frames
for angle in range(0, 360, 5):
    plotter.camera.azimuth = angle
    plotter.write_frame()

plotter.close()
```

## File Format Support

| Format | Extension | Read | Write |
|--------|-----------|------|-------|
| VTK Legacy | .vtk | ✓ | ✓ |
| VTK XML | .vtu, .vti, .vtp | ✓ | ✓ |
| STL | .stl | ✓ | ✓ |
| OBJ | .obj | ✓ | ✓ |
| PLY | .ply | ✓ | ✓ |
| GLTF | .gltf | ✓ | ✓ |

## Color Maps for Geoscience

| Map | Use Case |
|-----|----------|
| `terrain` | Topography, elevation |
| `seismic` | Seismic amplitudes |
| `viridis` | General scientific |
| `RdYlBu` | Diverging data |
| `Set1`, `Set2` | Categorical (lithology) |

## Tips

1. **Use `off_screen=True`** for batch processing
2. **Add axes and scale bar** for publication figures
3. **Export to HTML** for interactive sharing
4. **Use opacity** to show internal structure
5. **Combine with GemPy/LoopStructural** for geological models

## Resources

- Documentation: https://docs.pyvista.org/
- GitHub: https://github.com/pyvista/pyvista
- Examples: https://docs.pyvista.org/examples/
- Gallery: https://docs.pyvista.org/gallery/
