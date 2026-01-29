# EDI File Format Reference

## Table of Contents
- [Overview](#overview)
- [Header Section](#header-section)
- [Information Section](#information-section)
- [Define Measurement Section](#define-measurement-section)
- [Data Sections](#data-sections)
- [Impedance Data](#impedance-data)
- [Tipper Data](#tipper-data)

## Overview

EDI (Electrical Data Interchange) is the industry standard format for magnetotelluric data. Files are ASCII text with sections marked by `>` prefix.

```
>HEAD
>INFO
>=DEFINEMEAS
>=MTSECT
>FREQ
>ZROT
>ZXXR, >ZXXI, >ZXX.VAR
>ZXYR, >ZXYI, >ZXY.VAR
>ZYXR, >ZYXI, >ZYX.VAR
>ZYYR, >ZYYI, >ZYY.VAR
>TXR.EXP, >TXI.EXP (optional)
>TYR.EXP, >TYI.EXP (optional)
>END
```

## Header Section

Contains station identification and acquisition metadata.

```
>HEAD
  DATAID="STATION001"
  ACQBY="SURVEY COMPANY"
  FILEBY="PROCESSING CENTER"
  ACQDATE=2024-03-15
  FILEDATE=2024-04-01
  PROSPECT="EXPLORATION PROJECT"
  LOC="FIELD AREA"
  LAT=-25.5000
  LONG=135.2500
  ELEV=450.0
  UNITS=M
  STDVERS="SEG 1.0"
  PROGVERS="MTPY-V2"
  PROGDATE=2024
  EMPTY=1.0E+32
```

### Key Fields

| Field | Description |
|-------|-------------|
| DATAID | Station identifier |
| LAT, LONG | Geographic coordinates |
| ELEV | Elevation in specified units |
| UNITS | M (meters) or FT (feet) |
| EMPTY | Value representing null/missing data |

### Access in mtpy
```python
from mtpy import MT

mt = MT('station.edi')
print(mt.station)       # DATAID
print(mt.latitude)      # LAT
print(mt.longitude)     # LONG
print(mt.elevation)     # ELEV
```

## Information Section

Free-form text for processing notes.

```
>INFO
  MAXINFO=1000
  Processing notes and acquisition details
  Remote reference: STATION002
  Processing software: EMTF
```

## Define Measurement Section

Specifies channel configuration.

```
>=DEFINEMEAS
  MAXCHAN=5
  MAXRUN=1
  MAXMEAS=999
  UNITS=M
  REFTYPE=CART
  REFLAT=-25.5000
  REFLONG=135.2500
  REFELEV=450.0

>HMEAS ID=1001.001 CHTYPE=HX X=0.0 Y=0.0 Z=0.0 AZM=0.0
>HMEAS ID=1002.001 CHTYPE=HY X=0.0 Y=0.0 Z=0.0 AZM=90.0
>HMEAS ID=1003.001 CHTYPE=HZ X=0.0 Y=0.0 Z=0.0 AZM=0.0
>EMEAS ID=1004.001 CHTYPE=EX X=-50.0 Y=0.0 Z=0.0 X2=50.0 Y2=0.0
>EMEAS ID=1005.001 CHTYPE=EY X=0.0 Y=-50.0 Z=0.0 X2=0.0 Y2=50.0
```

### Channel Types

| Type | Description |
|------|-------------|
| HX | Magnetic field, north component |
| HY | Magnetic field, east component |
| HZ | Magnetic field, vertical component |
| EX | Electric field, north component |
| EY | Electric field, east component |

## Data Sections

### MT Section Header
```
>=MTSECT
  NFREQ=50
  HX=1001.001
  HY=1002.001
  HZ=1003.001
  EX=1004.001
  EY=1005.001
```

### Frequency Array
```
>FREQ NFREQ=50 ORDER=DEC // 50
  3.200000E+02  2.560000E+02  2.048000E+02  1.638400E+02
  1.310720E+02  1.048576E+02  8.388608E+01  6.710886E+01
  ...
```

- ORDER=DEC: Frequencies in decreasing order
- ORDER=INC: Frequencies in increasing order

### Access in mtpy
```python
freq = mt.frequency          # Frequency array (Hz)
period = 1 / mt.frequency    # Period array (s)
```

## Impedance Data

Impedance tensor stored as real, imaginary, and variance components.

```
>ZROT // 50
  0.000000E+00  0.000000E+00  0.000000E+00  ...

>ZXXR ROT=ZROT // 50
  1.234567E-02 -2.345678E-02  3.456789E-02  ...

>ZXXI ROT=ZROT // 50
  9.876543E-03 -8.765432E-03  7.654321E-03  ...

>ZXX.VAR ROT=ZROT // 50
  1.000000E-06  1.200000E-06  1.500000E-06  ...
```

### Impedance Components

| Section | Description | Units |
|---------|-------------|-------|
| ZXXR | Zxx real part | mV/km/nT |
| ZXXI | Zxx imaginary part | mV/km/nT |
| ZXX.VAR | Zxx variance | (mV/km/nT)^2 |
| ZXYR | Zxy real part | mV/km/nT |
| ZXYI | Zxy imaginary part | mV/km/nT |
| ZXY.VAR | Zxy variance | (mV/km/nT)^2 |
| ZYXR | Zyx real part | mV/km/nT |
| ZYXI | Zyx imaginary part | mV/km/nT |
| ZYX.VAR | Zyx variance | (mV/km/nT)^2 |
| ZYYR | Zyy real part | mV/km/nT |
| ZYYI | Zyy imaginary part | mV/km/nT |
| ZYY.VAR | Zyy variance | (mV/km/nT)^2 |

### Access in mtpy
```python
Z = mt.Z              # Complex impedance tensor [nfreq, 2, 2]
Z_err = mt.Z_err      # Impedance errors [nfreq, 2, 2]

# Individual components
Zxy = mt.Z[:, 0, 1]   # Complex Zxy
Zyx = mt.Z[:, 1, 0]   # Complex Zyx

# Derived quantities
rho_xy = mt.apparent_resistivity[:, 0, 1]  # Ohm-m
phase_xy = mt.phase[:, 0, 1]               # Degrees
```

## Tipper Data

Vertical magnetic field transfer function (optional).

```
>TXR.EXP ROT=ZROT // 50
  1.234567E-02  2.345678E-02  3.456789E-02  ...

>TXI.EXP ROT=ZROT // 50
  9.876543E-03  8.765432E-03  7.654321E-03  ...

>TXVAR.EXP ROT=ZROT // 50
  1.000000E-06  1.200000E-06  1.500000E-06  ...

>TYR.EXP ROT=ZROT // 50
  ...

>TYI.EXP ROT=ZROT // 50
  ...

>TYVAR.EXP ROT=ZROT // 50
  ...
```

### Tipper Components

| Section | Description |
|---------|-------------|
| TXR.EXP | Real part of Tx (Hz/Hx) |
| TXI.EXP | Imaginary part of Tx |
| TXVAR.EXP | Variance of Tx |
| TYR.EXP | Real part of Ty (Hz/Hy) |
| TYI.EXP | Imaginary part of Ty |
| TYVAR.EXP | Variance of Ty |

### Access in mtpy
```python
if mt.has_tipper:
    T = mt.Tipper           # Complex tipper [nfreq, 1, 2]
    T_err = mt.Tipper_err   # Tipper errors

    Tx = mt.Tipper[:, 0, 0]  # Hz/Hx component
    Ty = mt.Tipper[:, 0, 1]  # Hz/Hy component
```

## Data Quality Indicators

### Rotation Angle
```
>ZROT // 50
```
Rotation angle applied to impedance tensor. Zero means north-oriented.

### Coherence (optional)
Some EDI files include coherence estimates:
```
>COH // 50
  0.95  0.93  0.91  ...
```

## Creating EDI Files

```python
from mtpy import MT
import numpy as np

# Load and modify
mt = MT('input.edi')

# Change station name
mt.station = 'NEW_NAME'

# Apply rotation
mt_rotated = mt.rotate(45)

# Write new EDI
mt_rotated.write_edi('output.edi')
```

## Common Format Issues

| Issue | Description | Solution |
|-------|-------------|----------|
| Wrong EMPTY value | Missing data not flagged | Check EMPTY in >HEAD |
| Coordinate confusion | Lat/Long swapped | Verify geographic sense |
| Unit mismatch | SI vs CGS units | Check UNITS field |
| Missing sections | Incomplete file | Validate required sections |
