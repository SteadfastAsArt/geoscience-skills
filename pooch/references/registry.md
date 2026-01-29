# Pooch Registry Configuration

## Overview

A Pooch registry manages multiple data files with versioning, checksums, and automatic caching. Use registries for reproducible scientific workflows.

## Creating a Registry

### Basic Registry

```python
import pooch

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

# Fetch files (downloads once, then uses cache)
eq_file = REGISTRY.fetch("earthquakes.csv")
stations_file = REGISTRY.fetch("stations.json")
```

### With Environment Variable Override

```python
import pooch

REGISTRY = pooch.create(
    path=pooch.os_cache("myproject"),
    base_url="https://example.com/data/",
    version="1.0.0",
    env="MYPROJECT_DATA_DIR",  # Users can override cache location
    registry={
        "data.csv": "sha256:abc123...",
    }
)
```

Users can then set: `export MYPROJECT_DATA_DIR=/custom/path`

### With Mirror URLs

```python
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

## Registry Parameters

| Parameter | Description |
|-----------|-------------|
| `path` | Local cache directory |
| `base_url` | Base URL for file downloads |
| `version` | Version string (creates subdirectory) |
| `env` | Environment variable to override path |
| `registry` | Dict mapping filenames to hashes |
| `urls` | Dict mapping filenames to URL lists |

## Loading Registry from File

### Registry File Format (registry.txt)

```
earthquakes.csv sha256:abc123def456...
stations.json sha256:789ghi012jkl...
model.nc sha256:mno345pqr678...
```

### Load from File

```python
import pooch

REGISTRY = pooch.create(
    path=pooch.os_cache("myproject"),
    base_url="https://example.com/data/",
    version="1.0.0",
    registry=None,  # Will load from file
)

# Load registry from text file
REGISTRY.load_registry("registry.txt")

# Or from package resources
REGISTRY.load_registry(
    pooch.os.path.join(os.path.dirname(__file__), "registry.txt")
)
```

## Generating Hashes

### Single File

```python
import pooch

# Default SHA256
hash_value = pooch.file_hash("/path/to/file.csv")
print(f"sha256:{hash_value}")

# MD5
hash_value = pooch.file_hash("/path/to/file.csv", alg="md5")
print(f"md5:{hash_value}")
```

### Generate Registry for Directory

See `scripts/create_registry.py` for automated registry generation.

## Versioning Strategy

### Semantic Versioning

```python
REGISTRY = pooch.create(
    path=pooch.os_cache("myproject"),
    base_url="https://example.com/data/",
    version="1.2.3",  # Major.Minor.Patch
    registry={...}
)
# Files cached in: ~/.cache/myproject/1.2.3/
```

### Development Version

```python
REGISTRY = pooch.create(
    path=pooch.os_cache("myproject"),
    base_url="https://example.com/data/",
    version_dev="main",  # Use during development
    version="1.0.0",     # Released version
    registry={...}
)
```

## Fetch with Processors

```python
# Fetch and decompress
data_file = REGISTRY.fetch(
    "data.csv.gz",
    processor=pooch.Decompress()
)

# Fetch and extract
data_files = REGISTRY.fetch(
    "archive.zip",
    processor=pooch.Unzip()
)
```

## Best Practices

1. **Always use checksums** - Ensures data integrity and reproducibility
2. **Version your registry** - Different versions can coexist in cache
3. **Use environment variables** - Allow users to customize cache location
4. **Provide mirrors** - Improves reliability for large files
5. **Document data sources** - Include DOIs and citations in your code
6. **Keep registry updated** - Regenerate hashes when data files change

## Common Patterns

### Package Data Module

```python
# mypackage/data/__init__.py
import pooch
import os

REGISTRY = pooch.create(
    path=pooch.os_cache("mypackage"),
    base_url="https://github.com/org/mypackage/raw/main/data/",
    version="1.0.0",
    env="MYPACKAGE_DATA_DIR",
    registry=None,
)

REGISTRY.load_registry(
    os.path.join(os.path.dirname(__file__), "registry.txt")
)

def fetch_earthquakes():
    """Fetch earthquake catalog."""
    return REGISTRY.fetch("earthquakes.csv")

def fetch_stations():
    """Fetch station metadata."""
    return REGISTRY.fetch("stations.json")
```

### Integration with pandas/xarray

```python
import pandas as pd
import xarray as xr

# CSV data
df = pd.read_csv(REGISTRY.fetch("data.csv"))

# NetCDF data
ds = xr.open_dataset(REGISTRY.fetch("model.nc"))
```
