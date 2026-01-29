# LAS File Troubleshooting Guide

## Table of Contents
- [Reading Errors](#reading-errors)
- [Data Quality Issues](#data-quality-issues)
- [Writing Issues](#writing-issues)
- [Performance](#performance)

## Reading Errors

### Encoding Issues

**Problem**: `UnicodeDecodeError` when reading file

```python
# Solution 1: Specify encoding
las = lasio.read("well.las", encoding='latin-1')

# Solution 2: Try common encodings
for enc in ['utf-8', 'latin-1', 'cp1252', 'ascii']:
    try:
        las = lasio.read("well.las", encoding=enc)
        break
    except UnicodeDecodeError:
        continue
```

### Header Parsing Errors

**Problem**: `LASHeaderError` from malformed headers

```python
# Ignore header errors and parse what's possible
las = lasio.read("well.las", ignore_header_errors=True)

# Check what was parsed
print(las.well)    # May have missing fields
print(las.curves)  # Should still have curve data
```

### Missing Data Section

**Problem**: File has headers but no data

```python
las = lasio.read("well.las")
if las.data.size == 0:
    print("No data in file")
    print("Available headers:", las.well.keys())
```

### Inconsistent Column Count

**Problem**: Data rows have varying column counts

```python
# lasio handles this automatically, but check:
las = lasio.read("well.las")
expected_cols = len(las.curves)
actual_cols = las.data.shape[1]
if expected_cols != actual_cols:
    print(f"Mismatch: {expected_cols} curves, {actual_cols} data columns")
```

## Data Quality Issues

### Null Values Not Recognized

**Problem**: Null values appearing as numbers

```python
import numpy as np

# Check the null value defined in file
null_val = float(las.well['NULL'].value)
print(f"Null value: {null_val}")

# Replace with NaN
df = las.df()
df = df.replace(null_val, np.nan)

# Or replace during access
data = las['GR']
data = np.where(data == null_val, np.nan, data)
```

### Wrong Depth Units

**Problem**: Depth appears in wrong units

```python
# Check depth unit
depth_unit = las.curves['DEPT'].unit
print(f"Depth unit: {depth_unit}")

# Convert if needed
if depth_unit.upper() == 'FT':
    depth_m = las['DEPT'] * 0.3048
```

### Duplicate Curve Names

**Problem**: Multiple curves with same mnemonic

```python
# Check for duplicates
from collections import Counter
names = [c.mnemonic for c in las.curves]
dups = [k for k, v in Counter(names).items() if v > 1]
if dups:
    print(f"Duplicate curves: {dups}")

# Access by index instead
curve_data = las.curves[0].data  # First curve
```

### Depth Not Monotonic

**Problem**: Depth values not strictly increasing/decreasing

```python
import numpy as np

depth = las['DEPT']
if not (np.all(np.diff(depth) > 0) or np.all(np.diff(depth) < 0)):
    print("Warning: Depth not monotonic")

    # Find problem indices
    diff = np.diff(depth)
    problems = np.where(diff <= 0)[0] if diff[0] > 0 else np.where(diff >= 0)[0]
    print(f"Issues at indices: {problems}")
```

## Writing Issues

### Preserve Original Formatting

**python
# Read with original formatting
las = lasio.read("original.las")

# Make modifications
las['GR'] = las['GR'] * 2

# Write with same version
las.write('output.las', version=las.version['VERS'].value)
```

### Control Output Precision

```python
# Set data precision (decimal places)
las.write('output.las', fmt='%.4f')

# Different precision per column
# Not directly supported - format data before writing
las['GR'] = np.round(las['GR'], 2)
```

### Missing Required Headers

```python
# Ensure minimum required headers exist
required = ['WELL', 'STRT', 'STOP', 'STEP', 'NULL']
for field in required:
    if field not in las.well:
        las.well[field] = lasio.HeaderItem(field, value='')
```

## Performance

### Large File Handling

```python
# For very large files, process in chunks
import pandas as pd

# Read only specific curves
las = lasio.read("large.las")
needed = ['DEPT', 'GR', 'RHOB']
df = las.df()[needed]  # Only load needed columns

# Or use memory mapping (not directly supported)
# Consider converting to binary format for repeated access
```

### Batch Processing Optimization

```python
from pathlib import Path
from concurrent.futures import ProcessPoolExecutor

def process_file(path):
    try:
        las = lasio.read(path)
        return path.name, las.df().describe()
    except Exception as e:
        return path.name, str(e)

# Parallel processing
paths = list(Path('wells/').glob('*.las'))
with ProcessPoolExecutor(max_workers=4) as executor:
    results = list(executor.map(process_file, paths))
```

### Memory Issues

```python
# Clear data after processing
import gc

for path in paths:
    las = lasio.read(path)
    # Process...
    del las
    gc.collect()
```
