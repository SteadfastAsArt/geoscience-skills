---
name: obspy
description: Seismology data processing with ObsPy. Helps with reading seismic data, filtering waveforms, fetching data from FDSN services, plotting seismograms, and earthquake analysis.
---

# ObsPy Seismology Assistant

Help users work with seismic data using the ObsPy Python library.

## Prerequisites

Ensure ObsPy is installed:
```bash
pip install obspy
```

## Core Concepts

### Key Classes
| Class | Purpose |
|-------|---------|
| `Stream` | Container for multiple Trace objects (waveforms) |
| `Trace` | Single continuous time series with metadata |
| `UTCDateTime` | Precise time handling for seismology |
| `Inventory` | Station/channel metadata |
| `Catalog` | Earthquake event information |

### Trace Attributes
- `trace.data` - NumPy array of waveform samples
- `trace.stats` - Metadata: station, channel, network, location, sampling_rate, starttime, endtime, npts

## Common Workflows

### 1. Read and Plot Local Data
```python
from obspy import read

# Read any supported format (MiniSEED, SAC, GSE2, etc.)
st = read("data.mseed")
print(st)  # Summary of traces

# Access individual traces
tr = st[0]
print(tr.stats)

# Plot waveforms
st.plot()
```

### 2. Filter and Process
```python
from obspy import read

st = read("data.mseed")

# Remove instrument trend
st.detrend("demean")
st.detrend("linear")

# Apply taper to avoid edge effects
st.taper(max_percentage=0.05)

# Filter options
st.filter("bandpass", freqmin=0.1, freqmax=10.0)  # Bandpass
st.filter("highpass", freq=1.0)                    # Highpass
st.filter("lowpass", freq=5.0)                     # Lowpass

st.plot()
```

### 3. Fetch Data from FDSN Services
```python
from obspy.clients.fdsn import Client
from obspy import UTCDateTime

# Available clients: IRIS, USGS, GEOFON, GFZ, ETH, ORFEUS, etc.
client = Client("IRIS")

# Define time window
t1 = UTCDateTime("2023-02-06T01:17:00")  # Turkey earthquake
t2 = t1 + 3600  # 1 hour of data

# Fetch waveforms: network, station, location, channel, start, end
st = client.get_waveforms("IU", "ANMO", "00", "LHZ", t1, t2)
st.plot()

# Save locally
st.write("earthquake.mseed", format="MSEED")
```

### 4. Search for Earthquakes
```python
from obspy.clients.fdsn import Client
from obspy import UTCDateTime

client = Client("USGS")

# Search for events
cat = client.get_events(
    starttime=UTCDateTime("2023-01-01"),
    endtime=UTCDateTime("2023-12-31"),
    minmagnitude=7.0,
    orderby="magnitude"
)

print(cat)  # List of events
cat.plot()  # Map view

# Access event details
event = cat[0]
origin = event.origins[0]
magnitude = event.magnitudes[0]
print(f"M{magnitude.mag} at {origin.latitude}, {origin.longitude}")
```

### 5. Get Station Information
```python
from obspy.clients.fdsn import Client

client = Client("IRIS")

# Get station metadata
inv = client.get_stations(
    network="IU",
    station="ANMO",
    level="response"  # Include instrument response
)

print(inv)
inv.plot()  # Map of stations

# Get response for instrument correction
inv.plot_response(min_freq=0.001)
```

### 6. Remove Instrument Response
```python
from obspy.clients.fdsn import Client
from obspy import UTCDateTime

client = Client("IRIS")
t = UTCDateTime("2023-02-06T01:17:00")

# Get waveforms and inventory
st = client.get_waveforms("IU", "ANMO", "00", "LHZ", t, t + 3600)
inv = client.get_stations(network="IU", station="ANMO", level="response")

# Remove response - convert to ground motion
st.remove_response(inventory=inv, output="VEL")  # VEL, DISP, or ACC
st.plot()
```

### 7. Spectrogram Analysis
```python
from obspy import read

st = read("data.mseed")
tr = st[0]

# Generate spectrogram
tr.spectrogram(log=True, title="Spectrogram")
```

### 8. Trim and Select Data
```python
from obspy import read, UTCDateTime

st = read("data.mseed")

# Trim to time window
t1 = UTCDateTime("2023-02-06T01:17:00")
t2 = UTCDateTime("2023-02-06T01:30:00")
st.trim(t1, t2)

# Select specific traces
st_z = st.select(channel="*Z")  # Only vertical components
st_bh = st.select(channel="BH*")  # Only BH channels
st_station = st.select(station="ANMO")  # Specific station
```

### 9. Write Data to Files
```python
from obspy import read

st = read("data.mseed")

# Supported formats: MSEED, SAC, GSE2, SEGY, SU, WAV, etc.
st.write("output.mseed", format="MSEED")
st.write("output.sac", format="SAC")

# Write each trace separately
for tr in st:
    tr.write(f"{tr.id}.mseed", format="MSEED")
```

### 10. Merge and Handle Gaps
```python
from obspy import read

st = read("data.mseed")

# Check for gaps
gaps = st.get_gaps()
st.print_gaps()

# Merge overlapping traces
st.merge(method=1, fill_value="interpolate")

# Or split at gaps
st = st.split()
```

## FDSN Data Centers

| Code | Name | Region |
|------|------|--------|
| IRIS | IRIS DMC | Global |
| USGS | USGS Earthquake Hazards | USA |
| GEOFON | GFZ Potsdam | Europe |
| ORFEUS | ORFEUS Data Center | Europe |
| ETH | Swiss Seismological Service | Switzerland |
| INGV | INGV Rome | Italy |
| NCEDC | Northern California | California |
| SCEDC | Southern California | California |

## Channel Naming Convention

Format: `Band` `Instrument` `Orientation`

**Band codes:**
- `L` - Long period (1 sps)
- `B` - Broadband (10-80 sps)
- `H` - High broadband (80-250 sps)
- `S` - Short period (10-80 sps)
- `E` - Extremely short period (>80 sps)

**Instrument codes:**
- `H` - High gain seismometer
- `L` - Low gain seismometer
- `N` - Accelerometer

**Orientation:**
- `Z` - Vertical
- `N/E` - North/East horizontal
- `1/2` - Horizontal (non-traditional)

Example: `BHZ` = Broadband, High-gain seismometer, Vertical

## Tips

1. **Always detrend and taper before filtering** to avoid artifacts
2. **Use `level="response"`** when fetching stations if you need to remove instrument response
3. **Check for gaps** before processing with `st.print_gaps()`
4. **Use wildcards** in station queries: `station="A*"`, `channel="BH?"`
5. **UTCDateTime** accepts many formats: ISO strings, timestamps, datetime objects

## Error Handling

```python
from obspy.clients.fdsn.header import FDSNNoDataException

try:
    st = client.get_waveforms("IU", "ANMO", "00", "LHZ", t1, t2)
except FDSNNoDataException:
    print("No data available for this time/station")
```

## Resources

- Documentation: https://docs.obspy.org/
- Tutorial: https://docs.obspy.org/tutorial/
- GitHub: https://github.com/obspy/obspy
- Supported formats: https://docs.obspy.org/packages/autogen/obspy.core.stream.read.html
