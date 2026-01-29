# FDSN Data Centers Reference

## Table of Contents
- [Overview](#overview)
- [Major Data Centers](#major-data-centers)
- [Regional Data Centers](#regional-data-centers)
- [Connecting to Data Centers](#connecting-to-data-centers)
- [Service Capabilities](#service-capabilities)
- [Data Access Tips](#data-access-tips)

## Overview

FDSN (International Federation of Digital Seismograph Networks) web services provide standardized access to seismic data worldwide. ObsPy's `Client` class connects to these services.

```python
from obspy.clients.fdsn import Client

# List all available data centers
from obspy.clients.fdsn.header import URL_MAPPINGS
print(list(URL_MAPPINGS.keys()))
```

## Major Data Centers

| Code | Name | Region | URL |
|------|------|--------|-----|
| IRIS | IRIS DMC | Global | service.iris.edu |
| USGS | USGS Earthquake Hazards | USA/Global | earthquake.usgs.gov |
| GEOFON | GFZ Potsdam | Europe/Global | geofon.gfz-potsdam.de |
| ORFEUS | ORFEUS Data Center | Europe | orfeus-eu.org |
| ISC | International Seismological Centre | Global | isc-mirror.iris.edu |

### IRIS (Incorporated Research Institutions for Seismology)
- Largest archive of seismic data
- Global coverage with emphasis on research networks
- Waveforms, events, and stations

```python
client = Client("IRIS")
```

### USGS (United States Geological Survey)
- Best for earthquake catalogs (especially US events)
- Real-time earthquake monitoring
- ShakeMap and other hazard products

```python
client = Client("USGS")
```

### GEOFON (GeoForschungsNetz)
- GFZ Potsdam, Germany
- Strong European and global coverage
- Real-time data access

```python
client = Client("GEOFON")
# or
client = Client("GFZ")
```

## Regional Data Centers

### North America

| Code | Name | Coverage |
|------|------|----------|
| NCEDC | Northern California Earthquake Data Center | California |
| SCEDC | Southern California Earthquake Data Center | California |
| TEXNET | TexNet Seismic Network | Texas |

### Europe

| Code | Name | Coverage |
|------|------|----------|
| ETH | Swiss Seismological Service | Switzerland |
| INGV | Istituto Nazionale di Geofisica | Italy |
| RESIF | French Seismological Network | France |
| BGR | Federal Institute for Geosciences | Germany |
| KOERI | Kandilli Observatory | Turkey |
| NOA | National Observatory of Athens | Greece |
| LMU | Ludwig Maximilian University | Germany |

### Asia-Pacific

| Code | Name | Coverage |
|------|------|----------|
| NIED | National Research Institute for Earth Science | Japan |
| GEONET | GeoNet New Zealand | New Zealand |
| AUSPASS | AusPASS | Australia |

## Connecting to Data Centers

### Basic Connection
```python
from obspy.clients.fdsn import Client

# By code
client = Client("IRIS")

# By URL (custom or internal servers)
client = Client("http://myserver.org:8080")
```

### With Authentication (Restricted Data)
```python
# Using credentials
client = Client("IRIS", user="username", password="password")

# Using EIDA token
client = Client("RESIF", eida_token="path/to/token.txt")
```

### Connection Timeout
```python
# Increase timeout for slow connections
client = Client("IRIS", timeout=120)
```

## Service Capabilities

Not all data centers provide all services:

| Service | Description | Common Endpoints |
|---------|-------------|------------------|
| dataselect | Waveform data | IRIS, GEOFON, all |
| station | Station metadata | IRIS, GEOFON, all |
| event | Earthquake catalogs | USGS, IRIS, GEOFON |

### Check Available Services
```python
from obspy.clients.fdsn import Client

client = Client("IRIS")
print(client.services)  # Available services
```

### Service-Specific Usage

#### Waveforms (dataselect)
```python
st = client.get_waveforms("IU", "ANMO", "00", "BHZ", t1, t2)
```

#### Stations (station)
```python
inv = client.get_stations(network="IU", station="ANMO", level="response")
```

#### Events (event)
```python
cat = client.get_events(starttime=t1, endtime=t2, minmagnitude=5.0)
```

## Data Access Tips

### Finding Available Data

```python
# Search for stations
inv = client.get_stations(
    network="*",
    station="*",
    starttime=UTCDateTime("2023-01-01"),
    endtime=UTCDateTime("2023-12-31"),
    minlatitude=30, maxlatitude=50,
    minlongitude=-120, maxlongitude=-100,
    level="station"
)
```

### Bulk Requests
```python
# Download multiple station/time combinations efficiently
bulk = [
    ("IU", "ANMO", "00", "BHZ", t1, t2),
    ("IU", "CCM", "00", "BHZ", t1, t2),
    ("IU", "HRV", "00", "BHZ", t1, t2),
]
st = client.get_waveforms_bulk(bulk)
```

### Data Availability
```python
# Check what's available before downloading
from obspy.clients.fdsn import RoutingClient

# Federated search across multiple data centers
client = RoutingClient("eida-routing")
```

### Rate Limiting
- Most services have request limits
- Use bulk requests for efficiency
- Cache data locally when possible
- Be respectful during emergencies (high server load)

### Federated Access (EIDA)
```python
# Route requests to appropriate European data centers
from obspy.clients.fdsn import RoutingClient

client = RoutingClient("eida-routing")
st = client.get_waveforms(network="*", station="*",
                          location="*", channel="BHZ",
                          starttime=t1, endtime=t2)
```
