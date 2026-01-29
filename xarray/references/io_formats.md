# I/O Formats Reference

## Table of Contents
- [NetCDF](#netcdf)
- [Zarr](#zarr)
- [Other Formats](#other-formats)
- [Compression](#compression)
- [Encoding Options](#encoding-options)

## NetCDF

### Read NetCDF
```python
import xarray as xr

# Single file
ds = xr.open_dataset('data.nc')

# With specific engine
ds = xr.open_dataset('data.nc', engine='netcdf4')   # Default
ds = xr.open_dataset('data.nc', engine='h5netcdf')  # Alternative HDF5 backend
ds = xr.open_dataset('data.nc', engine='scipy')     # NetCDF3 only

# Disable time decoding (for problematic time coordinates)
ds = xr.open_dataset('data.nc', decode_times=False)

# Multiple files
ds = xr.open_mfdataset('data_*.nc', combine='by_coords')
ds = xr.open_mfdataset('data_????.nc', combine='nested', concat_dim='time')
```

### Write NetCDF
```python
# Basic write
ds.to_netcdf('output.nc')

# With format specification
ds.to_netcdf('output.nc', format='NETCDF4')         # Default, HDF5-based
ds.to_netcdf('output.nc', format='NETCDF4_CLASSIC') # HDF5 with classic model
ds.to_netcdf('output.nc', format='NETCDF3_64BIT')   # Legacy compatibility

# With compression (per variable)
encoding = {
    'temperature': {'zlib': True, 'complevel': 5},
    'precipitation': {'zlib': True, 'complevel': 5}
}
ds.to_netcdf('output.nc', encoding=encoding)

# Unlimited dimension (for appending)
ds.to_netcdf('output.nc', unlimited_dims=['time'])
```

### netCDF4-Python (Low-Level)
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

## Zarr

Zarr is a cloud-optimized format for parallel I/O.

### Read Zarr
```python
# Local directory
ds = xr.open_zarr('data.zarr')

# Cloud storage (S3)
import s3fs
fs = s3fs.S3FileSystem(anon=True)
store = s3fs.S3Map(root='bucket/data.zarr', s3=fs)
ds = xr.open_zarr(store)

# Google Cloud Storage
import gcsfs
fs = gcsfs.GCSFileSystem(token='anon')
store = gcsfs.GCSMap(root='bucket/data.zarr', gcs=fs)
ds = xr.open_zarr(store)
```

### Write Zarr
```python
# Basic write
ds.to_zarr('output.zarr')

# Overwrite existing
ds.to_zarr('output.zarr', mode='w')

# Append to existing
ds.to_zarr('output.zarr', mode='a', append_dim='time')

# With specific chunks
ds = ds.chunk({'time': 100, 'lat': 50, 'lon': 50})
ds.to_zarr('output.zarr')

# With compression
from numcodecs import Blosc
compressor = Blosc(cname='zstd', clevel=3)
encoding = {var: {'compressor': compressor} for var in ds.data_vars}
ds.to_zarr('output.zarr', encoding=encoding)
```

## Other Formats

### GRIB (Weather Model Output)
```python
# Requires cfgrib: pip install cfgrib eccodes
ds = xr.open_dataset('forecast.grib', engine='cfgrib')

# With filter keys
ds = xr.open_dataset('forecast.grib', engine='cfgrib',
                     backend_kwargs={'filter_by_keys': {'typeOfLevel': 'surface'}})
```

### GeoTIFF (Raster Data)
```python
# Requires rioxarray: pip install rioxarray
import rioxarray

# Read
da = rioxarray.open_rasterio('image.tif')

# Write single timestep
ds['temperature'].isel(time=0).rio.to_raster('output.tif')
```

### CSV/Pandas
```python
# To DataFrame
df = ds.to_dataframe()
df.to_csv('output.csv')

# From DataFrame
df = pd.read_csv('data.csv', parse_dates=['time'])
ds = df.set_index(['time', 'lat', 'lon']).to_xarray()
```

## Compression

### Compression Algorithms

| Algorithm | Speed | Ratio | Use Case |
|-----------|-------|-------|----------|
| zlib | Medium | Good | General purpose |
| lzf | Fast | Lower | Quick I/O |
| zstd | Fast | Best | Modern systems |
| blosc | Fastest | Good | Zarr default |

### NetCDF Compression
```python
encoding = {
    'temperature': {
        'zlib': True,
        'complevel': 5,      # 1-9, higher = smaller/slower
        'shuffle': True,     # Improves compression
        'dtype': 'float32',  # Reduce precision if acceptable
    }
}
ds.to_netcdf('output.nc', encoding=encoding)
```

### Scale/Offset Encoding
```python
# Pack float data as integers
encoding = {
    'temperature': {
        'dtype': 'int16',
        'scale_factor': 0.01,
        'add_offset': 273.15,
        '_FillValue': -32768,
    }
}
ds.to_netcdf('output.nc', encoding=encoding)
```

## Encoding Options

### Common Encoding Parameters

| Parameter | Description |
|-----------|-------------|
| `dtype` | Data type (float32, int16, etc.) |
| `zlib` | Enable zlib compression |
| `complevel` | Compression level (1-9) |
| `shuffle` | Byte shuffle filter |
| `_FillValue` | Missing value indicator |
| `scale_factor` | Multiply to unpack |
| `add_offset` | Add to unpack |
| `chunksizes` | Chunk shape for NetCDF4 |

### Full Encoding Example
```python
encoding = {}
for var in ds.data_vars:
    encoding[var] = {
        'dtype': 'float32',
        'zlib': True,
        'complevel': 4,
        'shuffle': True,
        '_FillValue': -9999.0,
    }

# Add coordinate encoding
encoding['time'] = {'dtype': 'float64'}
encoding['lat'] = {'dtype': 'float32'}
encoding['lon'] = {'dtype': 'float32'}

ds.to_netcdf('output.nc', encoding=encoding)
```

## File Format Comparison

| Format | Engine | Best For |
|--------|--------|----------|
| NetCDF4 | `netcdf4` | General use, compression |
| NetCDF3 | `scipy` | Legacy compatibility |
| HDF5 | `h5netcdf` | Large files, parallel I/O |
| Zarr | `zarr` | Cloud storage, parallel |
| GRIB | `cfgrib` | Weather model output |

## Common NetCDF Data Sources

| Source | Description |
|--------|-------------|
| ERA5 | ECMWF reanalysis (Copernicus CDS) |
| CMIP6 | Climate models (ESGF) |
| NOAA | Ocean/atmosphere (NCEI) |
| NASA | Earth observation (Earthdata) |
