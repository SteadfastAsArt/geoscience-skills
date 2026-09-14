---
name: gemgis
description: |
  Spatial data processing for geological modelling with GemPy. Use when the agent
  needs to: (1) Prepare spatial data for GemPy models, (2) Extract interface
  points from geological maps, (3) Process orientations/dip measurements,
  (4) Sample DEMs along profiles or cross-sections, (5) Convert between GIS
  formats and GemPy inputs, (6) Clip/transform vector/raster data for modeling,
  (7) Create model extents from geospatial bounds.
license: MIT
metadata:
  version: "1.0.2"
  author: Geoscience Skills
  tags: '["GIS", "Geospatial", "Data Preparation", "DEM", "Geological Modelling"]'
  dependencies: '["gemgis>=1.1.9", "geopandas", "rasterio"]'
  complements: '["gempy", "loopstructural", "pyvista"]'
  workflow_role: processing
  skill_type: domain
---

# GIS contacts and DEM elevations

Use GemGIS to extract geological observations from spatial data. Establish the
horizontal CRS, vertical units/datum, geometry type and missing-data policy
before sampling. Model coordinates must share a projected metre CRS; converting
horizontal coordinates does not transform elevations or their datum.

## Extract contact vertices

The following function accepts a single-band DEM already in a metre projected
CRS, with elevations in metres. `dem` is an open Rasterio dataset, not a path.
GemGIS repeats attributes when a line becomes multiple points: do not overwrite
those attributes using the original feature index.

```python
import gemgis as gg
from rasterio.transform import rowcol
import numpy as np
from pyproj import CRS

def contacts_at_dem(contacts, dem):
    crs = CRS.from_user_input(dem.crs)
    if (contacts.crs is None or not crs.is_projected or dem.count != 1
            or any(not np.isclose(a.unit_conversion_factor, 1.) for a in crs.axis_info[:2])):
        raise ValueError('Require a known vector CRS and a single-band metric DEM')
    if contacts.empty or not contacts.is_valid.all() or contacts.geometry.has_z.any():
        raise ValueError('Require valid nonempty 2D contact geometry')
    if 'formation' not in contacts or contacts['formation'].isna().any():
        raise ValueError('Formation labels are required')
    points = gg.vector.extract_xy(contacts.to_crs(dem.crs))
    xy = points[['X', 'Y']].to_numpy()
    rows, cols = np.asarray(rowcol(dem.transform, xy[:, 0], xy[:, 1]))
    if np.any((rows < 0) | (rows >= dem.height) | (cols < 0) | (cols >= dem.width)):
        raise ValueError('Vertices outside DEM')
    samples = np.ma.vstack(list(dem.sample(xy, indexes=1, masked=True)))[:, 0]
    if np.ma.getmaskarray(samples).any() or not np.isfinite(samples.data).all():
        raise ValueError('Missing DEM elevations')
    return gg.vector.extract_xyz(gdf=points, dem=dem)[['X', 'Y', 'Z', 'formation']]
```

Open with `with rasterio.open(dem_path) as dem:` and call this function while the
dataset is open. Pixel sampling uses the containing cell; it is not bilinear
interpolation. Do not fill NoData or outside-extent samples with zero.

## Orientations and helper

Dip is in degrees, 0–90. Output azimuth is dip direction clockwise from DEM grid north, wrapped
to [0, 360). Convert strike with `(strike + 90) % 360` only when the source
explicitly follows the right-hand rule. Preserve supplied polarity (+1/−1);
the helper uses +1 only when the column is absent. Never clamp invalid dip.
Declare `--azimuth-reference dem-grid` for bearings already relative to the DEM
grid, or `true-north` for geographic bearings. The latter applies local
meridian convergence only on locally conformal projections; other projections
are rejected. Magnetic bearings need a documented declination correction first.

The [preparation helper](scripts/prepare_gempy_data.py) validates these rules,
reprojects vectors to the DEM CRS, converts declared ft elevations to metres,
and writes CSVs plus `spatial_metadata.json` into a fresh output directory. Its `--target-crs` is an assertion
that must match the DEM; resample/reproject a raster separately when needed.

```bash
python scripts/prepare_gempy_data.py --contacts contacts.gpkg \
  --orientations orientations.gpkg --azimuth-reference true-north --dem dem.tif --dem-z-unit m \
  --vertical-datum "documented source datum" --output-dir prepared
```

Resolve this command relative to the installed skill directory. The output
schema uses X/Y/Z and formation, plus dip/azimuth/polarity for orientations;
pass these to the current modelling library's input API rather than assuming
all GemPy versions accept identical keyword arguments.

## Conditional operations

Read [profiles and extraction](references/data_extraction.md) for sampled
profiles and orientation conventions. Read [CRS, clipping and raster handling](references/vector_raster.md)
for bounds order, masks, reprojection and provenance. Existing 3D geometry
needs an explicit choice between measured Z and DEM Z before using this helper.

## Verification scope

GemGIS 1.1.9, GeoPandas 1.1.4 and Rasterio 1.4.4 were checked with a real
GeoTIFF/GeoPackage fixture: unequal vertex counts and nonconsecutive indices,
CRS conversion, feet elevations, NoData, outside points, orientations and CLI
CSV readback. Synthetic elevations test data handling, not field DEM accuracy
or vertical-datum transformation.

[Official GemGIS source](https://github.com/cgre-aachen/gemgis),
[Rasterio sampling API](https://rasterio.readthedocs.io/en/stable/api/rasterio.sample.html),
checked 2026-09-14.
