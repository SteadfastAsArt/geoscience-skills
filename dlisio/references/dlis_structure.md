# DLIS File Structure Reference

## Table of Contents
- [Overview](#overview)
- [Physical vs Logical Files](#physical-vs-logical-files)
- [Object Types](#object-types)
- [Origin Objects](#origin-objects)
- [Frame Objects](#frame-objects)
- [Channel Objects](#channel-objects)
- [Other Objects](#other-objects)
- [Data Representation](#data-representation)

## Overview

DLIS (Digital Log Interchange Standard) is defined by RP66 (API Recommended Practice 66). It's a binary format that supports:
- Multiple logical files per physical file
- Multiple frames per logical file
- Multi-dimensional data (images, waveforms)
- Rich metadata

## Physical vs Logical Files

```
Physical File (.dlis)
├── Logical File 1
│   ├── Origin
│   ├── Frame 1
│   │   ├── Channel A
│   │   ├── Channel B
│   │   └── ...
│   ├── Frame 2
│   │   └── ...
│   └── Parameters
├── Logical File 2
│   └── ...
└── ...
```

### Access in dlisio
```python
import dlisio

# load() returns all logical files
with dlisio.dlis.load('well.dlis') as files:
    print(f"Number of logical files: {len(list(files))}")

# Unpack first logical file
with dlisio.dlis.load('well.dlis') as (f, *rest):
    print(f"First file: {f.describe()}")
    print(f"Remaining files: {len(rest)}")
```

## Object Types

DLIS organizes data into typed objects:

| Type | Code | Description |
|------|------|-------------|
| ORIGIN | ORIGIN | File and well identification |
| FRAME | FRAME | Data organization and sampling |
| CHANNEL | CHANNEL | Curve definitions |
| TOOL | TOOL | Logging tool metadata |
| PARAMETER | PARAMETER | Constants and settings |
| CALIBRATION | CALIBR | Calibration data |
| EQUIPMENT | EQUIP | Equipment specifications |
| COMPUTATION | COMP | Computed curve definitions |
| PROCESS | PROCES | Processing parameters |
| ZONE | ZONE | Depth zones |
| SPLICE | SPLICE | Splice information |

### Find Objects by Type
```python
with dlisio.dlis.load('well.dlis') as (f, *_):
    # All objects of a type
    origins = f.origins
    frames = f.frames
    channels = f.channels
    tools = f.tools
    parameters = f.parameters

    # Find with filter
    matched = f.find('CHANNEL', 'GR')  # Exact match
    matched = f.find('CHANNEL', '.*GR.*', regex=True)  # Regex
```

## Origin Objects

Origin contains file and well identification:

| Attribute | Description |
|-----------|-------------|
| `well_name` | Well name |
| `field_name` | Field name |
| `company` | Operating company |
| `run_nr` | Run number |
| `creation_time` | File creation timestamp |
| `producer_code` | Producer ID |
| `producer_name` | Producer name |
| `file_id` | File identifier |
| `file_set_name` | File set name |
| `file_set_nr` | File set number |

### Access Origin Data
```python
with dlisio.dlis.load('well.dlis') as (f, *_):
    for origin in f.origins:
        print(f"Well: {origin.well_name}")
        print(f"Field: {origin.field_name}")
        print(f"Company: {origin.company}")
        print(f"Run Number: {origin.run_nr}")
        print(f"Created: {origin.creation_time}")
```

## Frame Objects

Frames group channels with common sampling:

| Attribute | Description |
|-----------|-------------|
| `name` | Frame name |
| `channels` | List of channels |
| `index_type` | Index type (e.g., BOREHOLE-DEPTH) |
| `direction` | Logging direction |
| `spacing` | Sample spacing |
| `index_min` | Minimum index value |
| `index_max` | Maximum index value |

### Work with Frames
```python
with dlisio.dlis.load('well.dlis') as (f, *_):
    for frame in f.frames:
        print(f"Frame: {frame.name}")
        print(f"  Index type: {frame.index_type}")
        print(f"  Direction: {frame.direction}")
        print(f"  Spacing: {frame.spacing}")
        print(f"  Range: {frame.index_min} - {frame.index_max}")
        print(f"  Channels: {len(frame.channels)}")

        # Read all data
        curves = frame.curves()
```

## Channel Objects

Channels define individual curves:

| Attribute | Description |
|-----------|-------------|
| `name` | Channel mnemonic |
| `long_name` | Descriptive name |
| `units` | Unit of measurement |
| `dimension` | Data dimensions |
| `reprc` | Representation code |
| `frame` | Parent frame |
| `source` | Source reference |
| `properties` | Additional properties |

### Access Channel Metadata
```python
with dlisio.dlis.load('well.dlis') as (f, *_):
    frame = f.frames[0]
    for channel in frame.channels:
        print(f"Name: {channel.name}")
        print(f"  Long name: {channel.long_name}")
        print(f"  Units: {channel.units}")
        print(f"  Dimension: {channel.dimension}")
        print(f"  Reprc: {channel.reprc}")
        print()
```

### Channel Dimensions
```python
# Scalar channels: dimension = [1]
# Array channels: dimension = [n] or [n, m]

with dlisio.dlis.load('well.dlis') as (f, *_):
    frame = f.frames[0]
    curves = frame.curves()

    for channel in frame.channels:
        data = curves[channel.name]
        if data.ndim == 1:
            print(f"{channel.name}: scalar, {len(data)} samples")
        else:
            print(f"{channel.name}: array, shape {data.shape}")
```

## Other Objects

### Tool Objects
```python
with dlisio.dlis.load('well.dlis') as (f, *_):
    for tool in f.tools:
        print(f"Tool: {tool.name}")
        print(f"  Description: {tool.description}")
        print(f"  Trademark: {tool.trademark_name}")
        print(f"  Status: {tool.status}")
```

### Parameter Objects
```python
with dlisio.dlis.load('well.dlis') as (f, *_):
    for param in f.parameters:
        print(f"{param.name}: {param.values}")
        print(f"  Units: {param.units}")
        print(f"  Zones: {param.zones}")
```

## Data Representation

DLIS uses various representation codes (reprc):

| Code | Type | Description |
|------|------|-------------|
| FSINGL | float32 | Single precision float |
| FDOUBL | float64 | Double precision float |
| SSHORT | int8 | Signed short |
| SNORM | int16 | Signed normal |
| SLONG | int32 | Signed long |
| USHORT | uint8 | Unsigned short |
| UNORM | uint16 | Unsigned normal |
| ULONG | uint32 | Unsigned long |
| ASCII | str | ASCII string |
| DTIME | datetime | Date/time |
| OBNAME | tuple | Object name reference |

### Check Representation
```python
with dlisio.dlis.load('well.dlis') as (f, *_):
    frame = f.frames[0]
    for ch in frame.channels:
        print(f"{ch.name}: {ch.reprc}")
```

## File Describe

Get a summary of file contents:

```python
with dlisio.dlis.load('well.dlis') as (f, *_):
    # Full description
    print(f.describe())

    # Or inspect manually
    print(f"Origins: {len(f.origins)}")
    print(f"Frames: {len(f.frames)}")
    print(f"Channels: {len(f.channels)}")
    print(f"Tools: {len(f.tools)}")
    print(f"Parameters: {len(f.parameters)}")
```
