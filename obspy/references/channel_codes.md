# Seismic Channel Naming Convention

## Table of Contents
- [Overview](#overview)
- [Band Code](#band-code)
- [Instrument Code](#instrument-code)
- [Orientation Code](#orientation-code)
- [Common Channel Combinations](#common-channel-combinations)
- [Location Codes](#location-codes)
- [SEED Identifier Format](#seed-identifier-format)

## Overview

Seismic channel names follow the SEED (Standard for the Exchange of Earthquake Data) convention. A channel code is 3 characters: **Band** + **Instrument** + **Orientation**.

```
Channel: BHZ
         |||
         ||+-- Orientation: Z (vertical)
         |+--- Instrument: H (high-gain seismometer)
         +---- Band: B (broadband, 10-80 sps)
```

## Band Code

The first character indicates sample rate and response period:

| Code | Sample Rate | Period Range | Typical Use |
|------|-------------|--------------|-------------|
| F | >= 1000 sps | > 10 Hz | Short period acoustic |
| G | >= 1000 sps | < 10 Hz | Short period |
| D | 250-1000 sps | < 10 Hz | Short period |
| C | 250-1000 sps | > 10 Hz | Short period acoustic |
| E | 80-250 sps | < 10 Hz | Extremely short period |
| S | 10-80 sps | < 10 Hz | Short period |
| H | 80-250 sps | < 10 Hz | High broadband |
| B | 10-80 sps | > 10 Hz | Broadband |
| M | 1-10 sps | > 10 Hz | Mid period |
| L | ~1 sps | > 10 Hz | Long period |
| V | ~0.1 sps | > 10 Hz | Very long period |
| U | ~0.01 sps | > 10 Hz | Ultra long period |
| R | 0.001-0.0001 sps | - | Extremely long period |

### Common Choices by Application

| Application | Typical Band | Sample Rate |
|-------------|--------------|-------------|
| Teleseismic earthquakes | BH, LH | 20-40 sps, 1 sps |
| Regional earthquakes | BH, HH | 40-100 sps |
| Local earthquakes | HH, SH | 100 sps |
| Strong motion | HN, BN | 100-200 sps |
| Infrasound | BD | 40 sps |
| Strain/tilt | BS, BK | 20-40 sps |

## Instrument Code

The second character indicates sensor type:

| Code | Instrument Type |
|------|-----------------|
| H | High gain seismometer |
| L | Low gain seismometer |
| G | Gravimeter |
| M | Mass position seismometer |
| N | Accelerometer |
| A | Tiltmeter |
| B | Strain meter |
| D | Barometer/pressure |
| F | Magnetometer |
| I | Humidity |
| K | Temperature |
| O | Water current |
| P | Geophone (short period) |
| R | Rotational sensor |
| S | Strain meter |
| T | Tide gauge |
| U | Bolometer |
| V | Volumetric strain |
| W | Wind |
| Z | Synthesized beam |

### Most Common

| Code | Use |
|------|-----|
| H | Standard broadband seismometer |
| N | Strong motion / accelerometer |
| L | Weak motion / low gain |
| P | Short period geophone |
| D | Infrasound / pressure |

## Orientation Code

The third character indicates component orientation:

### Standard Geographic
| Code | Direction |
|------|-----------|
| Z | Vertical (up positive) |
| N | North-South (north positive) |
| E | East-West (east positive) |

### Non-Standard Geographic
| Code | Direction |
|------|-----------|
| 1 | Orthogonal horizontal 1 (often ~N) |
| 2 | Orthogonal horizontal 2 (often ~E) |
| 3 | Vertical (when not ZNE) |

### Special Orientations
| Code | Description |
|------|-------------|
| H | Horizontal (unspecified) |
| R | Radial (toward event) |
| T | Transverse (perpendicular to event) |
| A, B, C | Triaxial, non-standard |
| U, V, W | Optional orthogonal |

## Common Channel Combinations

### Broadband Seismometers
| Channels | Description | Sample Rate |
|----------|-------------|-------------|
| BHZ, BHN, BHE | Broadband high gain | 20-40 sps |
| HHZ, HHN, HHE | High broadband | 100 sps |
| LHZ, LHN, LHE | Long period | 1 sps |

### Accelerometers (Strong Motion)
| Channels | Description | Sample Rate |
|----------|-------------|-------------|
| HNZ, HNN, HNE | Strong motion | 100-200 sps |
| BNZ, BNN, BNE | Strong motion | 20-40 sps |

### Short Period
| Channels | Description | Sample Rate |
|----------|-------------|-------------|
| SHZ, SHN, SHE | Short period | 50-100 sps |
| EHZ, EHN, EHE | Extremely short period | 100+ sps |

## Location Codes

Location codes (2 characters) distinguish multiple instruments at the same station:

| Code | Typical Use |
|------|-------------|
| 00 | Primary instrument |
| 10 | Secondary instrument |
| 01-09 | Instrument variations |
| EP | Strong motion (episensor) |
| SP | Short period |

```python
# Fetch specific location
st = client.get_waveforms("IU", "ANMO", "00", "BHZ", t1, t2)  # Primary
st = client.get_waveforms("IU", "ANMO", "10", "BHZ", t1, t2)  # Secondary
st = client.get_waveforms("IU", "ANMO", "*", "BHZ", t1, t2)   # All locations
```

## SEED Identifier Format

Full SEED identifier: `Network.Station.Location.Channel`

```
IU.ANMO.00.BHZ
|| |||| || |||
|| |||| || ||+-- Orientation (vertical)
|| |||| || |+--- Instrument (high gain)
|| |||| || +---- Band (broadband)
|| |||| |+------ Location (primary)
|| |||| +------- Location code separator
|| ++++--------- Station code (max 5 chars)
|+-------------- Network code separator
++-------------- Network code (2 chars)
```

### Working with SEED IDs in ObsPy
```python
tr = st[0]
print(tr.id)                    # "IU.ANMO.00.BHZ"
print(tr.stats.network)         # "IU"
print(tr.stats.station)         # "ANMO"
print(tr.stats.location)        # "00"
print(tr.stats.channel)         # "BHZ"

# Select by SEED pattern
st.select(id="IU.*.*.BHZ")      # All IU BHZ channels
```

## Channel Selection Examples

```python
from obspy.clients.fdsn import Client
from obspy import UTCDateTime

client = Client("IRIS")
t1 = UTCDateTime("2023-01-01")
t2 = t1 + 3600

# All broadband at a station
st = client.get_waveforms("IU", "ANMO", "*", "BH*", t1, t2)

# All vertical channels
st = client.get_waveforms("IU", "ANMO", "*", "*Z", t1, t2)

# Specific channel types
st = client.get_waveforms("IU", "ANMO", "00", "LH?", t1, t2)  # Long period 3-comp
st = client.get_waveforms("IU", "ANMO", "00", "HN?", t1, t2)  # Strong motion 3-comp
```
