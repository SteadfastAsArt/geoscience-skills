---
name: geological-modelling
description: |
  3D geological modelling workflow from spatial data preparation through
  implicit surface modelling and 3D visualization. Use when building
  geological models from surface data, boreholes, or GIS inputs.
license: MIT
metadata:
  skill_type: workflow
  version: 1.0.2
  author: Geoscience Skills
  tags: '["Geological Modelling", "3D", "Implicit Surfaces", "GIS", "Workflow"]'
  dependencies: '["gemgis", "gempy==2026.0.3", "gempy-engine==2026.0.3.post1", "pyvista==0.49.0"]'
  complements: '["gemgis", "gempy", "loopstructural", "pyvista"]'
  workflow_role: modelling
---

# Geological Modelling Workflow

End-to-end pipeline for building 3D geological models from spatial data,
covering GIS data preparation, implicit surface modelling, and 3D visualization.

## Skill Chain

```text
gemgis              gempy / loopstructural       pyvista
[GIS Preprocessing] --> [Implicit Modelling]     --> [3D Visualization]
  |                      |                           |
  Shapefile parsing      Surface interpolation       Volume render
  Raster extraction      Fault modelling             Cross-sections
  Borehole to points     Unconformities              Mesh export
  CRS transforms         Scalar field solving        Interactive pick
```

## Decision Points: GemPy vs LoopStructural

| Criterion | GemPy | LoopStructural |
|-----------|-------|----------------|
| Standard layer-cake geology | Preferred | Works |
| Complex folding (refolded folds) | Limited | Preferred (structural frames) |
| Fault networks | Good | Good |
| Built-in gravity forward model | Yes | No |
| Learning curve | Gentler | Steeper |
| Data input | Points + orientations | Points + orientations + fold constraints |
| Unconformities | ERODE / ONLAP types | Supported |
| API style | Functional (`gp.compute_model`) | Object-oriented (`model.update()`) |

**Rule of thumb**: Use GemPy for standard structural geology with faults and
unconformities. Use LoopStructural when fold geometry is the primary control
on model architecture.

## Step-by-Step Orchestration

### Stage 1: Spatial Data Preparation (gemgis)

```python
import gemgis as gg
import geopandas as gpd
import rasterio

# Load geological map (shapefile)
contacts = gpd.read_file('geological_contacts.shp')
orientations = gpd.read_file('orientations.shp')

# Extract surface points from GIS contacts with DEM
with rasterio.open('dem.tif') as dem:
    # All inputs must share the DEM's projected CRS and metre units.
    contacts = contacts.to_crs(dem.crs)
    orientations = orientations.to_crs(dem.crs)
    surface_points = gg.vector.extract_xyz(contacts, dem=dem)
    orientation_pts = gg.vector.extract_xyz(orientations, dem=dem)

# Define model extent from data bounds
extent = gg.utils.set_extent(
    gdf=surface_points,
    z_min=-500, z_max=1000
)
```

### Stage 2a: Implicit Modelling with GemPy

The following **synthetic inclined contact** is a runnable GemPy 2026.0.3
example without input files or a GPU. Coordinates are local projected metres;
Z is elevation, positive upward. Replace the arrays with Stage 1's validated
contact coordinates and formation names for a real model. Orientations require
pole-vector components `G_x/G_y/G_z`. Convert measured dip directions using the
documented coordinate convention and polarity before building that table.

```python
# example: gempy-model
import numpy as np
import gempy as gp
from gempy.core.data.options import InterpolationOptionsType

# Synthetic contact: z = -227.5 - 0.125 * (x - 1000).
extent = np.array([1000., 1200., 2000., 2120., -300., -180.])
resolution = np.array([8, 6, 5])  # Number of CELLS, not corner points.
surface_table = gp.data.SurfacePointsTable.from_arrays(
    x=np.array([1020., 1180., 1020.]),
    y=np.array([2020., 2020., 2100.]),
    z=np.array([-230., -250., -230.]),
    names='Sandstone_base',
)
pole = np.array([0.125, 0., 1.])
pole /= np.linalg.norm(pole)
orientation_table = gp.data.OrientationsTable.from_arrays(
    x=np.array([1060.]), y=np.array([2060.]), z=np.array([-235.]),
    G_x=pole[[0]], G_y=pole[[1]], G_z=pole[[2]],
    names=['Sandstone_base'], name_id_map=surface_table.name_id_map,
)
frame = gp.data.StructuralFrame.from_data_tables(surface_table, orientation_table)
geo_model = gp.create_geomodel(
    project_name='SyntheticInclinedContact',
    extent=extent, resolution=resolution, structural_frame=frame,
    intpolation_options_tye=InterpolationOptionsType.DENSE_GRID,
)
gp.map_stack_to_surfaces(geo_model, mapping_object={'Stratigraphy': ['Sandstone_base']})
geo_model.interpolation_options.evaluation_options.mesh_extraction = False
sol = gp.compute_model(
    geo_model,
    engine_config=gp.data.GemPyEngineConfig(backend=gp.data.AvailableBackends.numpy),
)
```

`structural_frame` supplies data at construction; `gp.set_interpolator` is not
part of this API. The spelling `intpolation_options_tye` is the library's current
keyword. For faulted input, map existing fault elements to their own groups with
`mapping_object`, then call `gp.set_is_fault` and inspect the fault relations
before computing. Do not invent fault surfaces without measurements.
Optional GemPy-specific section plots use `gempy_viewer.plot_2d`.

### Stage 2b: Implicit Modelling with LoopStructural (alternative)

This alternative requires its own prepared scalar-field and orientation
constraints; it does not produce GemPy's `sol`. Its regular-grid ordering and
stratigraphic column must be checked independently before exporting lithology.

```python
from LoopStructural import GeologicalModel
import pandas as pd

# Prepare input DataFrames
data = pd.DataFrame({
    'X': x_coords, 'Y': y_coords, 'Z': z_coords,
    'feature_name': formation_names,
    'val': stratigraphic_values,     # Scalar values for interface position
    'gx': gradient_x, 'gy': gradient_y, 'gz': gradient_z  # Orientation
})

# Build model
model = GeologicalModel(
    origin=[extent[0], extent[2], extent[4]],
    maximum=[extent[1], extent[3], extent[5]]
)
model.data = data

# Add features
model.create_and_add_foliation('Stratigraphy', interpolatortype='FDI')
model.create_and_add_fault('MainFault', displacement=100)

# Update and access
model.update()
lithology = model.evaluate_model(model.regular_grid())
```

### Stage 3: Export the GemPy Cell Model (pyvista)

Run this after Stage 2a. GemPy samples dense-grid **cell centres** with Z varying
fastest (NumPy C order). VTK cell arrays use X fastest (Fortran order). Preserve
both the axis ordering and physical extent when converting.

```python
# example: gempy-export
import numpy as np
import pyvista as pv

regular = geo_model.grid.regular_grid
shape = np.asarray(regular.resolution, dtype=int)
bounds = np.asarray(regular.extent, dtype=float)
lith_block = np.asarray(sol.raw_arrays.lith_block)
if lith_block.size != np.prod(shape):
    raise ValueError('Export requires a complete dense-grid lithology block')
spacing = (bounds[1::2] - bounds[::2]) / shape
grid = pv.ImageData(
    dimensions=tuple(shape + 1), spacing=tuple(spacing), origin=tuple(bounds[::2]),
)
grid.cell_data['lithology'] = lith_block.reshape(tuple(shape), order='C').ravel(order='F')
grid.save('geological_model.vti')
```

Lithology IDs are categorical: use discrete colours and slices or extracted
cells, rather than interpreting interpolated volume colours as rock mixtures.

```python
import pyvista as pv

plotter = pv.Plotter()
sliced = grid.slice(normal='y', origin=grid.center)
plotter.add_mesh(sliced, scalars='lithology', cmap='tab10', categories=True)
plotter.add_mesh(grid.outline(), color='black')
plotter.show_axes()
plotter.show()
```

## Common Pipelines

### Standard 3D Geological Model
```text
- [ ] Gather input data: geological map, DEM, borehole logs, structural measurements
- [ ] Load shapefiles and rasters with geopandas and rasterio
- [ ] Extract surface contact points with elevation using gemgis
- [ ] Extract orientation data (dip, azimuth) with gemgis
- [ ] Define model extent and resolution (cover data + buffer)
- [ ] Create GemPy GeoModel with extent and resolution
- [ ] Add surface points and orientations
- [ ] Define stratigraphic pile and structural relationships (ERODE, ONLAP)
- [ ] Add fault surfaces if present
- [ ] Configure interpolation options and compute model
- [ ] Validate with 2D cross-sections through known data points
- [ ] Visualize 3D result with pyvista
- [ ] Export to VTK or numpy for downstream use
```

### Borehole-Based Model
```text
- [ ] Load borehole data (collar, survey, lithology intervals)
- [ ] Convert lithology picks to surface contact points at formation boundaries
- [ ] Estimate orientations from multi-well dip calculation or assign regional dip
- [ ] Supply sufficient contact geometry and at least one orientation per structural group
- [ ] Validate: check model honours borehole intersections
- [ ] Iterate: add more data or adjust orientations to fix artifacts
```

### GIS-to-Model Pipeline
```text
- [ ] Load geological map polygons and structural measurements from shapefiles
- [ ] Reproject to common CRS with geopandas
- [ ] Extract formation boundary polylines from polygon contacts
- [ ] Sample points along polylines with gemgis
- [ ] Drape points onto DEM to get 3D coordinates
- [ ] Build GemPy model from extracted points and orientations
- [ ] Compare model surface traces with original geological map
```

## When to Use

Use the geological modelling workflow when:

- Building 3D geological models from surface mapping, boreholes, or GIS data
- Converting GIS spatial data into implicit geological surfaces
- Modelling faults, unconformities, or intrusions in 3D
- Creating subsurface models for downstream geophysical or engineering use

Use individual domain skills when:
- Only converting GIS data formats (use `gemgis` alone)
- Only building a model with data already prepared (use `gempy` alone)
- Only visualizing existing VTK meshes (use `pyvista` alone)

## Common Issues

| Issue | Solution |
|-------|----------|
| Model artifacts at edges | Extend model extent 10-20% beyond data coverage |
| Insufficient contact geometry | Obtain additional constraints; label geological assumptions explicitly |
| Fault offset direction wrong | Reverse pole_vector or swap footwall/hangingwall points |
| CRS mismatch between datasets | Reproject all data to common projected CRS with geopandas |
| LoopStructural fold not honoured | Add fold axis orientation and wavelength constraints |
| Resolution too coarse | Increase grid resolution but watch memory (50^3 = 125k cells) |

## API Sources and Verification

- [GemPy model construction](https://docs.gempy.org/_modules/gempy/API/initialization_API.html)
  and [structural data / groups](https://docs.gempy.org/tutorials/b_fundamentals/a01_basics.html).
- [PyVista cell-centred uniform grids](https://tutorial.pyvista.org/tutorial/02_mesh/solutions/c_create-uniform-grid.html).
- `tests/science/test_model_examples.py` executes the marked synthetic model and
  export blocks using the real libraries; it checks physical bounds, cell centres,
  categorical values, and a VTK save/read round trip. GIS files, fault networks,
  LoopStructural and interactive rendering are outside that test's scope.
