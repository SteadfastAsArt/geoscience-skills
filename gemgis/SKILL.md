---
name: gemgis
description: Spatial data processing for geological modelling. Prepare and transform geospatial data for use with GemPy and other geological modelling tools.
---

# GemGIS - Geospatial Data for Geological Modelling

Help users prepare spatial data for geological modelling with GemPy.

## Installation

```bash
pip install gemgis
```

## Core Concepts

### What GemGIS Does
- Extract geological data from maps
- Process DEMs and rasters
- Handle vector data (shapefiles, GeoJSON)
- Interface with GemPy
- Coordinate transformations
- Cross-section generation

### Key Modules
| Module | Purpose |
|--------|---------|
| `gemgis.vector` | Vector data processing |
| `gemgis.raster` | Raster/DEM processing |
| `gemgis.utils` | Utility functions |
| `gemgis.postprocessing` | Model postprocessing |

## Common Workflows

### 1. Load Vector Data
```python
import gemgis as gg
import geopandas as gpd

# Load shapefile
gdf = gpd.read_file('geology_map.shp')

# View data
print(gdf.columns)
print(gdf.head())

# Check geometry types
print(gdf.geom_type.unique())
```

### 2. Extract Interface Points from Lines
```python
import gemgis as gg
import geopandas as gpd

# Load geological contacts
contacts = gpd.read_file('contacts.shp')

# Extract vertices as interface points
interfaces = gg.vector.extract_xyz(
    gdf=contacts,
    dem='dem.tif'  # Assign Z from DEM
)

print(interfaces.head())
# Returns DataFrame with X, Y, Z, formation columns
```

### 3. Extract Orientation Data
```python
import gemgis as gg
import geopandas as gpd

# Load dip/strike measurements
measurements = gpd.read_file('structural_measurements.shp')

# Process orientations
orientations = gg.vector.extract_xyz(
    gdf=measurements,
    dem='dem.tif'
)

# Add dip/azimuth if not present
orientations['dip'] = measurements['dip']
orientations['azimuth'] = measurements['strike'] + 90  # Convert strike to dip direction

print(orientations.head())
```

### 4. Sample DEM Along Profile
```python
import gemgis as gg
import numpy as np

# Define profile line
start = (500000, 5600000)  # UTM coordinates
end = (510000, 5605000)

# Sample DEM along profile
profile = gg.raster.sample_from_raster(
    raster='dem.tif',
    line=[start, end],
    n_samples=100
)

import matplotlib.pyplot as plt
plt.plot(profile['distance'], profile['Z'])
plt.xlabel('Distance (m)')
plt.ylabel('Elevation (m)')
plt.title('Topographic Profile')
plt.show()
```

### 5. Create Model Extent
```python
import gemgis as gg

# Define model boundaries
extent = gg.utils.set_extent(
    x_min=500000,
    x_max=510000,
    y_min=5600000,
    y_max=5610000
)

# Or from GeoDataFrame bounds
gdf = gpd.read_file('geology.shp')
extent = gg.utils.set_extent_from_bounds(gdf)

print(extent)
# Returns [x_min, x_max, y_min, y_max]
```

### 6. Clip Data to Model Extent
```python
import gemgis as gg
import geopandas as gpd

# Load data
gdf = gpd.read_file('geology.shp')

# Define extent polygon
from shapely.geometry import box
extent_poly = box(500000, 5600000, 510000, 5610000)

# Clip
gdf_clipped = gdf.clip(extent_poly)

# Or use gemgis
gdf_clipped = gg.vector.clip_by_extent(
    gdf=gdf,
    extent=[500000, 510000, 5600000, 5610000]
)
```

### 7. Prepare Data for GemPy
```python
import gemgis as gg
import geopandas as gpd
import gempy as gp

# Load geological map data
contacts = gpd.read_file('contacts.shp')
measurements = gpd.read_file('orientations.shp')

# Extract interface points
interfaces = gg.vector.extract_xyz(
    gdf=contacts,
    dem='dem.tif'
)
interfaces['formation'] = contacts['formation']

# Extract orientations
orientations = gg.vector.extract_xyz(
    gdf=measurements,
    dem='dem.tif'
)
orientations['dip'] = measurements['dip']
orientations['azimuth'] = measurements['azimuth']
orientations['formation'] = measurements['formation']

# Create GemPy model
geo_model = gp.create_geomodel(
    project_name='Geological Model',
    extent=[500000, 510000, 5600000, 5610000, -2000, 1000],
    resolution=[50, 50, 50],
    structural_frame=gp.create_structural_frame(
        structural_groups=[...]
    )
)

# Add surface points
gp.add_surface_points(
    geo_model,
    x=interfaces['X'],
    y=interfaces['Y'],
    z=interfaces['Z'],
    surface=interfaces['formation']
)

# Add orientations
gp.add_orientations(
    geo_model,
    x=orientations['X'],
    y=orientations['Y'],
    z=orientations['Z'],
    surface=orientations['formation'],
    azimuth=orientations['azimuth'],
    dip=orientations['dip']
)
```

### 8. Process Raster Data
```python
import gemgis as gg
import rasterio

# Read DEM
with rasterio.open('dem.tif') as src:
    dem = src.read(1)
    transform = src.transform

# Resample to lower resolution
dem_resampled = gg.raster.resize_by_factor(
    raster='dem.tif',
    factor=2  # Reduce resolution by half
)

# Calculate slope and aspect
slope = gg.raster.calculate_slope(raster='dem.tif')
aspect = gg.raster.calculate_aspect(raster='dem.tif')
```

### 9. Create Cross-Section
```python
import gemgis as gg
import geopandas as gpd

# Load geological polygons
geology = gpd.read_file('geology_polygons.shp')

# Define section line
section_line = [(500000, 5600000), (510000, 5610000)]

# Create cross-section
section = gg.vector.create_section(
    gdf=geology,
    section_line=section_line,
    dem='dem.tif'
)

# Plot section
import matplotlib.pyplot as plt
section.plot(column='formation', legend=True)
plt.xlabel('Distance (m)')
plt.ylabel('Elevation (m)')
plt.show()
```

### 10. Interpolate Surface
```python
import gemgis as gg
import numpy as np

# Scattered elevation points
points = gpd.read_file('surface_points.shp')

# Interpolate to grid
grid = gg.raster.interpolate_raster(
    gdf=points,
    value_col='elevation',
    extent=[500000, 510000, 5600000, 5610000],
    resolution=100,  # meters
    method='linear'  # or 'cubic', 'nearest'
)

# Save as raster
gg.raster.save_raster(
    array=grid,
    extent=[500000, 510000, 5600000, 5610000],
    crs='EPSG:32632',
    path='interpolated_surface.tif'
)
```

### 11. Convert CRS
```python
import gemgis as gg
import geopandas as gpd

# Load data in WGS84
gdf = gpd.read_file('geology.shp')
print(f"Original CRS: {gdf.crs}")

# Convert to UTM
gdf_utm = gdf.to_crs('EPSG:32632')  # UTM zone 32N
print(f"New CRS: {gdf_utm.crs}")

# Or use GemGIS utility
gdf_utm = gg.vector.reproject(gdf, 'EPSG:32632')
```

### 12. Export for Visualization
```python
import gemgis as gg
import geopandas as gpd

# After processing
interfaces = gpd.read_file('processed_interfaces.shp')

# Export to different formats
interfaces.to_file('interfaces.geojson', driver='GeoJSON')
interfaces.to_file('interfaces.gpkg', driver='GPKG')

# Export to CSV for GemPy
df = interfaces[['X', 'Y', 'Z', 'formation']]
df.to_csv('interfaces.csv', index=False)
```

## Supported File Formats

| Format | Extension | Read | Write |
|--------|-----------|------|-------|
| Shapefile | .shp | ✓ | ✓ |
| GeoJSON | .geojson | ✓ | ✓ |
| GeoPackage | .gpkg | ✓ | ✓ |
| GeoTIFF | .tif | ✓ | ✓ |
| ASCII Grid | .asc | ✓ | ✓ |

## Coordinate Systems

| EPSG | Description |
|------|-------------|
| 4326 | WGS84 (lat/lon) |
| 32632 | UTM Zone 32N |
| 32633 | UTM Zone 33N |

## Tips

1. **Always check CRS** - Data must be in same coordinate system
2. **Use UTM for modelling** - Meters are easier than degrees
3. **Assign Z from DEM** - Ensures consistent elevations
4. **Validate geometry** - Fix invalid geometries before processing
5. **Buffer extent slightly** - Avoid edge effects

## Resources

- GitHub: https://github.com/cgre-aachen/gemgis
- Documentation: https://gemgis.readthedocs.io/
- GemPy: https://www.gempy.org/
- Tutorials: https://gemgis.readthedocs.io/en/latest/getting_started/tutorial/index.html
