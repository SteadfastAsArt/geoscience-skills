---
name: dlisio
description: |
  Read and parse DLIS (Digital Log Interchange Standard) and LIS (Log Information
  Standard) well log files. Use when Claude needs to: (1) Read/parse DLIS or LIS
  files, (2) Extract well log curves as numpy arrays, (3) Access file metadata and
  origin information, (4) Handle multi-frame or multi-file DLIS, (5) Convert DLIS
  to LAS or DataFrame, (6) Work with RP66 format well logs, (7) Process array or
  image log data.
---

# dlisio - DLIS/LIS File Reader

## Quick Reference

```python
import dlisio

# Open DLIS file (returns generator of logical files)
with dlisio.dlis.load('well.dlis') as (f, *rest):
    frame = f.frames[0]
    curves = frame.curves()

    # Access by channel name
    depth = curves['DEPTH']
    gr = curves['GR']

    # File metadata
    for origin in f.origins:
        print(origin.well_name, origin.field_name)
```

## Key Classes

| Class | Purpose |
|-------|---------|
| `PhysicalFile` | Container returned by `dlis.load()` |
| `LogicalFile` | Independent dataset within physical file |
| `Frame` | Group of channels with common sampling |
| `Channel` | Individual log curve with metadata |
| `Origin` | Well and file metadata |

## Essential Operations

### Read Curves to DataFrame
```python
import pandas as pd

with dlisio.dlis.load('well.dlis') as (f, *_):
    frame = f.frames[0]
    curves = frame.curves()
    df = pd.DataFrame(curves)
    df.set_index('DEPTH', inplace=True)
```

### Access Channel and Origin Metadata
```python
with dlisio.dlis.load('well.dlis') as (f, *_):
    # Origin metadata
    for origin in f.origins:
        print(f"Well: {origin.well_name}, Field: {origin.field_name}")

    # Channel properties
    for ch in f.frames[0].channels:
        print(f"{ch.name}: {ch.units}, dim={ch.dimension}")
```

### Find Channels Across Frames
```python
with dlisio.dlis.load('well.dlis') as (f, *_):
    # By exact name or regex
    channels = f.find('CHANNEL', '.*GR.*', regex=True)

    # Find frame containing specific channel
    for frame in f.frames:
        if 'GR' in [ch.name for ch in frame.channels]:
            curves = frame.curves()
            break
```

### Handle Array Channels
```python
with dlisio.dlis.load('well.dlis') as (f, *_):
    curves = f.frames[0].curves()
    for name, data in curves.items():
        if data.ndim > 1:
            print(f"{name}: shape = {data.shape}")  # Image/waveform
```

## Common Object Types

| Object Type | Description |
|-------------|-------------|
| ORIGIN | File/well metadata |
| FRAME | Channel grouping with index |
| CHANNEL | Log curve definition |
| TOOL | Logging tool info |
| PARAMETER | Constants and settings |

## Common Curve Names

| Curve | Description |
|-------|-------------|
| DEPT, DEPTH, TDEP | Depth curves |
| GR | Gamma ray |
| NPHI | Neutron porosity |
| RHOB | Bulk density |
| DT, DTC | Compressional slowness |
| RT, ILD | Resistivity |

## Error Handling

```python
dlisio.dlis.set_encodings(['utf-8', 'latin-1'])

try:
    with dlisio.dlis.load('file.dlis') as files:
        for f in files:
            curves = f.frames[0].curves()
except Exception as e:
    print(f"Error: {e}")
```

## DLIS vs LAS Comparison

| Feature | DLIS | LAS |
|---------|------|-----|
| Format | Binary | ASCII |
| Multi-frame | Yes | No |
| Array data | Yes | Limited |
| Metadata | Rich | Basic |

## References

- **[DLIS File Structure](references/dlis_structure.md)** - RP66 format specification
- **[Frames and Channels](references/frame_channels.md)** - Working with frames and channels

## Scripts

- **[scripts/dlis_to_las.py](scripts/dlis_to_las.py)** - Convert DLIS to LAS format
