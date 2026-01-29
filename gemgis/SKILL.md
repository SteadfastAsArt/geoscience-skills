---
name: gemgis
description: |
  Spatial data processing for geological modelling with GemPy. Use when Claude
  needs to: (1) Prepare spatial data for GemPy models, (2) Extract interface
  points from geological maps, (3) Process orientations/dip measurements,
  (4) Sample DEMs along profiles or cross-sections, (5) Convert between GIS
  formats and GemPy inputs, (6) Clip/transform vector/raster data for modeling,
  (7) Create model extents from geospatial bounds.
---

# GemGIS - Geospatial Data for Geological Modelling

## Quick Reference

```python
import gemgis as gg
import geopandas as gpd

# Load vector data
gdf = gpd.read_file('geology.shp')

# Extract XYZ from geometry with elevation from DEM
interfaces = gg.vector.extract_xyz(gdf=gdf, dem='dem.tif')

# Define model extent
extent = [x_min, x_max, y_min, y_max]

# Clip to extent
gdf_clipped = gg.vector.clip_by_extent(gdf=gdf, extent=extent)
```

## Key Modules

| Module | Purpose |
|--------|---------|
| `gemgis.vector` | Vector data processing, XYZ extraction |
| `gemgis.raster` | Raster/DEM processing, sampling, interpolation |
| `gemgis.utils` | Utility functions, extent management |
| `gemgis.postprocessing` | Model postprocessing |

## Essential Operations

### Extract Interface Points
```python
contacts = gpd.read_file('contacts.shp')
interfaces = gg.vector.extract_xyz(gdf=contacts, dem='dem.tif')
interfaces['formation'] = contacts['formation']
# Returns DataFrame with X, Y, Z, formation columns
```

### Extract Orientations
```python
measurements = gpd.read_file('structural_measurements.shp')
orientations = gg.vector.extract_xyz(gdf=measurements, dem='dem.tif')
orientations['dip'] = measurements['dip']
orientations['azimuth'] = measurements['strike'] + 90  # strike to dip direction
orientations['formation'] = measurements['formation']
```

### Sample DEM Along Profile
```python
profile = gg.raster.sample_from_raster(
    raster='dem.tif',
    line=[(500000, 5600000), (510000, 5605000)],
    n_samples=100
)
# Returns dict with 'distance' and 'Z' arrays
```

### Define Model Extent
```python
# From coordinates
extent = gg.utils.set_extent(
    x_min=500000, x_max=510000,
    y_min=5600000, y_max=5610000
)

# From GeoDataFrame bounds
extent = gg.utils.set_extent_from_bounds(gdf)
```

### Clip Data to Extent
```python
from shapely.geometry import box
extent_poly = box(500000, 5600000, 510000, 5610000)
gdf_clipped = gdf.clip(extent_poly)

# Or using gemgis
gdf_clipped = gg.vector.clip_by_extent(
    gdf=gdf,
    extent=[500000, 510000, 5600000, 5610000]
)
```

### CRS Conversion
```python
# Always work in projected CRS (meters) for modeling
gdf_utm = gdf.to_crs('EPSG:32632')  # UTM zone 32N

# Or use GemGIS utility
gdf_utm = gg.vector.reproject(gdf, 'EPSG:32632')
```

## Supported Formats

| Format | Extension | Read | Write |
|--------|-----------|------|-------|
| Shapefile | .shp | Yes | Yes |
| GeoJSON | .geojson | Yes | Yes |
| GeoPackage | .gpkg | Yes | Yes |
| GeoTIFF | .tif | Yes | Yes |
| ASCII Grid | .asc | Yes | Yes |

## Common CRS

| EPSG | Description |
|------|-------------|
| 4326 | WGS84 (lat/lon) |
| 32632 | UTM Zone 32N |
| 32633 | UTM Zone 33N |

## Tips

1. **Always check CRS** - All data must be in the same coordinate system
2. **Use UTM for modelling** - Meters are easier than degrees
3. **Assign Z from DEM** - Ensures consistent elevations across datasets
4. **Validate geometry** - Fix invalid geometries before processing
5. **Buffer extent slightly** - Avoid edge effects in interpolation

## References

- **[Data Extraction Methods](references/data_extraction.md)** - Extract interfaces, orientations, and profiles
- **[Vector and Raster Operations](references/vector_raster.md)** - Detailed processing workflows

## Scripts

- **[scripts/prepare_gempy_data.py](scripts/prepare_gempy_data.py)** - Prepare spatial data for GemPy model input
