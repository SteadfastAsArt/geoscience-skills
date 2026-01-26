---
name: segyio
description: Read and write SEG-Y and Seismic Unix seismic data files. Fast C library with Python bindings for trace, header, inline, and crossline access.
---

# segyio - SEG-Y File Handler

Help users read, write, and manipulate SEG-Y seismic data files efficiently.

## Installation

```bash
pip install segyio
```

## Core Concepts

### SEG-Y Structure
- **Text header** - 3200-byte EBCDIC/ASCII header
- **Binary header** - File-wide parameters
- **Trace headers** - Per-trace metadata (240 bytes each)
- **Trace data** - Seismic samples

### Access Modes
| Mode | Description |
|------|-------------|
| `trace` | Sequential trace access by index |
| `header` | Trace header access |
| `iline` | Inline-indexed (3D surveys) |
| `xline` | Crossline-indexed (3D surveys) |
| `depth_slice` | Horizontal time/depth slices |
| `gather` | CDP gathers |

## Common Workflows

### 1. Open and Inspect File
```python
import segyio

with segyio.open('seismic.sgy', 'r') as f:
    print(f"Traces: {f.tracecount}")
    print(f"Samples per trace: {len(f.samples)}")
    print(f"Sample interval: {f.samples[1] - f.samples[0]} ms")

    # For 3D data
    if f.ilines is not None:
        print(f"Inlines: {f.ilines}")
        print(f"Crosslines: {f.xlines}")
```

### 2. Read Trace Data
```python
import segyio
import numpy as np

with segyio.open('seismic.sgy', 'r') as f:
    # Single trace
    trace0 = f.trace[0]  # numpy array

    # Multiple traces
    traces = f.trace[10:20]  # Returns generator

    # All traces as 2D array
    data = segyio.tools.collect(f.trace[:])
    # Shape: (n_traces, n_samples)
```

### 3. Read Trace Headers
```python
import segyio

with segyio.open('seismic.sgy', 'r') as f:
    # Single trace header
    header = f.header[0]

    # Common header fields
    print(header[segyio.TraceField.INLINE_3D])
    print(header[segyio.TraceField.CROSSLINE_3D])
    print(header[segyio.TraceField.CDP_X])
    print(header[segyio.TraceField.CDP_Y])
    print(header[segyio.TraceField.offset])

    # Get all values for one field
    inlines = f.attributes(segyio.TraceField.INLINE_3D)[:]
```

### 4. Read 3D Data by Inline/Crossline
```python
import segyio

with segyio.open('seismic.sgy', 'r', iline=189, xline=193) as f:
    # Read single inline
    inline_100 = f.iline[100]  # 2D array (xlines x samples)

    # Read single crossline
    xline_200 = f.xline[200]  # 2D array (ilines x samples)

    # Read depth/time slice
    slice_500ms = f.depth_slice[250]  # 2D array (ilines x xlines)

    # Full 3D cube
    cube = segyio.tools.cube(f)
    # Shape: (n_ilines, n_xlines, n_samples)
```

### 5. Read Unstructured Data
```python
import segyio

# For 2D lines or unsorted data
with segyio.open('seismic.sgy', 'r', ignore_geometry=True) as f:
    data = segyio.tools.collect(f.trace[:])
```

### 6. Read Text and Binary Headers
```python
import segyio

with segyio.open('seismic.sgy', 'r') as f:
    # Text header (3200 bytes)
    text = f.text[0]
    print(text)

    # Binary header
    print(f.bin[segyio.BinField.Interval])      # Sample interval
    print(f.bin[segyio.BinField.Samples])        # Samples per trace
    print(f.bin[segyio.BinField.Format])         # Data format
```

### 7. Create New SEG-Y File
```python
import segyio
import numpy as np

# Define geometry
n_traces = 100
n_samples = 500
sample_interval = 4000  # microseconds (4ms)

# Create spec
spec = segyio.spec()
spec.samples = np.arange(n_samples) * sample_interval / 1000
spec.tracecount = n_traces
spec.format = 1  # IBM float

# Create synthetic data
data = np.random.randn(n_traces, n_samples).astype(np.float32)

# Write file
with segyio.create('output.sgy', spec) as f:
    for i, trace in enumerate(data):
        f.trace[i] = trace
        f.header[i] = {
            segyio.TraceField.TRACE_SEQUENCE_LINE: i + 1,
            segyio.TraceField.CDP: i + 1,
        }
```

### 8. Create 3D SEG-Y File
```python
import segyio
import numpy as np

ilines = np.arange(1, 51)    # 50 inlines
xlines = np.arange(1, 101)   # 100 crosslines
n_samples = 500

spec = segyio.spec()
spec.sorting = 2  # Inline sorting
spec.format = 1
spec.ilines = ilines
spec.xlines = xlines
spec.samples = np.arange(n_samples) * 4  # 4ms sample rate

# Create cube
cube = np.random.randn(len(ilines), len(xlines), n_samples)

with segyio.create('output_3d.sgy', spec) as f:
    for i, il in enumerate(ilines):
        for j, xl in enumerate(xlines):
            tr_idx = i * len(xlines) + j
            f.trace[tr_idx] = cube[i, j, :]
            f.header[tr_idx] = {
                segyio.TraceField.INLINE_3D: il,
                segyio.TraceField.CROSSLINE_3D: xl,
            }
```

### 9. Modify Existing File
```python
import segyio

# Open for read/write
with segyio.open('seismic.sgy', 'r+') as f:
    # Modify trace data
    f.trace[0] = f.trace[0] * 2.0

    # Modify header
    f.header[0][segyio.TraceField.TRACE_SEQUENCE_LINE] = 999

    # Modify text header
    f.text[0] = "Modified header text..."
```

### 10. Extract Subset
```python
import segyio

with segyio.open('large.sgy', 'r', iline=189, xline=193) as src:
    # Define subset
    il_subset = range(100, 200)
    xl_subset = range(50, 150)

    spec = segyio.spec()
    spec.sorting = 2
    spec.format = src.format
    spec.ilines = list(il_subset)
    spec.xlines = list(xl_subset)
    spec.samples = src.samples

    with segyio.create('subset.sgy', spec) as dst:
        idx = 0
        for il in il_subset:
            for xl in xl_subset:
                dst.trace[idx] = src.iline[il][:, xl_subset.index(xl)]
                idx += 1
```

## Important Trace Header Fields

| Field | Bytes | Description |
|-------|-------|-------------|
| `TRACE_SEQUENCE_LINE` | 1-4 | Trace sequence number |
| `INLINE_3D` | 189-192 | Inline number |
| `CROSSLINE_3D` | 193-196 | Crossline number |
| `CDP` | 21-24 | CDP number |
| `CDP_X` | 181-184 | X coordinate |
| `CDP_Y` | 185-188 | Y coordinate |
| `offset` | 37-40 | Source-receiver offset |
| `TRACE_SAMPLE_COUNT` | 115-116 | Samples in trace |
| `TRACE_SAMPLE_INTERVAL` | 117-118 | Sample interval |

## Data Formats

| Code | Format |
|------|--------|
| 1 | IBM 4-byte float |
| 2 | 4-byte signed integer |
| 3 | 2-byte signed integer |
| 5 | IEEE 4-byte float |
| 8 | 1-byte signed integer |

## Tips

1. **Always use context manager** - ensures file is closed properly
2. **Specify iline/xline bytes** for 3D - not all files use 189/193
3. **Use `ignore_geometry=True`** for unstructured data
4. **Check byte order** - SEG-Y is big-endian by default
5. **Use `segyio.tools.cube()`** for fast 3D loading

## Resources

- GitHub: https://github.com/equinor/segyio
- Documentation: https://segyio.readthedocs.io/
- SEG-Y Standard: https://seg.org/Portals/0/SEG/News%20and%20Resources/Technical%20Standards/seg_y_rev2_0-mar2017.pdf
