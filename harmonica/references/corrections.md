# Gravity and Magnetic Corrections

## Table of Contents
- [Gravity Corrections](#gravity-corrections)
- [Gravity Anomalies](#gravity-anomalies)
- [Magnetic Corrections](#magnetic-corrections)
- [Reference Ellipsoids](#reference-ellipsoids)

## Gravity Corrections

### Free-Air Correction

Accounts for elevation difference between observation point and reference surface.

```python
import harmonica as hm

# Free-air correction (mGal)
# Approximation: 0.3086 mGal/m
free_air_correction = 0.3086 * height_m

# More accurate using normal gravity gradient
import boule as bl
ellipsoid = bl.WGS84
normal_gravity = ellipsoid.normal_gravity(latitude, height)
```

| Height (m) | Correction (mGal) |
|------------|-------------------|
| 100 | 30.86 |
| 500 | 154.3 |
| 1000 | 308.6 |

### Bouguer Correction

Removes effect of rock mass between observation point and reference surface.

```python
import harmonica as hm

# Simple Bouguer plate (infinite slab)
bouguer_correction = hm.bouguer_correction(
    height,          # meters
    density=2670     # kg/m3
)

# Formula: 2 * pi * G * density * height
# Approximately: 0.0419 * density * height (mGal)
```

| Density (kg/m3) | Factor (mGal/m) |
|-----------------|-----------------|
| 2000 | 0.0838 |
| 2500 | 0.1048 |
| 2670 | 0.1119 |
| 3000 | 0.1257 |

### Terrain Correction

Corrects for topographic variations around observation point.

```python
import harmonica as hm
import xarray as xr

# Load high-resolution DEM
topo = xr.open_dataarray('dem.nc')

# Create prism layer
layer = hm.prism_layer(
    (topo.easting.values, topo.northing.values),
    surface=topo.values,
    reference=0,
    properties={'density': 2670}
)

# Calculate terrain effect
terrain_effect = layer.gravity(
    (obs_easting, obs_northing, obs_height),
    field='g_z'
)

# Terrain correction is always positive (adds to anomaly)
terrain_correction = terrain_effect
```

### Latitude Correction

Accounts for variation in normal gravity with latitude.

```python
import boule as bl

ellipsoid = bl.WGS84

# Normal gravity at observation latitude and height
normal_gravity = ellipsoid.normal_gravity(latitude, height)

# Normal gravity at sea level
normal_gravity_sealevel = ellipsoid.normal_gravity(latitude, 0)
```

### Atmospheric Correction

Corrects for gravitational attraction of atmosphere above observation point.

```python
# Atmospheric correction (mGal)
# Approximately 0.87 mGal at sea level, decreases with height
atmo_correction = 0.87 * np.exp(-height / 8500)
```

## Gravity Anomalies

### Processing Sequence

```
Observed gravity
    |
    v
- Normal gravity (latitude + height) --> Free-air anomaly
    |
    v
- Bouguer correction --> Simple Bouguer anomaly
    |
    v
+ Terrain correction --> Complete Bouguer anomaly
    |
    v
- Regional field --> Residual anomaly
```

### Free-Air Anomaly

```python
import boule as bl

ellipsoid = bl.WGS84
normal_gravity = ellipsoid.normal_gravity(latitude, height)
free_air_anomaly = observed_gravity - normal_gravity
```

### Bouguer Anomaly

```python
import harmonica as hm

# Simple Bouguer anomaly
bouguer_corr = hm.bouguer_correction(height, density=2670)
simple_bouguer = free_air_anomaly - bouguer_corr

# Complete Bouguer anomaly (with terrain)
complete_bouguer = simple_bouguer + terrain_correction
```

### Isostatic Anomaly

```python
# Remove effect of crustal thickness variations
# Requires crustal model (e.g., Moho depth)
isostatic_anomaly = bouguer_anomaly - isostatic_correction
```

## Magnetic Corrections

### Diurnal Correction

Removes time-varying external field.

```python
import pandas as pd

# Load base station readings
base = pd.read_csv('base_station.csv', parse_dates=['time'])

# Interpolate to survey times
diurnal = np.interp(survey_times, base['time'], base['magnetic'])

# Apply correction
corrected = observed_magnetic - diurnal + base_mean
```

### IGRF Removal

Removes regional geomagnetic field.

```python
# Use pyIGRF or similar package
import pyigrf

# Get IGRF field at observation points
igrf_field = pyigrf.igrf_value(latitude, longitude, altitude_km, date)

# Magnetic anomaly
anomaly = total_field - igrf_field.total
```

### Reduction to Pole (RTP)

Transforms anomaly to vertical magnetization (as if at magnetic pole).

```python
# RTP is a frequency-domain operation
# Requires gridded data
# Use external packages like SimPEG or custom FFT implementation
```

## Reference Ellipsoids

### Common Ellipsoids

```python
import boule as bl

# WGS84 (most common)
wgs84 = bl.WGS84

# GRS80
grs80 = bl.GRS80

# Properties
print(f"Semi-major axis: {wgs84.semimajor_axis} m")
print(f"Flattening: {wgs84.flattening}")
print(f"GM: {wgs84.geocentric_grav_const} m3/s2")
```

| Ellipsoid | a (m) | 1/f |
|-----------|-------|-----|
| WGS84 | 6378137.0 | 298.257223563 |
| GRS80 | 6378137.0 | 298.257222101 |

### Normal Gravity

```python
import boule as bl

ellipsoid = bl.WGS84

# Normal gravity at latitude (sea level)
gamma_0 = ellipsoid.normal_gravity(latitude, 0)

# Normal gravity at height
gamma_h = ellipsoid.normal_gravity(latitude, height)

# Approximate formula (International Gravity Formula 1980)
# gamma = 978032.7 * (1 + 0.0053024*sin^2(lat) - 0.0000058*sin^2(2*lat)) mGal
```

## Typical Densities

| Rock Type | Density (kg/m3) |
|-----------|-----------------|
| Sediments (unconsolidated) | 1600-2000 |
| Sandstone | 2000-2500 |
| Limestone | 2400-2700 |
| Granite | 2500-2700 |
| Basalt | 2700-3100 |
| Peridotite | 3100-3400 |
| Upper crust (average) | 2670 |
| Lower crust | 2800-3000 |
| Upper mantle | 3300-3400 |
