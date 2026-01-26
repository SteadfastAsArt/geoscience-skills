---
name: lasio
description: Read and write LAS (Log ASCII Standard) well log files. Handles LAS 1.2 and 2.0 formats for borehole geophysical, geological, and petrophysical data.
---

# lasio - LAS File Handler

Help users read, write, and manipulate LAS (Log ASCII Standard) well log files.

## Installation

```bash
pip install lasio
```

## Core Concepts

### LAS File Structure
- **Version section** - LAS format version info
- **Well section** - Well metadata (name, location, dates)
- **Curves section** - Log curve definitions (mnemonics, units)
- **Parameters section** - Additional parameters
- **Data section** - Actual log values

### Key Classes
| Class | Purpose |
|-------|---------|
| `LASFile` | Main container for LAS data |
| `CurveItem` | Single curve with data and metadata |
| `HeaderItem` | Header entry (mnemonic, unit, value, description) |

## Common Workflows

### 1. Read a LAS File
```python
import lasio

# From file path
las = lasio.read("well.las")

# From URL
las = lasio.read("https://example.com/well.las")

# Print summary
print(las)
```

### 2. Access Well Information
```python
# Well section headers
print(las.well)

# Specific well info
print(las.well['WELL'].value)  # Well name
print(las.well['UWI'].value)   # Unique well identifier
print(las.well['STRT'].value)  # Start depth
print(las.well['STOP'].value)  # Stop depth
print(las.well['STEP'].value)  # Depth step
```

### 3. Access Curve Data
```python
# List available curves
print(las.curves)

# Get curve by mnemonic
gr = las['GR']        # Returns numpy array
depth = las['DEPT']

# Curve metadata
curve = las.curves['GR']
print(curve.mnemonic)     # 'GR'
print(curve.unit)         # 'GAPI'
print(curve.descr)        # 'Gamma Ray'
print(curve.data)         # numpy array
```

### 4. Export to Pandas DataFrame
```python
import pandas as pd

# Convert to DataFrame
df = las.df()

# With depth as column (not index)
df = las.df().reset_index()

# Access specific curves
print(df[['DEPT', 'GR', 'NPHI', 'RHOB']])
```

### 5. Create a New LAS File
```python
import lasio
import numpy as np

# Create empty LAS
las = lasio.LASFile()

# Add well info
las.well['WELL'] = lasio.HeaderItem('WELL', value='Test Well')
las.well['COMP'] = lasio.HeaderItem('COMP', value='Oil Corp')
las.well['UWI'] = lasio.HeaderItem('UWI', value='12345678901234')

# Add curves
depth = np.arange(1000, 2000, 0.5)
gr = np.random.uniform(20, 150, len(depth))

las.append_curve('DEPT', depth, unit='M', descr='Depth')
las.append_curve('GR', gr, unit='GAPI', descr='Gamma Ray')

# Write to file
las.write('output.las')
```

### 6. Modify Existing LAS
```python
las = lasio.read("well.las")

# Add new curve
new_curve = las['GR'] * 0.5
las.append_curve('GR_NORM', new_curve, unit='GAPI', descr='Normalized GR')

# Delete curve
del las.curves['BAD_CURVE']

# Update header
las.well['WELL'].value = 'Updated Well Name'

# Save
las.write('modified.las')
```

### 7. Handle Multiple LAS Files
```python
import lasio
from pathlib import Path

# Load all LAS files in directory
las_files = {}
for path in Path('wells/').glob('*.las'):
    las_files[path.stem] = lasio.read(path)

# Combine curves from multiple files
for name, las in las_files.items():
    print(f"{name}: {list(las.curves.keys())}")
```

### 8. Handle Problematic Files
```python
# lasio handles many real-world file issues automatically
las = lasio.read("messy.las", ignore_header_errors=True)

# Check for issues
if las.version['VERS'].value < 2.0:
    print("LAS 1.2 format detected")

# Handle null values
null_value = las.well['NULL'].value
print(f"Null value: {null_value}")
```

### 9. Export to Excel
```python
las = lasio.read("well.las")

# Export to Excel
df = las.df()
df.to_excel('well_data.xlsx')
```

### 10. Access Raw Data Array
```python
# Get all data as 2D numpy array
data = las.data  # Shape: (n_samples, n_curves)

# Get curve index
idx = las.curves.keys().index('GR')
gr_data = data[:, idx]
```

## Common Curve Mnemonics

| Mnemonic | Description | Typical Unit |
|----------|-------------|--------------|
| DEPT | Depth | M or FT |
| GR | Gamma Ray | GAPI |
| NPHI | Neutron Porosity | V/V or % |
| RHOB | Bulk Density | G/CC |
| DT | Sonic Transit Time | US/F |
| RT/ILD | Resistivity | OHMM |
| SP | Spontaneous Potential | MV |
| CALI | Caliper | IN |
| PEF | Photoelectric Factor | B/E |

## Tips

1. **Always check units** - LAS files may use different unit systems
2. **Handle nulls** - Check `las.well['NULL'].value` for null representation
3. **Validate curves** - Some files have missing or corrupt data
4. **Use pandas** - `las.df()` is the easiest way to work with data
5. **Preserve metadata** - When modifying, keep original headers intact

## Error Handling

```python
try:
    las = lasio.read("file.las")
except lasio.LASHeaderError as e:
    print(f"Header error: {e}")
except lasio.LASDataError as e:
    print(f"Data error: {e}")
except FileNotFoundError:
    print("File not found")
```

## Resources

- Documentation: https://lasio.readthedocs.io/
- GitHub: https://github.com/kinverarity1/lasio
- LAS Specification: https://www.cwls.org/products/
