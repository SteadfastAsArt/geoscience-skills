# LAS File Structure Reference

## Table of Contents
- [Overview](#overview)
- [Version Section](#version-section)
- [Well Section](#well-section)
- [Curve Section](#curve-section)
- [Parameter Section](#parameter-section)
- [Data Section](#data-section)
- [LAS 3.0 Extensions](#las-30-extensions)

## Overview

LAS (Log ASCII Standard) files consist of sections marked by `~` prefix:

```
~VERSION INFORMATION
~WELL INFORMATION
~CURVE INFORMATION
~PARAMETER INFORMATION (optional)
~OTHER (optional)
~ASCII LOG DATA
```

## Version Section

Identifies file format version.

```
~VERSION INFORMATION
VERS.                  2.0 : CWLS LOG ASCII STANDARD - VERSION 2.0
WRAP.                  NO  : One line per depth step
DLM .              SPACE   : Column delimiter (LAS 3.0)
```

| Mnemonic | Description |
|----------|-------------|
| VERS | LAS version (1.2, 2.0, or 3.0) |
| WRAP | YES = data wraps, NO = one line per sample |
| DLM | Delimiter (SPACE, TAB, COMMA) - LAS 3.0 only |

### Access in lasio
```python
las.version['VERS'].value  # 2.0
las.version['WRAP'].value  # 'NO'
```

## Well Section

Contains well identification and depth range.

```
~WELL INFORMATION
STRT.M              1500.0000 : Start depth
STOP.M              2500.0000 : Stop depth
STEP.M                 0.1524 : Step increment
NULL.               -999.2500 : Null value
COMP.       SHELL EXPLORATION : Company name
WELL.              WELL-A-001 : Well name
FLD .              NORTH FIELD : Field name
LOC .       12-34-56-78W5M    : Location
PROV.                 ALBERTA : Province
SRVC.            SCHLUMBERGER : Service company
DATE.              2024-01-15 : Log date
UWI .    12345678901234       : Unique well identifier
```

### Required Fields (LAS 2.0)
| Mnemonic | Description |
|----------|-------------|
| STRT | Start depth |
| STOP | Stop depth |
| STEP | Step (0 if irregular) |
| NULL | Null/absent value |
| COMP | Company |
| WELL | Well name |

### Access in lasio
```python
las.well['WELL'].value       # 'WELL-A-001'
las.well['STRT'].value       # 1500.0
las.well['STRT'].unit        # 'M'
las.well['UWI'].value        # '12345678901234'
```

## Curve Section

Defines each data column (curve).

```
~CURVE INFORMATION
DEPT.M                        : 1  Measured Depth
GR  .GAPI                     : 2  Gamma Ray
RHOB.G/CC                     : 3  Bulk Density
NPHI.V/V                      : 4  Neutron Porosity
ILD .OHMM                     : 5  Deep Induction
```

Format: `MNEM.UNIT   value : description`

### Access in lasio
```python
# List all curves
for curve in las.curves:
    print(f"{curve.mnemonic}: {curve.unit} - {curve.descr}")

# Get specific curve info
las.curves['GR'].mnemonic    # 'GR'
las.curves['GR'].unit        # 'GAPI'
las.curves['GR'].descr       # 'Gamma Ray'
las.curves['GR'].data        # numpy array
```

## Parameter Section

Optional section for additional parameters.

```
~PARAMETER INFORMATION
MUD .        GEL CHEM : Mud type
BHT .DEGC      85.000 : Bottom hole temperature
BS  .MM       215.900 : Bit size
RMF .OHMM       0.550 : Mud filtrate resistivity
DFD .KG/M3   1200.000 : Drilling fluid density
```

### Access in lasio
```python
las.params['BHT'].value      # 85.0
las.params['BHT'].unit       # 'DEGC'
```

## Data Section

Contains the actual log values.

```
~ASCII LOG DATA
 1500.0000   45.2134    2.4521    0.1823   12.4500
 1500.1524   46.8921    2.4498    0.1856   11.9800
 1500.3048   44.1256    2.4612    0.1801   13.2100
```

- First column is always depth (index)
- Columns match order in Curve section
- Null values replaced with NULL value from Well section

### Access in lasio
```python
# As 2D numpy array
las.data                     # Shape: (n_samples, n_curves)

# As pandas DataFrame
df = las.df()                # Depth as index
df = las.df().reset_index()  # Depth as column

# Single curve as array
las['GR']                    # numpy array
```

## LAS 3.0 Extensions

LAS 3.0 adds:
- Multiple data sections with headers
- Log parameters per section
- Definition sections
- More flexible formatting

```
~Log_Definition
DEPT.M                         : Depth
GR  .GAPI                      : Gamma Ray

~Log_Data | Log_Definition
 1500.0000   45.2134
 1500.1524   46.8921
```

### Check version
```python
if las.version['VERS'].value >= 3.0:
    # Handle LAS 3.0 specific features
    pass
```

## Line Format Details

### Header Line Format
```
MNEM.UNIT  VALUE : DESCRIPTION
|    |     |       |
|    |     |       +-- Free text description
|    |     +---------- Value (numeric or string)
|    +---------------- Unit of measurement
+---------------------- Mnemonic (max 4 chars in LAS 1.2)
```

### Data Line Format
- Columns separated by spaces (default) or specified delimiter
- Fixed width not required in LAS 2.0+
- Exponential notation allowed: `1.234E+02`
