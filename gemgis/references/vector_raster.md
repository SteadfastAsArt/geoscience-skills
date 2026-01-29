# Vector and Raster Operations

## Table of Contents
- [Vector Operations](#vector-operations)
- [Raster Operations](#raster-operations)
- [Coordinate Transformations](#coordinate-transformations)
- [Data Export](#data-export)

## Vector Operations

### Loading Vector Data

```python
import geopandas as gpd

# Load from various formats
gdf = gpd.read_file('geology.shp')      # Shapefile
gdf = gpd.read_file('geology.geojson')  # GeoJSON
gdf = gpd.read_file('geology.gpkg')     # GeoPackage
gdf = gpd.read_file('data.gpkg', layer='geology')  # Specific layer

# Check basic info
print(f"CRS: {gdf.crs}")
print(f"Geometry types: {gdf.geom_type.unique()}")
print(f"Bounds: {gdf.total_bounds}")
print(f"Features: {len(gdf)}")
```

### Clipping to Extent

```python
import gemgis as gg
from shapely.geometry import box

# Define model extent
extent = [500000, 510000, 5600000, 5610000]  # [xmin, xmax, ymin, ymax]

# Method 1: Using shapely box
extent_poly = box(extent[0], extent[2], extent[1], extent[3])
gdf_clipped = gdf.clip(extent_poly)

# Method 2: Using GemGIS
gdf_clipped = gg.vector.clip_by_extent(gdf=gdf, extent=extent)

# Method 3: Using bounding box query
gdf_clipped = gdf.cx[extent[0]:extent[1], extent[2]:extent[3]]
```

### Geometry Validation and Repair

```python
# Check for invalid geometries
invalid = gdf[~gdf.is_valid]
print(f"Invalid geometries: {len(invalid)}")

# Fix invalid geometries
gdf['geometry'] = gdf['geometry'].buffer(0)

# Remove empty geometries
gdf = gdf[~gdf.is_empty]

# Remove null geometries
gdf = gdf.dropna(subset=['geometry'])
```

### Geometry Simplification

```python
# Simplify for faster processing (preserve topology)
gdf_simple = gdf.copy()
gdf_simple['geometry'] = gdf_simple['geometry'].simplify(
    tolerance=10,  # meters (in projected CRS)
    preserve_topology=True
)

# Check reduction
orig_points = sum(len(g.coords) if hasattr(g, 'coords') else 0
                  for g in gdf.geometry)
simp_points = sum(len(g.coords) if hasattr(g, 'coords') else 0
                  for g in gdf_simple.geometry)
print(f"Reduced from {orig_points} to {simp_points} vertices")
```

### Buffer Operations

```python
# Buffer features (useful for extending contacts)
buffered = gdf.copy()
buffered['geometry'] = gdf.buffer(100)  # 100m buffer

# Negative buffer (shrink polygons)
shrunk = gdf.copy()
shrunk['geometry'] = gdf.buffer(-50)  # 50m inward
shrunk = shrunk[~shrunk.is_empty]  # Remove collapsed features
```

### Spatial Joins

```python
# Add formation names to points based on polygon intersection
points = gpd.read_file('sample_points.shp')
polygons = gpd.read_file('geology_polygons.shp')

# Spatial join (points within polygons)
points_with_formation = gpd.sjoin(
    points,
    polygons[['geometry', 'formation']],
    how='left',
    predicate='within'
)
```

## Raster Operations

### Reading Raster Data

```python
import rasterio
import numpy as np

# Basic reading
with rasterio.open('dem.tif') as src:
    dem = src.read(1)           # First band as 2D array
    transform = src.transform   # Affine transform
    crs = src.crs               # Coordinate reference system
    nodata = src.nodata         # NoData value
    bounds = src.bounds         # Bounding box

# Handle NoData
dem = np.where(dem == nodata, np.nan, dem)
```

### Resampling Raster

```python
import gemgis as gg

# Reduce resolution (for faster processing)
dem_resampled = gg.raster.resize_by_factor(
    raster='dem.tif',
    factor=2  # Reduce resolution by half
)

# Using rasterio directly
from rasterio.enums import Resampling

with rasterio.open('dem.tif') as src:
    # Read at lower resolution
    dem_low = src.read(
        1,
        out_shape=(
            src.height // 2,
            src.width // 2
        ),
        resampling=Resampling.bilinear
    )
```

### Raster Clipping

```python
import rasterio
from rasterio.mask import mask
from shapely.geometry import box
import json

# Define extent polygon
extent_poly = box(500000, 5600000, 510000, 5610000)

# Clip raster to extent
with rasterio.open('dem.tif') as src:
    out_image, out_transform = mask(
        src,
        [extent_poly],
        crop=True
    )
    out_meta = src.meta.copy()

# Update metadata
out_meta.update({
    "height": out_image.shape[1],
    "width": out_image.shape[2],
    "transform": out_transform
})

# Save clipped raster
with rasterio.open('dem_clipped.tif', 'w', **out_meta) as dst:
    dst.write(out_image)
```

### Calculate Slope and Aspect

```python
import gemgis as gg
import numpy as np

# Using GemGIS
slope = gg.raster.calculate_slope(raster='dem.tif')
aspect = gg.raster.calculate_aspect(raster='dem.tif')

# Manual calculation with numpy
with rasterio.open('dem.tif') as src:
    dem = src.read(1).astype(float)
    cellsize = src.transform[0]

# Calculate gradients
dzdx = np.gradient(dem, cellsize, axis=1)
dzdy = np.gradient(dem, cellsize, axis=0)

# Slope in degrees
slope = np.degrees(np.arctan(np.sqrt(dzdx**2 + dzdy**2)))

# Aspect in degrees (0-360, clockwise from north)
aspect = np.degrees(np.arctan2(-dzdx, dzdy))
aspect = np.where(aspect < 0, aspect + 360, aspect)
```

### Interpolate to Grid

```python
import gemgis as gg
import geopandas as gpd

# Scattered points to regular grid
points = gpd.read_file('surface_points.shp')

grid = gg.raster.interpolate_raster(
    gdf=points,
    value_col='elevation',
    extent=[500000, 510000, 5600000, 5610000],
    resolution=100,  # Grid cell size in map units
    method='linear'  # 'linear', 'cubic', 'nearest'
)

# Save as raster
gg.raster.save_raster(
    array=grid,
    extent=[500000, 510000, 5600000, 5610000],
    crs='EPSG:32632',
    path='interpolated_surface.tif'
)
```

## Coordinate Transformations

### Reproject Vector Data

```python
import geopandas as gpd

# Check current CRS
print(f"Current CRS: {gdf.crs}")

# Transform to different CRS
gdf_utm = gdf.to_crs('EPSG:32632')    # UTM Zone 32N
gdf_wgs = gdf.to_crs('EPSG:4326')     # WGS84

# Using GemGIS
import gemgis as gg
gdf_utm = gg.vector.reproject(gdf, 'EPSG:32632')
```

### Common CRS for Geology

| EPSG | Name | Use Case |
|------|------|----------|
| 4326 | WGS84 | GPS data, web maps |
| 32632 | UTM 32N | Central Europe |
| 32633 | UTM 33N | Eastern Europe |
| 32610-32619 | UTM 10N-19N | Western USA |
| 32617-32619 | UTM 17N-19N | Eastern USA |
| 3857 | Web Mercator | Web mapping only |

### Reproject Raster Data

```python
import rasterio
from rasterio.warp import calculate_default_transform, reproject, Resampling

src_crs = 'EPSG:4326'
dst_crs = 'EPSG:32632'

with rasterio.open('dem_wgs84.tif') as src:
    transform, width, height = calculate_default_transform(
        src.crs, dst_crs, src.width, src.height, *src.bounds
    )

    kwargs = src.meta.copy()
    kwargs.update({
        'crs': dst_crs,
        'transform': transform,
        'width': width,
        'height': height
    })

    with rasterio.open('dem_utm.tif', 'w', **kwargs) as dst:
        for i in range(1, src.count + 1):
            reproject(
                source=rasterio.band(src, i),
                destination=rasterio.band(dst, i),
                src_transform=src.transform,
                src_crs=src.crs,
                dst_transform=transform,
                dst_crs=dst_crs,
                resampling=Resampling.bilinear
            )
```

## Data Export

### Export to GemPy-Ready CSV

```python
# Interface points
interfaces = gg.vector.extract_xyz(gdf=contacts, dem='dem.tif')
interfaces['formation'] = contacts['formation']
interfaces[['X', 'Y', 'Z', 'formation']].to_csv('interfaces.csv', index=False)

# Orientations
orientations = gg.vector.extract_xyz(gdf=measurements, dem='dem.tif')
orientations['dip'] = measurements['dip']
orientations['azimuth'] = measurements['azimuth']
orientations['polarity'] = 1
orientations['formation'] = measurements['formation']
orientations[['X', 'Y', 'Z', 'azimuth', 'dip', 'polarity', 'formation']].to_csv(
    'orientations.csv', index=False
)
```

### Export to Various Vector Formats

```python
# Shapefile (legacy, widely supported)
gdf.to_file('output.shp')

# GeoJSON (web-friendly, single file)
gdf.to_file('output.geojson', driver='GeoJSON')

# GeoPackage (modern, supports multiple layers)
gdf.to_file('output.gpkg', driver='GPKG', layer='geology')

# KML for Google Earth
gdf.to_crs('EPSG:4326').to_file('output.kml', driver='KML')
```

### Save Raster Data

```python
import rasterio
import numpy as np

# Define metadata
profile = {
    'driver': 'GTiff',
    'dtype': 'float32',
    'width': array.shape[1],
    'height': array.shape[0],
    'count': 1,
    'crs': 'EPSG:32632',
    'transform': rasterio.transform.from_bounds(
        xmin, ymin, xmax, ymax,
        array.shape[1], array.shape[0]
    ),
    'nodata': -9999
}

# Write raster
with rasterio.open('output.tif', 'w', **profile) as dst:
    dst.write(array.astype('float32'), 1)
```

## Best Practices

1. **Match CRS before operations** - Always ensure all data is in the same CRS
2. **Use projected CRS for modeling** - Geographic CRS (degrees) causes scale issues
3. **Handle NoData explicitly** - Replace NoData values with np.nan for calculations
4. **Validate after clipping** - Check that clipped data contains expected features
5. **Preserve metadata** - Keep CRS and transform when processing rasters
