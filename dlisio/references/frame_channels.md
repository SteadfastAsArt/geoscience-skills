# Frames and Channels Reference

## Table of Contents
- [Understanding Frames](#understanding-frames)
- [Working with Channels](#working-with-channels)
- [Reading Curve Data](#reading-curve-data)
- [Multi-Dimensional Data](#multi-dimensional-data)
- [Frame Selection Strategies](#frame-selection-strategies)
- [Performance Tips](#performance-tips)

## Understanding Frames

Frames are the fundamental data organization unit in DLIS. Each frame:
- Groups channels with the same sampling
- Has an index channel (usually depth or time)
- Contains one or more measurement channels

### Why Multiple Frames?

DLIS files often contain multiple frames because:
- Different tools sample at different rates
- Some data is depth-indexed, some is time-indexed
- Image data needs different sampling than scalar curves
- Different logging runs may be combined

### List All Frames
```python
import dlisio

with dlisio.dlis.load('well.dlis') as (f, *_):
    print(f"Number of frames: {len(f.frames)}")

    for i, frame in enumerate(f.frames):
        print(f"\nFrame {i}: {frame.name}")
        print(f"  Index: {frame.index_type}")
        print(f"  Channels: {len(frame.channels)}")
        print(f"  Range: {frame.index_min} - {frame.index_max}")
```

### Frame Properties
```python
with dlisio.dlis.load('well.dlis') as (f, *_):
    frame = f.frames[0]

    # Basic info
    print(f"Name: {frame.name}")
    print(f"Description: {frame.description}")

    # Index info
    print(f"Index type: {frame.index_type}")  # e.g., BOREHOLE-DEPTH
    print(f"Index min: {frame.index_min}")
    print(f"Index max: {frame.index_max}")
    print(f"Spacing: {frame.spacing}")
    print(f"Direction: {frame.direction}")  # INCREASING or DECREASING

    # Encrypted flag
    print(f"Encrypted: {frame.encrypted}")
```

## Working with Channels

Channels represent individual curves within a frame.

### List Channels in Frame
```python
with dlisio.dlis.load('well.dlis') as (f, *_):
    frame = f.frames[0]

    for ch in frame.channels:
        print(f"{ch.name}: {ch.units} ({ch.long_name})")
```

### Channel Attributes
```python
with dlisio.dlis.load('well.dlis') as (f, *_):
    frame = f.frames[0]
    channel = frame.channels[0]

    # Identification
    print(f"Name: {channel.name}")
    print(f"Long name: {channel.long_name}")

    # Data info
    print(f"Units: {channel.units}")
    print(f"Dimension: {channel.dimension}")
    print(f"Representation: {channel.reprc}")

    # References
    print(f"Frame: {channel.frame.name}")
    print(f"Source: {channel.source}")
    print(f"Properties: {channel.properties}")
```

### Find Channel by Name
```python
with dlisio.dlis.load('well.dlis') as (f, *_):
    # Search all frames
    for frame in f.frames:
        for ch in frame.channels:
            if ch.name == 'GR':
                print(f"Found GR in frame {frame.name}")
                curves = frame.curves()
                gr_data = curves['GR']
                break

    # Or use find()
    channels = f.find('CHANNEL', 'GR')
    for ch in channels:
        print(f"GR channel in frame: {ch.frame.name}")
```

## Reading Curve Data

### Read All Curves in Frame
```python
with dlisio.dlis.load('well.dlis') as (f, *_):
    frame = f.frames[0]

    # Returns structured numpy array
    curves = frame.curves()

    # Access by name
    depth = curves['DEPTH']
    gr = curves['GR']

    print(f"Type: {type(curves)}")  # numpy.ndarray (structured)
    print(f"Fields: {curves.dtype.names}")
    print(f"Samples: {len(curves)}")
```

### Convert to DataFrame
```python
import pandas as pd

with dlisio.dlis.load('well.dlis') as (f, *_):
    frame = f.frames[0]
    curves = frame.curves()

    # Direct conversion
    df = pd.DataFrame(curves)

    # With depth index
    df.set_index('DEPTH', inplace=True)

    print(df.head())
    print(df.describe())
```

### Read Specific Channels Only
```python
with dlisio.dlis.load('well.dlis') as (f, *_):
    frame = f.frames[0]
    curves = frame.curves()

    # Select specific columns
    wanted = ['DEPTH', 'GR', 'NPHI', 'RHOB']
    available = [c for c in wanted if c in curves.dtype.names]

    # Extract as dict
    data = {name: curves[name] for name in available}
```

## Multi-Dimensional Data

DLIS supports array channels for images, waveforms, and spectra.

### Identify Array Channels
```python
with dlisio.dlis.load('well.dlis') as (f, *_):
    frame = f.frames[0]
    curves = frame.curves()

    for ch in frame.channels:
        data = curves[ch.name]
        if data.ndim > 1:
            print(f"{ch.name}: {data.shape} (array)")
        else:
            print(f"{ch.name}: {data.shape} (scalar)")
```

### Working with Image Data
```python
import matplotlib.pyplot as plt
import numpy as np

with dlisio.dlis.load('well.dlis') as (f, *_):
    frame = f.frames[0]
    curves = frame.curves()

    # Find image channel
    for ch in frame.channels:
        if ch.dimension[0] > 1:  # Multi-sample
            image_data = curves[ch.name]
            print(f"Image: {ch.name}, shape: {image_data.shape}")

            # Plot image
            plt.figure(figsize=(8, 12))
            plt.imshow(image_data, aspect='auto', cmap='viridis')
            plt.colorbar(label=ch.units)
            plt.title(ch.name)
            plt.show()
            break
```

### Handling Waveform Data
```python
with dlisio.dlis.load('well.dlis') as (f, *_):
    for frame in f.frames:
        curves = frame.curves()
        for ch in frame.channels:
            data = curves[ch.name]
            if len(ch.dimension) > 1 and data.ndim == 2:
                n_samples, n_points = data.shape
                print(f"Waveform {ch.name}: {n_samples} traces, {n_points} points each")
```

## Frame Selection Strategies

### Find Frame with Specific Channel
```python
def find_frame_with_channel(logical_file, channel_name):
    """Find the frame containing a specific channel."""
    for frame in logical_file.frames:
        names = [ch.name for ch in frame.channels]
        if channel_name in names:
            return frame
    return None

with dlisio.dlis.load('well.dlis') as (f, *_):
    frame = find_frame_with_channel(f, 'GR')
    if frame:
        print(f"GR in frame: {frame.name}")
```

### Find Frame by Index Type
```python
def find_frame_by_index(logical_file, index_type):
    """Find frames with specific index type."""
    matching = []
    for frame in logical_file.frames:
        if frame.index_type and index_type.lower() in frame.index_type.lower():
            matching.append(frame)
    return matching

with dlisio.dlis.load('well.dlis') as (f, *_):
    depth_frames = find_frame_by_index(f, 'DEPTH')
    time_frames = find_frame_by_index(f, 'TIME')
```

### Find Largest Frame
```python
def find_largest_frame(logical_file):
    """Find frame with most channels."""
    return max(logical_file.frames, key=lambda fr: len(fr.channels))

with dlisio.dlis.load('well.dlis') as (f, *_):
    main_frame = find_largest_frame(f)
    print(f"Largest frame: {main_frame.name} ({len(main_frame.channels)} channels)")
```

## Performance Tips

### Avoid Reading Data Multiple Times
```python
# Bad: reads curves on every access
with dlisio.dlis.load('well.dlis') as (f, *_):
    frame = f.frames[0]
    for i in range(100):
        data = frame.curves()  # Reads from disk each time!

# Good: read once, reuse
with dlisio.dlis.load('well.dlis') as (f, *_):
    frame = f.frames[0]
    curves = frame.curves()  # Read once
    for i in range(100):
        # Use cached curves
        pass
```

### Process Multiple Files
```python
from pathlib import Path
from concurrent.futures import ProcessPoolExecutor

def process_dlis(path):
    """Process a single DLIS file."""
    try:
        with dlisio.dlis.load(str(path)) as (f, *_):
            frame = f.frames[0]
            curves = frame.curves()
            return path.name, len(curves)
    except Exception as e:
        return path.name, str(e)

# Parallel processing
paths = list(Path('data/').glob('*.dlis'))
with ProcessPoolExecutor(max_workers=4) as executor:
    results = list(executor.map(process_dlis, paths))
```

### Memory Management
```python
import gc

# For large files
for dlis_path in dlis_files:
    with dlisio.dlis.load(dlis_path) as files:
        for f in files:
            # Process each logical file
            for frame in f.frames:
                curves = frame.curves()
                # Process...
                del curves
            gc.collect()
```

### Extract Only Needed Data
```python
with dlisio.dlis.load('well.dlis') as (f, *_):
    frame = f.frames[0]

    # Read full curves
    curves = frame.curves()

    # Extract only what you need immediately
    depth = curves['DEPTH'].copy()
    gr = curves['GR'].copy()

    # Clear the full dataset
    del curves
```
