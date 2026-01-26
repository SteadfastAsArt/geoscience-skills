---
name: dlisio
description: Read DLIS and LIS well log files. Parse modern digital well log formats, extract curves, and access file metadata.
---

# dlisio - DLIS/LIS File Reader

Help users read DLIS and LIS well log file formats.

## Installation

```bash
pip install dlisio
```

## Core Concepts

### What dlisio Does
- Read DLIS (Digital Log Interchange Standard) files
- Read LIS (Log Information Standard) files
- Extract log curves as numpy arrays
- Access file and frame metadata
- Handle multi-file and multi-frame DLIS

### File Structure
DLIS files contain:
- **Logical Files** - Independent datasets within physical file
- **Frames** - Groups of channels with common sampling
- **Channels** - Individual log curves
- **Parameters** - Metadata and constants

## Common Workflows

### 1. Open and Explore DLIS File
```python
import dlisio

# Open DLIS file (returns generator of logical files)
with dlisio.dlis.load('well.dlis') as files:
    for f in files:
        print(f"Logical file: {f.describe()}")

        # List available frames
        for frame in f.frames:
            print(f"  Frame: {frame.name}")
            print(f"  Channels: {[ch.name for ch in frame.channels]}")
```

### 2. Read Specific Curves
```python
import dlisio
import numpy as np

with dlisio.dlis.load('well.dlis') as (f, *_):
    # Get first frame
    frame = f.frames[0]

    # Read all curves in frame
    curves = frame.curves()

    # Access by channel name
    depth = curves['DEPTH']
    gr = curves['GR']
    nphi = curves['NPHI']

    print(f"Depth range: {depth.min():.1f} - {depth.max():.1f}")
    print(f"GR range: {gr.min():.1f} - {gr.max():.1f}")
```

### 3. Convert to Pandas DataFrame
```python
import dlisio
import pandas as pd

with dlisio.dlis.load('well.dlis') as (f, *_):
    frame = f.frames[0]
    curves = frame.curves()

    # Convert to DataFrame
    df = pd.DataFrame(curves)

    # Set depth as index
    df.set_index('DEPTH', inplace=True)

    print(df.head())
    print(df.describe())
```

### 4. Access File Metadata
```python
import dlisio

with dlisio.dlis.load('well.dlis') as (f, *_):
    # Origin information
    for origin in f.origins:
        print(f"Well: {origin.well_name}")
        print(f"Field: {origin.field_name}")
        print(f"Company: {origin.company}")
        print(f"Run number: {origin.run_nr}")
        print(f"Creation time: {origin.creation_time}")

    # Parameters
    for param in f.parameters:
        print(f"{param.name}: {param.values}")
```

### 5. Handle Multi-Frame Files
```python
import dlisio

with dlisio.dlis.load('well.dlis') as (f, *_):
    # Find frame with specific channel
    for frame in f.frames:
        channel_names = [ch.name for ch in frame.channels]
        if 'GR' in channel_names:
            print(f"GR found in frame: {frame.name}")
            curves = frame.curves()
            gr = curves['GR']
            break
```

### 6. Channel Properties
```python
import dlisio

with dlisio.dlis.load('well.dlis') as (f, *_):
    frame = f.frames[0]

    for channel in frame.channels:
        print(f"Name: {channel.name}")
        print(f"  Long name: {channel.long_name}")
        print(f"  Units: {channel.units}")
        print(f"  Dimension: {channel.dimension}")
        print(f"  Representation: {channel.reprc}")
        print()
```

### 7. Handle Array Channels
```python
import dlisio
import numpy as np

with dlisio.dlis.load('well.dlis') as (f, *_):
    frame = f.frames[0]
    curves = frame.curves()

    # Some channels are multi-dimensional (e.g., waveforms, images)
    for name, data in curves.items():
        if data.ndim > 1:
            print(f"{name}: shape = {data.shape}")
        else:
            print(f"{name}: {len(data)} samples")
```

### 8. Read LIS Files
```python
import dlisio.lis

# Open LIS file
with dlisio.lis.load('well.lis') as files:
    for f in files:
        # Get data records
        for record in f.data_records():
            print(f"Record type: {record.type}")

        # Read curves
        curves = f.curves()
        print(curves.keys())
```

### 9. Find Specific Objects
```python
import dlisio

with dlisio.dlis.load('well.dlis') as (f, *_):
    # Find all objects by type
    tools = f.find('TOOL')
    for tool in tools:
        print(f"Tool: {tool.name}, {tool.description}")

    # Find channels matching pattern
    channels = f.find('CHANNEL', '.*GR.*', regex=True)
    for ch in channels:
        print(f"Channel: {ch.name}")
```

### 10. Export to LAS
```python
import dlisio
import lasio
import numpy as np

with dlisio.dlis.load('well.dlis') as (f, *_):
    frame = f.frames[0]
    curves = frame.curves()

    # Create LAS file
    las = lasio.LASFile()

    # Add header info
    for origin in f.origins:
        las.well.WELL = origin.well_name or ''
        las.well.FLD = origin.field_name or ''

    # Add curves
    for channel in frame.channels:
        name = channel.name
        data = curves[name]

        # Skip multi-dimensional data
        if data.ndim > 1:
            continue

        las.append_curve(
            name,
            data,
            unit=channel.units or ''
        )

    las.write('output.las')
```

### 11. Plot Curves
```python
import dlisio
import matplotlib.pyplot as plt

with dlisio.dlis.load('well.dlis') as (f, *_):
    frame = f.frames[0]
    curves = frame.curves()

    depth = curves['DEPTH']
    gr = curves['GR']
    nphi = curves['NPHI']

    fig, axes = plt.subplots(1, 2, figsize=(10, 12), sharey=True)

    # GR track
    axes[0].plot(gr, depth, 'g-')
    axes[0].set_xlabel('GR (API)')
    axes[0].set_xlim(0, 150)
    axes[0].invert_yaxis()

    # NPHI track
    axes[1].plot(nphi, depth, 'b-')
    axes[1].set_xlabel('NPHI (v/v)')
    axes[1].set_xlim(0.45, -0.15)

    plt.tight_layout()
    plt.show()
```

### 12. Handle Encrypted or Problematic Files
```python
import dlisio

# Set error handling
dlisio.dlis.set_encodings(['utf-8', 'latin-1'])

try:
    with dlisio.dlis.load('problem.dlis') as files:
        for f in files:
            try:
                frame = f.frames[0]
                curves = frame.curves()
            except Exception as e:
                print(f"Error reading frame: {e}")
except Exception as e:
    print(f"Error loading file: {e}")
```

## DLIS Structure Reference

| Object Type | Description |
|-------------|-------------|
| ORIGIN | File/well metadata |
| FRAME | Channel grouping with index |
| CHANNEL | Log curve definition |
| TOOL | Logging tool info |
| PARAMETER | Constants and settings |
| CALIBRATION | Tool calibration data |

## Common Curve Names

| Curve | Description |
|-------|-------------|
| DEPT, DEPTH | Measured depth |
| TDEP | True vertical depth |
| GR | Gamma ray |
| NPHI | Neutron porosity |
| RHOB | Bulk density |
| DT, DTC | Compressional slowness |
| RT, ILD | Resistivity |
| SP | Spontaneous potential |
| CALI | Caliper |

## Tips

1. **Use context manager** - Ensures proper file cleanup
2. **Handle multiple logical files** - DLIS can contain several
3. **Check channel dimensions** - Some are multi-dimensional
4. **Try multiple encodings** - For files with special characters
5. **Convert to DataFrame** - Easier analysis with pandas

## Comparison: DLIS vs LAS

| Feature | DLIS | LAS |
|---------|------|-----|
| Format | Binary | ASCII |
| Multi-frame | Yes | No |
| Array data | Yes | Limited |
| Metadata | Rich | Basic |
| File size | Smaller | Larger |
| Readability | Machine | Human |

## Resources

- Documentation: https://dlisio.readthedocs.io/
- GitHub: https://github.com/equinor/dlisio
- DLIS Standard: RP66 (API)
