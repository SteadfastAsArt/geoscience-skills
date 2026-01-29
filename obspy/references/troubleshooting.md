# ObsPy Troubleshooting Guide

## Table of Contents
- [FDSN Data Access Issues](#fdsn-data-access-issues)
- [Data Processing Errors](#data-processing-errors)
- [File I/O Problems](#file-io-problems)
- [Performance Issues](#performance-issues)
- [Plotting Problems](#plotting-problems)

## FDSN Data Access Issues

### No Data Available

**Problem**: `FDSNNoDataException: No data available`

```python
from obspy.clients.fdsn.header import FDSNNoDataException

try:
    st = client.get_waveforms("IU", "ANMO", "00", "BHZ", t1, t2)
except FDSNNoDataException:
    print("No data for this request")
```

**Common causes and solutions**:
1. **Wrong time range**: Check earthquake time, station operational dates
2. **Wrong channel code**: Try wildcards: `channel="BH*"` or `channel="*Z"`
3. **Wrong location code**: Try `location="*"` or `location=""`
4. **Station not in network**: Verify with `get_stations()` first
5. **Data center doesn't have it**: Try different client (IRIS, GEOFON)

```python
# Check station availability first
inv = client.get_stations(
    network="IU", station="ANMO",
    starttime=t1, endtime=t2,
    level="channel"
)
print(inv)  # Shows available channels
```

### Connection Timeout

**Problem**: Request times out on slow connections

```python
# Increase timeout (default is 120s)
client = Client("IRIS", timeout=300)

# For bulk requests, consider:
# 1. Smaller time windows
# 2. Fewer stations per request
# 3. Lower sample rate channels (LH instead of BH)
```

### HTTP 413: Request Too Large

**Problem**: Requesting too much data at once

```python
# Split large requests into chunks
from obspy import UTCDateTime

t1 = UTCDateTime("2023-01-01")
t2 = UTCDateTime("2023-02-01")

# Instead of one month, request day by day
streams = []
current = t1
while current < t2:
    try:
        st = client.get_waveforms("IU", "ANMO", "00", "BHZ",
                                   current, current + 86400)
        streams.append(st)
    except Exception as e:
        print(f"Error for {current}: {e}")
    current += 86400

# Combine all
st = streams[0]
for s in streams[1:]:
    st += s
st.merge()
```

### Authentication Required

**Problem**: Accessing restricted/embargoed data

```python
# With username/password
client = Client("IRIS", user="username", password="password")

# With EIDA token (for European data)
client = Client("RESIF", eida_token="/path/to/token.txt")
```

## Data Processing Errors

### Filter Artifacts / Ringing

**Problem**: Edge effects after filtering

```python
# ALWAYS detrend and taper before filtering
st = read("data.mseed")

# Correct order:
st.detrend("demean")              # Remove mean
st.detrend("linear")              # Remove linear trend
st.taper(max_percentage=0.05)     # Taper edges (5% each side)
st.filter("bandpass", freqmin=1, freqmax=10)

# For stronger filtering, use larger taper
st.taper(max_percentage=0.1)      # 10% each side
```

### Instrument Response Removal Fails

**Problem**: Error when calling `remove_response()`

```python
# Common issues:
# 1. Missing response information
inv = client.get_stations(network="IU", station="ANMO",
                          level="response")  # Must use level="response"

# 2. Time mismatch - ensure inventory covers waveform time
st = client.get_waveforms("IU", "ANMO", "00", "BHZ", t1, t2)
inv = client.get_stations(network="IU", station="ANMO",
                          starttime=t1, endtime=t2,
                          level="response")

# 3. Pre-filter to avoid instability at band edges
st.remove_response(
    inventory=inv,
    output="VEL",
    pre_filt=[0.005, 0.01, 45, 50]  # Corners for pre-filtering
)
```

### Merge Errors with Gaps

**Problem**: Cannot merge traces with gaps/overlaps

```python
st = read("data.mseed")

# Check for gaps
st.print_gaps()

# Option 1: Fill gaps with interpolation
st.merge(method=1, fill_value="interpolate")

# Option 2: Fill gaps with zeros
st.merge(method=1, fill_value=0)

# Option 3: Split at gaps (keeps separate traces)
st = st.split()

# Option 4: Only merge overlaps, keep gaps
st.merge(method=0)  # No fill
```

### Incompatible Sampling Rates

**Problem**: Merging streams with different sample rates

```python
# Resample to common rate before merging
target_rate = 20.0

for tr in st:
    if tr.stats.sampling_rate != target_rate:
        tr.resample(target_rate)

st.merge()
```

## File I/O Problems

### Unknown Format

**Problem**: `Cannot determine file format`

```python
# Specify format explicitly
st = read("data.unknown", format="MSEED")
st = read("data.sac", format="SAC")

# Check supported formats
from obspy.core.stream import ENTRY_POINTS
print(ENTRY_POINTS['waveform'].keys())
```

### SAC Header Issues

**Problem**: Missing or incorrect SAC headers

```python
# Read SAC file
st = read("data.sac")
tr = st[0]

# Check SAC headers
print(tr.stats.sac)

# Set required headers
tr.stats.sac = tr.stats.get('sac', {})
tr.stats.sac['evla'] = 35.0    # Event latitude
tr.stats.sac['evlo'] = -120.0  # Event longitude
tr.stats.sac['evdp'] = 10.0    # Event depth (km)

# Write with headers
tr.write("output.sac", format="SAC")
```

### Encoding Issues in Station XML

**Problem**: Unicode errors in station metadata

```python
# Save inventory with ASCII encoding
inv.write("stations.xml", format="STATIONXML", encoding="ASCII")

# Or handle when reading
import codecs
with codecs.open("stations.xml", encoding="utf-8-sig") as f:
    inv = read_inventory(f)
```

## Performance Issues

### Memory Problems with Large Files

**Problem**: Out of memory with large datasets

```python
# Process in chunks instead of loading all
from pathlib import Path

for filepath in Path("data/").glob("*.mseed"):
    st = read(str(filepath))
    # Process...
    # Clear memory
    del st

# Or use headonly for inspection
st = read("large_file.mseed", headonly=True)  # Only headers
print(st)  # See structure without loading data
```

### Slow Plotting

**Problem**: Plotting large datasets is slow

```python
# Downsample for plotting
st_plot = st.copy()
for tr in st_plot:
    if tr.stats.npts > 100000:
        tr.decimate(factor=10)  # Reduce by 10x
st_plot.plot()

# Or use dayplot for long time series
st[0].plot(type="dayplot")
```

### Parallel Processing

**Problem**: Need to process many files faster

```python
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path

def process_file(filepath):
    try:
        st = read(str(filepath))
        st.detrend("demean")
        st.filter("bandpass", freqmin=1, freqmax=10)
        # ... more processing
        return filepath.name, "success"
    except Exception as e:
        return filepath.name, str(e)

files = list(Path("data/").glob("*.mseed"))
with ProcessPoolExecutor(max_workers=4) as executor:
    results = list(executor.map(process_file, files))
```

## Plotting Problems

### Backend Issues

**Problem**: Plot not showing or matplotlib errors

```python
import matplotlib
matplotlib.use('Agg')  # Use non-interactive backend for scripts

from obspy import read
st = read("data.mseed")
st.plot(outfile="plot.png")  # Save to file instead of display
```

### Custom Plot Formatting

**Problem**: Need more control over plot appearance

```python
import matplotlib.pyplot as plt
from obspy import read

st = read("data.mseed")
tr = st[0]

# Manual plotting for full control
fig, ax = plt.subplots(figsize=(12, 4))
times = tr.times("matplotlib")  # Get time in matplotlib format
ax.plot(times, tr.data, 'k-', linewidth=0.5)
ax.xaxis_date()
fig.autofmt_xdate()
ax.set_ylabel(f"{tr.stats.channel}")
ax.set_title(f"{tr.id}")
plt.tight_layout()
plt.savefig("custom_plot.png", dpi=150)
```

### Spectrogram Issues

**Problem**: Spectrogram looks wrong or has artifacts

```python
tr = st[0]

# Adjust spectrogram parameters
tr.spectrogram(
    log=True,                    # Log frequency scale
    cmap='viridis',              # Color map
    wlen=tr.stats.sampling_rate,  # Window length in samples
    per_lap=0.9,                 # Overlap (0-1)
    dbscale=True,                # dB scale for colors
    clip=[0.0, 1.0]              # Clip percentile
)
```
