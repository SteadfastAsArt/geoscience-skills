# Computation and Aggregation Methods

## Table of Contents
- [Basic Statistics](#basic-statistics)
- [Temporal Aggregations](#temporal-aggregations)
- [Spatial Operations](#spatial-operations)
- [Weighted Operations](#weighted-operations)
- [Interpolation](#interpolation)
- [Gradients and Derivatives](#gradients-and-derivatives)
- [Custom Functions](#custom-functions)
- [Parallel Computing with Dask](#parallel-computing-with-dask)

## Basic Statistics

### Reduction Operations
```python
temp = ds['temperature']

# Over single dimension
temp_mean = temp.mean(dim='time')
temp_std = temp.std(dim='time')
temp_var = temp.var(dim='time')
temp_min = temp.min(dim='time')
temp_max = temp.max(dim='time')
temp_sum = temp.sum(dim='time')

# Over multiple dimensions
spatial_mean = temp.mean(dim=['lat', 'lon'])

# All dimensions (scalar result)
global_mean = temp.mean()

# Preserve NaN (default skipna=True)
temp_mean = temp.mean(dim='time', skipna=False)
```

### Percentiles and Quantiles
```python
# Single quantile
temp_p95 = temp.quantile(0.95, dim='time')
temp_median = temp.quantile(0.5, dim='time')

# Multiple quantiles
quantiles = temp.quantile([0.1, 0.5, 0.9], dim='time')
```

### Count and Boolean Operations
```python
# Count non-NaN values
count = temp.count(dim='time')

# Boolean reductions
any_hot = (temp > 30).any(dim='time')
all_positive = (temp > 0).all(dim='time')
```

## Temporal Aggregations

### GroupBy Time Components
```python
temp = ds['temperature']

# Available time components
monthly = temp.groupby('time.month').mean()      # 12 months
seasonal = temp.groupby('time.season').mean()    # DJF, MAM, JJA, SON
annual = temp.groupby('time.year').mean()        # Per year
daily = temp.groupby('time.dayofyear').mean()    # 365/366 days
hourly = temp.groupby('time.hour').mean()        # 24 hours
weekly = temp.groupby('time.week').mean()        # 52 weeks
```

### Climatology and Anomalies
```python
# Multi-year monthly mean (climatology)
climatology = temp.groupby('time.month').mean('time')

# Anomalies from climatology
anomalies = temp.groupby('time.month') - climatology

# Standardized anomalies
monthly_std = temp.groupby('time.month').std('time')
standardized = (temp.groupby('time.month') - climatology) / monthly_std
```

### Resample Time Series
```python
# Downsample (aggregate)
monthly = temp.resample(time='1M').mean()        # Daily to monthly
annual = temp.resample(time='1Y').mean()         # Daily to annual
weekly = temp.resample(time='1W').mean()         # Daily to weekly
quarterly = temp.resample(time='1Q').mean()      # Monthly to quarterly

# Other aggregations
monthly_max = temp.resample(time='1M').max()
monthly_sum = temp.resample(time='1M').sum()

# Upsample (interpolate)
hourly = temp.resample(time='1H').interpolate('linear')
daily_ffill = monthly.resample(time='1D').ffill()
```

### Rolling Windows
```python
# Rolling mean
rolling_30d = temp.rolling(time=30, center=True).mean()
rolling_7d = temp.rolling(time=7).sum()

# Min periods (handle edges)
rolling = temp.rolling(time=30, min_periods=15).mean()

# Multi-dimensional rolling
spatial_smooth = temp.rolling(lat=5, lon=5, center=True).mean()
```

## Spatial Operations

### Zonal/Meridional Means
```python
# Zonal mean (average over longitude)
zonal_mean = ds.mean(dim='lon')

# Meridional mean (average over latitude)
meridional_mean = ds.mean(dim='lat')
```

### Extract Regions
```python
# Box selection
region = ds.sel(lat=slice(-30, 30), lon=slice(-60, 60))

# Point selection
point = ds.sel(lat=35.5, lon=-120.3, method='nearest')

# Mask selection
tropics = (ds.lat > -23.5) & (ds.lat < 23.5)
tropical_data = ds.where(tropics, drop=True)
```

### Transects
```python
import numpy as np

# Diagonal transect
lats_transect = np.linspace(20, 60, 100)
lons_transect = np.linspace(-80, -40, 100)
transect = ds.interp(
    lat=xr.DataArray(lats_transect, dims='distance'),
    lon=xr.DataArray(lons_transect, dims='distance')
)
```

## Weighted Operations

### Area-Weighted Mean
```python
import numpy as np

# Latitude weights (cosine of latitude)
weights = np.cos(np.deg2rad(ds.lat))
temp_weighted = ds['temperature'].weighted(weights).mean(dim=['lat', 'lon'])

# Full area weights
lat_weights = np.cos(np.deg2rad(ds.lat))
area_weights = xr.ones_like(ds['temperature']) * lat_weights
global_mean = ds['temperature'].weighted(area_weights).mean(dim=['lat', 'lon'])
```

### Custom Weights
```python
# Population-weighted temperature
population = xr.open_dataset('population.nc')['population']
temp_pop_weighted = ds['temperature'].weighted(population).mean(dim=['lat', 'lon'])

# Time-weighted (for irregular time series)
dt = ds.time.diff('time').astype('timedelta64[D]').astype(float)
temp_time_weighted = (ds['temperature'] * dt).sum(dim='time') / dt.sum()
```

## Interpolation

### Grid Interpolation
```python
# Interpolate to new grid
new_lats = np.linspace(-90, 90, 360)
new_lons = np.linspace(-180, 180, 720)
ds_interp = ds.interp(lat=new_lats, lon=new_lons)

# Methods: linear (default), nearest, cubic, quadratic
ds_interp = ds.interp(lat=new_lats, lon=new_lons, method='cubic')
```

### Point Interpolation
```python
# Single point
temp_point = ds['temperature'].interp(lat=35.5, lon=-120.3)

# Multiple points
lats = xr.DataArray([35.5, 40.0, 45.2], dims='station')
lons = xr.DataArray([-120.3, -105.0, -90.5], dims='station')
temp_stations = ds['temperature'].interp(lat=lats, lon=lons)
```

### Time Interpolation
```python
import pandas as pd

# Interpolate to specific times
new_times = pd.date_range('2020-01-01', '2020-12-31', freq='6H')
ds_hourly = ds.interp(time=new_times)

# Fill gaps
ds_filled = ds.interpolate_na(dim='time', method='linear')
```

## Gradients and Derivatives

### Differentiation
```python
temp = ds['temperature']

# Gradient along dimension
dtemp_dlat = temp.differentiate('lat')
dtemp_dlon = temp.differentiate('lon')
dtemp_dt = temp.differentiate('time')
```

### Physical Gradients
```python
import numpy as np

# Convert to physical units (degrees to meters)
R_earth = 6.371e6  # meters
dlat = np.deg2rad(1.0) * R_earth
dlon = np.deg2rad(1.0) * R_earth * np.cos(np.deg2rad(ds.lat))

dtemp_dy = temp.differentiate('lat') / dlat
dtemp_dx = temp.differentiate('lon') / dlon

# Gradient magnitude
grad_magnitude = np.sqrt(dtemp_dx**2 + dtemp_dy**2)
```

### Cumulative Operations
```python
# Cumulative sum
temp_cumsum = temp.cumsum(dim='time')

# Running total
precip_total = ds['precipitation'].cumsum(dim='time')
```

## Custom Functions

### Apply NumPy Functions
```python
import numpy as np

# Direct application
temp_log = np.log(temp + 273.15)
temp_abs = np.abs(temp)
temp_sqrt = np.sqrt(temp.where(temp > 0))
```

### GroupBy with Custom Functions
```python
def detrend(x):
    return x - x.mean()

temp_detrended = temp.groupby('time.year').map(detrend)

def normalize(x):
    return (x - x.min()) / (x.max() - x.min())

temp_normalized = temp.groupby('time.month').map(normalize)
```

### apply_ufunc for Complex Operations
```python
def custom_func(x, y):
    return x ** 2 + y

result = xr.apply_ufunc(
    custom_func,
    ds['temperature'],
    ds['precipitation'],
    dask='parallelized',
    output_dtypes=[float]
)

# With dimension reduction
def weighted_mean(data, weights):
    return np.average(data, weights=weights)

result = xr.apply_ufunc(
    weighted_mean,
    ds['temperature'],
    weights,
    input_core_dims=[['lat', 'lon'], ['lat']],
    vectorize=True
)
```

## Parallel Computing with Dask

### Chunked Operations
```python
# Open with chunks
ds = xr.open_dataset('large_file.nc', chunks={'time': 100, 'lat': 50, 'lon': 50})

# All operations are lazy
temp_mean = ds['temperature'].mean(dim='time')
temp_anom = ds['temperature'] - ds['temperature'].mean(dim='time')

# Compute when ready
result = temp_mean.compute()

# Or save directly (parallel write)
temp_mean.to_netcdf('output.nc')
```

### Monitor Progress
```python
from dask.diagnostics import ProgressBar

with ProgressBar():
    result = ds['temperature'].mean(dim='time').compute()
```

### Dask Cluster
```python
from dask.distributed import Client

# Local cluster
client = Client(n_workers=4)

# Operations automatically distributed
result = ds['temperature'].mean(dim='time').compute()

client.close()
```

### Rechunk Data
```python
# Change chunk structure
ds_rechunked = ds.chunk({'time': -1, 'lat': 50, 'lon': 50})

# Optimal for time-based operations
ds_time = ds.chunk({'time': 'auto', 'lat': -1, 'lon': -1})
```
