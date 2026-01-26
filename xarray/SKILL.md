---
name: xarray
description: N-dimensional labeled arrays for geoscience data. Read/write NetCDF, work with climate and oceanographic datasets, perform multi-dimensional analysis with labeled coordinates.
---

# xarray - Multi-Dimensional Geoscience Data

Help users work with NetCDF files and multi-dimensional labeled arrays for climate, ocean, atmosphere, and geoscience applications.

## Installation

```bash
pip install xarray netcdf4 h5netcdf
# For parallel computing
pip install dask[complete]
# For visualization
pip install matplotlib cartopy
```

## Core Concepts

### What xarray Does
- Read/write NetCDF, HDF5, GRIB, Zarr files
- Label-based indexing (time, lat, lon, depth)
- Automatic alignment and broadcasting
- GroupBy operations (daily/monthly means)
- Integration with Dask for large datasets

### Key Classes
| Class | Purpose |
|-------|---------|
| `DataArray` | Single variable with labeled dimensions |
| `Dataset` | Collection of aligned DataArrays |
| `Coordinates` | Dimension labels (time, lat, lon) |

### Dimension Convention (CF)
| Dimension | Typical Names |
|-----------|---------------|
| Time | `time`, `t` |
| Latitude | `lat`, `latitude`, `y` |
| Longitude | `lon`, `longitude`, `x` |
| Depth/Height | `depth`, `z`, `level`, `lev` |

## Common Workflows

### 1. Read NetCDF File
```python
import xarray as xr

# Open single file
ds = xr.open_dataset('climate_data.nc')

# View structure
print(ds)

# List variables
print(ds.data_vars)

# List coordinates
print(ds.coords)

# Access attributes
print(ds.attrs)

# Access single variable as DataArray
temp = ds['temperature']
print(temp.dims)    # ('time', 'lat', 'lon')
print(temp.shape)   # (365, 180, 360)
```

### 2. Write NetCDF File
```python
import xarray as xr
import numpy as np
import pandas as pd

# Create coordinates
times = pd.date_range('2020-01-01', periods=365, freq='D')
lats = np.linspace(-90, 90, 180)
lons = np.linspace(-180, 180, 360)

# Create data
temperature = np.random.randn(365, 180, 360) * 10 + 15

# Create DataArray
da = xr.DataArray(
    data=temperature,
    dims=['time', 'lat', 'lon'],
    coords={
        'time': times,
        'lat': lats,
        'lon': lons
    },
    attrs={
        'units': 'degC',
        'long_name': 'Surface Temperature',
        'standard_name': 'air_temperature'
    }
)

# Create Dataset
ds = xr.Dataset({
    'temperature': da,
    'precipitation': (['time', 'lat', 'lon'], np.random.rand(365, 180, 360) * 10)
})

# Add global attributes
ds.attrs['title'] = 'Climate Model Output'
ds.attrs['institution'] = 'My Institution'
ds.attrs['Conventions'] = 'CF-1.8'

# Save to NetCDF
ds.to_netcdf('output.nc')

# Save with compression
encoding = {
    'temperature': {'zlib': True, 'complevel': 5},
    'precipitation': {'zlib': True, 'complevel': 5}
}
ds.to_netcdf('output_compressed.nc', encoding=encoding)
```

### 3. Select Data by Labels
```python
import xarray as xr

ds = xr.open_dataset('climate_data.nc')

# Select by coordinate value
temp_jan = ds['temperature'].sel(time='2020-01-15')
temp_region = ds['temperature'].sel(lat=slice(-30, 30), lon=slice(-60, 60))

# Select nearest value
temp_point = ds['temperature'].sel(lat=35.5, lon=-120.3, method='nearest')

# Select by index
temp_first = ds['temperature'].isel(time=0)
temp_subset = ds['temperature'].isel(time=slice(0, 10))

# Select time range
temp_summer = ds['temperature'].sel(time=slice('2020-06-01', '2020-08-31'))
```

### 4. Compute Statistics
```python
import xarray as xr

ds = xr.open_dataset('climate_data.nc')
temp = ds['temperature']

# Mean over dimension
temp_mean_time = temp.mean(dim='time')           # Spatial map
temp_mean_space = temp.mean(dim=['lat', 'lon'])  # Time series

# Standard deviation
temp_std = temp.std(dim='time')

# Min/Max
temp_min = temp.min()
temp_max = temp.max()

# Percentiles
temp_p95 = temp.quantile(0.95, dim='time')

# Weighted mean (area-weighted)
weights = np.cos(np.deg2rad(ds.lat))
temp_weighted = temp.weighted(weights).mean(dim=['lat', 'lon'])
```

### 5. GroupBy Operations
```python
import xarray as xr

ds = xr.open_dataset('climate_data.nc')
temp = ds['temperature']

# Monthly mean
monthly_mean = temp.groupby('time.month').mean()

# Seasonal mean
seasonal_mean = temp.groupby('time.season').mean()

# Annual mean
annual_mean = temp.groupby('time.year').mean()

# Climatology (multi-year monthly mean)
climatology = temp.groupby('time.month').mean('time')

# Anomalies from climatology
anomalies = temp.groupby('time.month') - climatology

# Day of year
doy_mean = temp.groupby('time.dayofyear').mean()
```

### 6. Resample Time Series
```python
import xarray as xr

ds = xr.open_dataset('daily_data.nc')
temp = ds['temperature']

# Daily to monthly
monthly = temp.resample(time='1M').mean()

# Daily to annual
annual = temp.resample(time='1Y').mean()

# Downscale: monthly to daily (forward fill)
daily = monthly.resample(time='1D').ffill()

# Rolling mean (30-day window)
rolling_mean = temp.rolling(time=30, center=True).mean()
```

### 7. Interpolation
```python
import xarray as xr
import numpy as np

ds = xr.open_dataset('climate_data.nc')
temp = ds['temperature']

# Interpolate to new coordinates
new_lats = np.linspace(-90, 90, 360)
new_lons = np.linspace(-180, 180, 720)
temp_interp = temp.interp(lat=new_lats, lon=new_lons)

# Interpolate to specific point
temp_point = temp.interp(lat=35.5, lon=-120.3)

# Interpolate in time
new_times = pd.date_range('2020-01-01', '2020-12-31', freq='6H')
temp_hourly = temp.interp(time=new_times)
```

### 8. Merge and Combine Datasets
```python
import xarray as xr

# Open multiple files
ds1 = xr.open_dataset('data_2019.nc')
ds2 = xr.open_dataset('data_2020.nc')

# Concatenate along time
ds_combined = xr.concat([ds1, ds2], dim='time')

# Merge different variables
ds_temp = xr.open_dataset('temperature.nc')
ds_precip = xr.open_dataset('precipitation.nc')
ds_merged = xr.merge([ds_temp, ds_precip])

# Open multiple files at once (lazy loading)
ds = xr.open_mfdataset('data_*.nc', combine='by_coords')

# Or with specific pattern
ds = xr.open_mfdataset('data_????.nc', combine='nested', concat_dim='time')
```

### 9. Plotting
```python
import xarray as xr
import matplotlib.pyplot as plt

ds = xr.open_dataset('climate_data.nc')
temp = ds['temperature']

# Simple 2D plot
temp.isel(time=0).plot()
plt.title('Temperature Map')
plt.savefig('temp_map.png')

# Contour plot
temp.isel(time=0).plot.contourf(levels=20, cmap='RdBu_r')

# Time series
temp.sel(lat=0, lon=0, method='nearest').plot()
plt.title('Temperature at Equator')

# Faceted plots
temp.isel(time=slice(0, 12)).plot(col='time', col_wrap=4)

# With Cartopy projection
import cartopy.crs as ccrs

fig, ax = plt.subplots(subplot_kw={'projection': ccrs.Robinson()})
temp.isel(time=0).plot(
    ax=ax,
    transform=ccrs.PlateCarree(),
    cmap='RdBu_r'
)
ax.coastlines()
ax.gridlines()
plt.savefig('temp_map_projection.png', dpi=150)
```

### 10. Work with Large Datasets (Dask)
```python
import xarray as xr

# Open with chunking (lazy loading)
ds = xr.open_dataset('large_file.nc', chunks={'time': 100})

# Or specify chunks
ds = xr.open_mfdataset(
    'data_*.nc',
    chunks={'time': 'auto', 'lat': 100, 'lon': 100}
)

# Operations are lazy
temp_mean = ds['temperature'].mean(dim='time')

# Compute when needed
result = temp_mean.compute()

# Or save directly (computed in parallel)
temp_mean.to_netcdf('mean_temperature.nc')

# Monitor progress
from dask.diagnostics import ProgressBar
with ProgressBar():
    result = temp_mean.compute()
```

### 11. Apply Custom Functions
```python
import xarray as xr
import numpy as np

ds = xr.open_dataset('climate_data.nc')
temp = ds['temperature']

# Apply numpy function
temp_log = np.log(temp + 273.15)  # Log of absolute temperature

# Apply along dimension
def detrend(x):
    return x - x.mean()

temp_detrended = temp.groupby('time.year').map(detrend)

# Apply with xr.apply_ufunc
def custom_func(x, y):
    return x ** 2 + y

result = xr.apply_ufunc(
    custom_func,
    ds['temperature'],
    ds['precipitation'],
    dask='parallelized',
    output_dtypes=[float]
)
```

### 12. CF Conventions and Metadata
```python
import xarray as xr

ds = xr.open_dataset('climate_data.nc')

# Decode CF conventions (usually automatic)
ds = xr.open_dataset('climate_data.nc', decode_cf=True)

# Access units
print(ds['temperature'].attrs.get('units', 'unknown'))

# Add CF-compliant attributes
ds['temperature'].attrs = {
    'units': 'K',
    'long_name': 'Air Temperature',
    'standard_name': 'air_temperature',
    'cell_methods': 'time: mean',
    '_FillValue': -9999.0
}

# Set coordinate attributes
ds['lat'].attrs = {
    'units': 'degrees_north',
    'long_name': 'Latitude',
    'standard_name': 'latitude'
}

ds['lon'].attrs = {
    'units': 'degrees_east',
    'long_name': 'Longitude',
    'standard_name': 'longitude'
}
```

### 13. Extract Transects and Profiles
```python
import xarray as xr
import numpy as np

ds = xr.open_dataset('ocean_data.nc')

# Zonal mean (average over longitude)
zonal_mean = ds.mean(dim='lon')

# Meridional mean (average over latitude)
meridional_mean = ds.mean(dim='lat')

# Extract along a transect
lats_transect = np.linspace(20, 60, 100)
lons_transect = np.linspace(-80, -40, 100)
transect = ds.interp(lat=xr.DataArray(lats_transect, dims='distance'),
                      lon=xr.DataArray(lons_transect, dims='distance'))

# Vertical profile at a point
profile = ds.sel(lat=30, lon=-70, method='nearest')
```

### 14. Mask and Where
```python
import xarray as xr
import numpy as np

ds = xr.open_dataset('climate_data.nc')
temp = ds['temperature']

# Mask by condition
temp_warm = temp.where(temp > 20)

# Replace values
temp_clipped = temp.where(temp > 0, 0)  # Replace negative with 0

# Mask by another variable
land_mask = ds['land_fraction'] > 0.5
temp_land = temp.where(land_mask)

# Mask by coordinate
tropics = (ds.lat > -23.5) & (ds.lat < 23.5)
temp_tropics = temp.where(tropics, drop=True)
```

### 15. Calculate Gradients and Derivatives
```python
import xarray as xr
import numpy as np

ds = xr.open_dataset('climate_data.nc')
temp = ds['temperature']

# Gradient along dimension
dtemp_dlat = temp.differentiate('lat')
dtemp_dlon = temp.differentiate('lon')

# Convert to physical units (if coordinates in degrees)
R_earth = 6.371e6  # meters
dlat = np.deg2rad(1.0) * R_earth
dlon = np.deg2rad(1.0) * R_earth * np.cos(np.deg2rad(ds.lat))

dtemp_dy = dtemp_dlat / dlat
dtemp_dx = dtemp_dlon / dlon

# Magnitude of gradient
grad_magnitude = np.sqrt(dtemp_dx**2 + dtemp_dy**2)
```

### 16. Export to Other Formats
```python
import xarray as xr

ds = xr.open_dataset('climate_data.nc')

# To pandas DataFrame
df = ds.to_dataframe()

# To numpy array
arr = ds['temperature'].values

# To Zarr (cloud-optimized)
ds.to_zarr('output.zarr')

# To GeoTIFF (requires rioxarray)
import rioxarray
ds['temperature'].isel(time=0).rio.to_raster('output.tif')

# To CSV (single time slice)
ds.isel(time=0).to_dataframe().to_csv('output.csv')
```

## NetCDF4-Python (Low-Level)

For more control, use netCDF4 directly:

```python
from netCDF4 import Dataset
import numpy as np

# Create file
nc = Dataset('output.nc', 'w', format='NETCDF4')

# Create dimensions
nc.createDimension('time', None)  # Unlimited
nc.createDimension('lat', 180)
nc.createDimension('lon', 360)

# Create variables
times = nc.createVariable('time', 'f8', ('time',))
lats = nc.createVariable('lat', 'f4', ('lat',))
lons = nc.createVariable('lon', 'f4', ('lon',))
temp = nc.createVariable('temperature', 'f4', ('time', 'lat', 'lon'),
                          zlib=True, complevel=4)

# Add attributes
nc.title = 'My Dataset'
temp.units = 'K'
temp.long_name = 'Temperature'

# Write data
lats[:] = np.linspace(-90, 90, 180)
lons[:] = np.linspace(-180, 180, 360)
temp[0, :, :] = np.random.randn(180, 360) + 288

nc.close()
```

## Common NetCDF Sources

| Source | Description | URL |
|--------|-------------|-----|
| ERA5 | Reanalysis | Copernicus CDS |
| CMIP6 | Climate models | ESGF |
| NOAA | Ocean/atmosphere | NOAA NCEI |
| NASA | Earth observation | NASA Earthdata |

## File Format Comparison

| Format | Engine | Best For |
|--------|--------|----------|
| NetCDF4 | `netcdf4` | General use, compression |
| NetCDF3 | `scipy` | Legacy compatibility |
| HDF5 | `h5netcdf` | Large files, parallel I/O |
| Zarr | `zarr` | Cloud storage, parallel |
| GRIB | `cfgrib` | Weather model output |

## Tips

1. **Use chunking** for large files to enable lazy loading
2. **Apply CF conventions** for interoperability
3. **Compress with zlib** to reduce file size
4. **Use `open_mfdataset`** for multi-file datasets
5. **Add `_FillValue`** for missing data handling
6. **Use Dask** for datasets larger than memory

## Resources

- xarray docs: https://docs.xarray.dev/
- xarray GitHub: https://github.com/pydata/xarray
- netCDF4-python: https://unidata.github.io/netcdf4-python/
- CF Conventions: https://cfconventions.org/
- Pangeo: https://pangeo.io/ (big data geoscience)
