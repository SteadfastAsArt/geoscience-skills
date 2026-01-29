# SEG-Y Troubleshooting Guide

## Table of Contents
- [Opening Files](#opening-files)
- [3D Geometry Issues](#3d-geometry-issues)
- [Header Issues](#header-issues)
- [Data Issues](#data-issues)
- [Writing Issues](#writing-issues)
- [Performance](#performance)

## Opening Files

### File Won't Open

**Problem**: `RuntimeError` or file not found errors

```python
# Check file exists and is readable
import os
print(os.path.exists('file.sgy'))
print(os.access('file.sgy', os.R_OK))

# Try with ignore_geometry for unstructured files
with segyio.open('file.sgy', 'r', ignore_geometry=True) as f:
    print(f.tracecount)
```

### Strict Mode Errors

**Problem**: File fails validation

```python
# Disable strict mode
with segyio.open('file.sgy', 'r', strict=False) as f:
    data = f.trace[0]
```

### Endianness Issues

**Problem**: Data appears corrupted or extreme values

```python
# SEG-Y is big-endian by default
# Try specifying endianness explicitly
with segyio.open('file.sgy', 'r', endian='big') as f:
    trace = f.trace[0]

# Or try little-endian
with segyio.open('file.sgy', 'r', endian='little') as f:
    trace = f.trace[0]
```

## 3D Geometry Issues

### Geometry Not Detected

**Problem**: `f.ilines` or `f.xlines` returns None

```python
# Find correct inline/crossline byte positions
with segyio.open('file.sgy', 'r', ignore_geometry=True) as f:
    h = f.header[0]
    # Check common locations
    print(f"Bytes 189-192: {h[segyio.TraceField.INLINE_3D]}")
    print(f"Bytes 193-196: {h[segyio.TraceField.CROSSLINE_3D]}")
    print(f"Bytes 9-12: {h[segyio.TraceField.FieldRecord]}")
    print(f"Bytes 21-24: {h[segyio.TraceField.CDP]}")

# Then open with correct byte positions
with segyio.open('file.sgy', 'r', iline=189, xline=193) as f:
    print(f.ilines)
```

### Wrong Inline/Crossline Ranges

**Problem**: Inline/crossline numbers don't match expected geometry

```python
# Scan all headers to find actual ranges
with segyio.open('file.sgy', 'r', ignore_geometry=True) as f:
    ilines = f.attributes(segyio.TraceField.INLINE_3D)[:]
    xlines = f.attributes(segyio.TraceField.CROSSLINE_3D)[:]
    print(f"Inline range: {min(ilines)} to {max(ilines)}")
    print(f"Crossline range: {min(xlines)} to {max(xlines)}")
    print(f"Unique inlines: {len(set(ilines))}")
    print(f"Unique xlines: {len(set(xlines))}")
```

### Unsorted or 2D Data

**Problem**: 3D access methods fail on 2D or pre-stack data

```python
# Use ignore_geometry for non-3D stacked data
with segyio.open('file.sgy', 'r', ignore_geometry=True) as f:
    # Access traces sequentially
    for i, trace in enumerate(f.trace):
        header = f.header[i]
        # Process trace...
```

## Header Issues

### Reading Non-Standard Header Locations

**Problem**: Data is stored in non-standard byte locations

```python
# Read raw header bytes
with segyio.open('file.sgy', 'r', ignore_geometry=True) as f:
    # Access header as dictionary
    h = f.header[0]

    # List all non-zero header values
    for field in segyio.TraceField.enums():
        val = h[field]
        if val != 0:
            print(f"{field.name} (byte {int(field)}): {val}")
```

### Coordinate Scaling

**Problem**: Coordinates appear too large or too small

```python
with segyio.open('file.sgy', 'r', ignore_geometry=True) as f:
    h = f.header[0]

    # Get scalar (bytes 71-72)
    scalar = h[segyio.TraceField.SourceGroupScalar]

    # Apply scaling
    cdp_x = h[segyio.TraceField.CDP_X]
    cdp_y = h[segyio.TraceField.CDP_Y]

    if scalar < 0:
        x = cdp_x / abs(scalar)
        y = cdp_y / abs(scalar)
    elif scalar > 0:
        x = cdp_x * scalar
        y = cdp_y * scalar
    else:
        x, y = cdp_x, cdp_y

    print(f"Scaled coordinates: ({x}, {y})")
```

### Missing Header Values

**Problem**: Expected header fields contain zeros

```python
# Check text header for documentation
with segyio.open('file.sgy', 'r') as f:
    print(f.text[0])  # Often documents non-standard header usage

# Check binary header
with segyio.open('file.sgy', 'r') as f:
    for field in segyio.BinField.enums():
        val = f.bin[field]
        if val != 0:
            print(f"{field.name}: {val}")
```

## Data Issues

### Extreme or NaN Values

**Problem**: Trace data contains unexpected values

```python
import numpy as np

with segyio.open('file.sgy', 'r', ignore_geometry=True) as f:
    trace = f.trace[0]
    print(f"Min: {np.nanmin(trace)}")
    print(f"Max: {np.nanmax(trace)}")
    print(f"NaN count: {np.sum(np.isnan(trace))}")
    print(f"Inf count: {np.sum(np.isinf(trace))}")

    # Check data format
    print(f"Format code: {f.format}")
```

### Wrong Sample Count

**Problem**: Trace length doesn't match expected

```python
with segyio.open('file.sgy', 'r', ignore_geometry=True) as f:
    # Check binary header
    print(f"Binary header samples: {f.bin[segyio.BinField.Samples]}")

    # Check trace header
    h = f.header[0]
    print(f"Trace header samples: {h[segyio.TraceField.TRACE_SAMPLE_COUNT]}")

    # Actual samples
    print(f"Actual samples: {len(f.samples)}")
```

### Sample Interval Mismatch

**Problem**: Time axis doesn't match expected

```python
with segyio.open('file.sgy', 'r') as f:
    # Binary header (microseconds)
    bin_interval = f.bin[segyio.BinField.Interval]

    # Trace header (microseconds)
    tr_interval = f.header[0][segyio.TraceField.TRACE_SAMPLE_INTERVAL]

    # Computed from samples array (milliseconds)
    if len(f.samples) > 1:
        computed = f.samples[1] - f.samples[0]

    print(f"Binary header: {bin_interval} us")
    print(f"Trace header: {tr_interval} us")
    print(f"Computed: {computed} ms")
```

## Writing Issues

### Creating 3D SEG-Y

**Problem**: Written file doesn't have correct 3D structure

```python
import numpy as np

ilines = np.arange(1, 51)
xlines = np.arange(1, 101)
n_samples = 500

spec = segyio.spec()
spec.sorting = 2  # Inline sorting (critical for 3D)
spec.format = 1   # IBM float
spec.ilines = ilines
spec.xlines = xlines
spec.samples = np.arange(n_samples) * 4  # 4ms

with segyio.create('output.sgy', spec) as f:
    for i, il in enumerate(ilines):
        for j, xl in enumerate(xlines):
            tr_idx = i * len(xlines) + j
            f.trace[tr_idx] = data[i, j, :]
            f.header[tr_idx] = {
                segyio.TraceField.INLINE_3D: il,
                segyio.TraceField.CROSSLINE_3D: xl,
            }
```

### Text Header Encoding

**Problem**: Text header appears garbled

```python
# Write ASCII text header (not EBCDIC)
with segyio.create('output.sgy', spec) as f:
    text = "C01 Created with segyio\n" + "C02 ...\n" * 39
    # Pad to exactly 3200 characters
    text = text.ljust(3200)[:3200]
    f.text[0] = text
```

### Preserving Original Headers

**Problem**: Need to copy headers from source file

```python
with segyio.open('source.sgy', 'r') as src:
    spec = segyio.tools.metadata(src)

    with segyio.create('dest.sgy', spec) as dst:
        # Copy text header
        dst.text[0] = src.text[0]

        # Copy binary header
        dst.bin = src.bin

        # Copy traces with headers
        for i in range(src.tracecount):
            dst.trace[i] = src.trace[i]
            dst.header[i] = src.header[i]
```

## Performance

### Large File Handling

**Problem**: Memory issues with large files

```python
# Process traces in batches
batch_size = 1000
with segyio.open('large.sgy', 'r', ignore_geometry=True) as f:
    for start in range(0, f.tracecount, batch_size):
        end = min(start + batch_size, f.tracecount)
        traces = [f.trace[i] for i in range(start, end)]
        # Process batch...
```

### Memory-Mapped Access

**Problem**: Need efficient random access

```python
# segyio uses memory mapping by default
# For explicit control:
with segyio.open('file.sgy', 'r') as f:
    # Access is already memory-mapped
    # Random access is efficient
    trace_1000 = f.trace[1000]
    trace_5000 = f.trace[5000]
```

### Parallel Reading

**Problem**: Need to speed up processing

```python
from concurrent.futures import ProcessPoolExecutor
import segyio

def process_traces(args):
    filepath, start, end = args
    with segyio.open(filepath, 'r', ignore_geometry=True) as f:
        results = []
        for i in range(start, end):
            trace = f.trace[i]
            # Process...
            results.append(result)
    return results

# Split work across processes
filepath = 'large.sgy'
with segyio.open(filepath, 'r', ignore_geometry=True) as f:
    n_traces = f.tracecount

chunks = [(filepath, i, min(i+1000, n_traces))
          for i in range(0, n_traces, 1000)]

with ProcessPoolExecutor(max_workers=4) as executor:
    all_results = list(executor.map(process_traces, chunks))
```
