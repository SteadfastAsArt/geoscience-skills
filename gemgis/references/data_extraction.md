# Data Extraction Methods

## Table of Contents
- [Extract XYZ from Geometry](#extract-xyz-from-geometry)
- [Interface Points from Contacts](#interface-points-from-contacts)
- [Orientation Data Processing](#orientation-data-processing)
- [Profile Sampling](#profile-sampling)
- [Cross-Section Generation](#cross-section-generation)

## Extract XYZ from Geometry

The core extraction function for getting 3D coordinates from vector data.

```python
import gemgis as gg
import geopandas as gpd

gdf = gpd.read_file('geology.shp')

# Basic extraction (Z from geometry if present)
xyz = gg.vector.extract_xyz(gdf=gdf)

# Extract with Z values from DEM
xyz = gg.vector.extract_xyz(gdf=gdf, dem='dem.tif')

# Result columns: X, Y, Z (plus any original attributes)
print(xyz.columns)
```

### Options for extract_xyz

| Parameter | Description |
|-----------|-------------|
| `gdf` | GeoDataFrame with point/line/polygon geometry |
| `dem` | Path to DEM raster for Z extraction |
| `reset_index` | Reset index of output DataFrame |

## Interface Points from Contacts

Extract surface contact points for GemPy from geological boundary lines.

```python
import gemgis as gg
import geopandas as gpd

# Load geological contact lines
contacts = gpd.read_file('geological_contacts.shp')

# Ensure CRS is projected (meters)
contacts = contacts.to_crs('EPSG:32632')

# Extract vertices with elevation from DEM
interfaces = gg.vector.extract_xyz(gdf=contacts, dem='dem.tif')

# Add formation information from original attributes
interfaces['formation'] = contacts.loc[interfaces.index, 'formation'].values

# Result: DataFrame ready for GemPy
print(interfaces.head())
#        X          Y        Z       formation
# 0  500123.4  5601234.5  450.2  Sandstone
# 1  500234.5  5601345.6  455.1  Sandstone
```

### Working with Different Geometry Types

```python
# For LineString geometries
# extract_xyz gets all vertices
line_gdf = gpd.read_file('fault_traces.shp')
fault_points = gg.vector.extract_xyz(gdf=line_gdf, dem='dem.tif')

# For Polygon geometries
# extract_xyz gets boundary vertices
poly_gdf = gpd.read_file('geology_polygons.shp')
boundary_points = gg.vector.extract_xyz(gdf=poly_gdf, dem='dem.tif')

# For Point geometries
# Direct extraction
point_gdf = gpd.read_file('sample_points.shp')
sample_xyz = gg.vector.extract_xyz(gdf=point_gdf, dem='dem.tif')
```

## Orientation Data Processing

Process structural measurements (dip/strike) for GemPy orientations.

```python
import gemgis as gg
import geopandas as gpd

# Load structural measurement points
measurements = gpd.read_file('structural_data.shp')

# Extract XYZ coordinates
orientations = gg.vector.extract_xyz(gdf=measurements, dem='dem.tif')

# Add orientation attributes
orientations['dip'] = measurements['dip']
orientations['polarity'] = 1  # Normal polarity

# Convert strike to azimuth (dip direction)
# Azimuth = Strike + 90 (right-hand rule)
orientations['azimuth'] = measurements['strike'] + 90
orientations.loc[orientations['azimuth'] >= 360, 'azimuth'] -= 360

# Add formation for GemPy
orientations['formation'] = measurements['formation']

# Validate orientations
assert (orientations['dip'] >= 0).all() and (orientations['dip'] <= 90).all()
assert (orientations['azimuth'] >= 0).all() and (orientations['azimuth'] < 360).all()
```

### Orientation Conventions

| Field | Range | Description |
|-------|-------|-------------|
| dip | 0-90 | Inclination from horizontal (degrees) |
| azimuth | 0-360 | Dip direction (degrees from north) |
| strike | 0-360 | Strike direction (azimuth - 90) |
| polarity | 1/-1 | Normal/overturned |

### Converting Between Strike and Azimuth

```python
# Strike to Azimuth (right-hand rule)
azimuth = (strike + 90) % 360

# Azimuth to Strike
strike = (azimuth - 90) % 360
```

## Profile Sampling

Sample elevation or attribute values along a profile line.

```python
import gemgis as gg
import matplotlib.pyplot as plt

# Define profile endpoints (in map coordinates)
start = (500000, 5600000)
end = (510000, 5605000)

# Sample DEM along profile
profile = gg.raster.sample_from_raster(
    raster='dem.tif',
    line=[start, end],
    n_samples=100
)

# Plot topographic profile
plt.figure(figsize=(12, 4))
plt.plot(profile['distance'], profile['Z'])
plt.xlabel('Distance (m)')
plt.ylabel('Elevation (m)')
plt.title('Topographic Profile A-A\'')
plt.grid(True)
plt.show()
```

### Profile with Multiple Rasters

```python
import numpy as np

# Sample multiple surfaces
dem_profile = gg.raster.sample_from_raster(
    raster='dem.tif',
    line=[start, end],
    n_samples=100
)

basement_profile = gg.raster.sample_from_raster(
    raster='basement_surface.tif',
    line=[start, end],
    n_samples=100
)

# Plot both
plt.fill_between(dem_profile['distance'],
                 basement_profile['Z'],
                 dem_profile['Z'],
                 alpha=0.5, label='Sediment Cover')
plt.plot(dem_profile['distance'], dem_profile['Z'], 'k-', label='Surface')
plt.plot(basement_profile['distance'], basement_profile['Z'], 'b-', label='Basement')
plt.legend()
```

## Cross-Section Generation

Create geological cross-sections from map data.

```python
import gemgis as gg
import geopandas as gpd
import matplotlib.pyplot as plt

# Load geological polygons
geology = gpd.read_file('geology_polygons.shp')

# Define section line
section_line = [(500000, 5600000), (510000, 5610000)]

# Create section (intersects geology with vertical plane)
section = gg.vector.create_section(
    gdf=geology,
    section_line=section_line,
    dem='dem.tif'
)

# Plot cross-section
fig, ax = plt.subplots(figsize=(14, 6))
section.plot(ax=ax, column='formation', legend=True, cmap='Set3')
ax.set_xlabel('Distance along section (m)')
ax.set_ylabel('Elevation (m)')
ax.set_title('Geological Cross-Section A-A\'')
plt.show()
```

### Manual Cross-Section Construction

```python
from shapely.geometry import LineString
import numpy as np

# Create section line geometry
section_line = LineString([(500000, 5600000), (510000, 5610000)])

# Sample topography along section
profile = gg.raster.sample_from_raster(
    raster='dem.tif',
    line=list(section_line.coords),
    n_samples=200
)

# Intersect geological contacts with section line
contacts = gpd.read_file('contacts.shp')
intersections = contacts.intersection(section_line)

# Convert intersection points to section coordinates
for idx, geom in intersections.items():
    if not geom.is_empty:
        # Calculate distance along section
        dist = section_line.project(geom)
        # Sample elevation at this point
        z = gg.raster.sample_from_raster(
            raster='dem.tif',
            line=[list(geom.coords)[0]],
            n_samples=1
        )['Z'][0]
        print(f"Contact at distance {dist:.1f}m, elevation {z:.1f}m")
```

## Best Practices

1. **Always check CRS before extraction** - Mismatched CRS causes incorrect coordinates
2. **Use projected CRS for distance calculations** - Geographic CRS (degrees) gives wrong distances
3. **Validate DEM coverage** - Ensure DEM covers all extraction points
4. **Handle NoData values** - Check for -9999 or NaN in extracted Z values
5. **Preserve attribute linkage** - Keep track of original feature IDs when extracting
