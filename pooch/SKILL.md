---
name: pooch
description: Data file fetching and caching for geoscience applications. Download sample datasets with automatic caching, checksum verification, and multiple download sources.
---

# Pooch - Data File Fetching

Help users download and cache data files for geoscience applications.

## Installation

```bash
pip install pooch
```

## Core Concepts

### What Pooch Does
- Downloads files from URLs with automatic caching
- Verifies file integrity with checksums (SHA256, MD5)
- Supports multiple download sources (URLs, DOIs, Zenodo)
- Decompresses archives automatically
- Provides sample datasets for testing

### Key Functions
| Function | Purpose |
|----------|---------|
| `pooch.retrieve()` | Download single file |
| `pooch.create()` | Create custom data registry |
| `pooch.Pooch` | Manager for multiple files |
| `pooch.os_cache()` | Get OS-specific cache directory |

## Common Workflows

### 1. Download a Single File
```python
import pooch

# Download file with checksum verification
file_path = pooch.retrieve(
    url="https://example.com/data.csv",
    known_hash="sha256:abc123...",  # Optional but recommended
    fname="data.csv",  # Local filename
    path=pooch.os_cache("myproject")  # Cache location
)

# Use the downloaded file
import pandas as pd
df = pd.read_csv(file_path)
```

### 2. Download Without Hash (Development)
```python
import pooch

# Skip hash checking (for development only)
file_path = pooch.retrieve(
    url="https://example.com/data.nc",
    known_hash=None  # Skips verification
)
```

### 3. Create a Data Registry
```python
import pooch

# Define registry of files
REGISTRY = pooch.create(
    path=pooch.os_cache("myproject"),
    base_url="https://example.com/data/",
    version="1.0.0",
    registry={
        "earthquakes.csv": "sha256:abc123...",
        "stations.json": "sha256:def456...",
        "model.nc": "sha256:ghi789...",
    }
)

# Fetch individual files
eq_file = REGISTRY.fetch("earthquakes.csv")
```

### 4. Fetch from Zenodo
```python
import pooch

# Zenodo DOI-based download
file_path = pooch.retrieve(
    url="doi:10.5281/zenodo.1234567/data.zip",
    known_hash="sha256:abc123..."
)
```

### 5. Handle Compressed Archives
```python
import pooch

# Download and extract ZIP
files = pooch.retrieve(
    url="https://example.com/data.zip",
    known_hash="sha256:abc123...",
    processor=pooch.Unzip()  # Extracts contents
)
# Returns list of extracted file paths

# Extract specific files
files = pooch.retrieve(
    url="https://example.com/data.tar.gz",
    known_hash="sha256:abc123...",
    processor=pooch.Untar(members=["data/file1.csv", "data/file2.csv"])
)
```

### 6. Decompress Single Files
```python
import pooch

# Decompress gzip file
file_path = pooch.retrieve(
    url="https://example.com/data.csv.gz",
    known_hash="sha256:abc123...",
    processor=pooch.Decompress(name="data.csv")
)
```

### 7. Custom Cache Location
```python
import pooch
import os

# Use environment variable
cache = os.environ.get("MY_DATA_DIR", pooch.os_cache("myproject"))

file_path = pooch.retrieve(
    url="https://example.com/data.csv",
    known_hash=None,
    path=cache
)
```

### 8. Multiple Download Sources (Mirrors)
```python
import pooch

REGISTRY = pooch.create(
    path=pooch.os_cache("myproject"),
    base_url="https://primary.com/data/",
    urls={
        "large_file.nc": [
            "https://primary.com/data/large_file.nc",
            "https://mirror1.com/data/large_file.nc",
            "https://mirror2.com/data/large_file.nc",
        ]
    },
    registry={
        "large_file.nc": "sha256:abc123...",
    }
)

# Automatically tries mirrors if primary fails
file_path = REGISTRY.fetch("large_file.nc")
```

### 9. Progress Bar for Large Downloads
```python
import pooch

file_path = pooch.retrieve(
    url="https://example.com/large_file.nc",
    known_hash="sha256:abc123...",
    progressbar=True  # Shows download progress
)
```

### 10. Use with Geoscience Libraries
```python
import pooch
import xarray as xr

# Download NetCDF data
file_path = pooch.retrieve(
    url="https://example.com/climate_data.nc",
    known_hash=None
)

# Open with xarray
ds = xr.open_dataset(file_path)
```

### 11. Generate Hashes for Your Files
```python
import pooch

# Get hash of existing file
file_hash = pooch.file_hash("/path/to/file.csv")
print(f"SHA256: {file_hash}")

# Specify algorithm
md5_hash = pooch.file_hash("/path/to/file.csv", alg="md5")
print(f"MD5: {md5_hash}")
```

### 12. HTTP Authentication
```python
import pooch

# Basic auth for protected URLs
file_path = pooch.retrieve(
    url="https://example.com/protected/data.csv",
    known_hash=None,
    downloader=pooch.HTTPDownloader(auth=("username", "password"))
)
```

## Sample Datasets

Pooch is used by many geoscience libraries to provide sample data:

```python
# Verde sample data
import verde as vd
data = vd.datasets.fetch_rio_magnetic()

# Harmonica sample data
import harmonica as hm
data = hm.datasets.fetch_south_africa_gravity()

# These use Pooch internally
```

## Cache Locations

| OS | Default Cache Path |
|----|-------------------|
| Linux | `~/.cache/<project>` |
| macOS | `~/Library/Caches/<project>` |
| Windows | `C:\Users\<user>\AppData\Local\<project>\Cache` |

## Processor Options

| Processor | Purpose |
|-----------|---------|
| `Unzip()` | Extract ZIP archives |
| `Untar()` | Extract TAR/TAR.GZ archives |
| `Decompress()` | Decompress gzip, bz2, lzma, xz files |

## Tips

1. **Always use checksums in production** - Prevents corrupted downloads
2. **Use `pooch.os_cache()`** - Provides platform-appropriate cache location
3. **Set environment variables** - Override cache with `MYPROJECT_DATA_DIR`
4. **Version your registry** - Ensures reproducibility
5. **Use processors** - Automatically handle compressed files

## Error Handling

```python
import pooch

try:
    file_path = pooch.retrieve(
        url="https://example.com/data.csv",
        known_hash="sha256:abc123..."
    )
except pooch.exceptions.HTTPDownloadError:
    print("Download failed - check URL")
except pooch.exceptions.DownloadError:
    print("Download failed - network issue")
```

## Resources

- Documentation: https://www.fatiando.org/pooch/
- GitHub: https://github.com/fatiando/pooch
- Tutorials: https://www.fatiando.org/pooch/latest/tutorials/
