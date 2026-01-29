# Curve Processing Methods

## Table of Contents
- [Despike](#despike)
- [Smooth](#smooth)
- [Normalize](#normalize)
- [Resample](#resample)
- [Clip](#clip)
- [Quality Checks](#quality-checks)
- [Combining Operations](#combining-operations)

## Despike

Remove outliers using a moving window and z-score threshold.

```python
from welly import Well

w = Well.from_las('well.las')
gr = w.data['GR']

# Default despiking
gr_clean = gr.despike()

# Custom parameters
gr_clean = gr.despike(
    window=5,     # Window size (samples)
    z=2,          # Z-score threshold (lower = more aggressive)
)

# Check result
import matplotlib.pyplot as plt
fig, ax = plt.subplots(figsize=(6, 10))
gr.plot(ax=ax, c='red', alpha=0.5, label='Original')
gr_clean.plot(ax=ax, c='blue', label='Despiked')
ax.legend()
```

### When to Use Despike
- Before statistical analysis
- Before curve fitting or correlation
- When data has obvious spikes from tool issues
- Before generating synthetics

## Smooth

Apply smoothing filter to reduce noise.

```python
gr = w.data['GR']

# Moving average smoothing
gr_smooth = gr.smooth(window=11)  # Window size in samples

# Different window sizes
gr_light = gr.smooth(window=5)   # Light smoothing
gr_heavy = gr.smooth(window=21)  # Heavy smoothing
```

### Smoothing Considerations
- Larger window = more smoothing but loss of detail
- Use odd window sizes for symmetric averaging
- Consider the sample rate (step) when choosing window
- Smoothing reduces noise but may blur formation boundaries

## Normalize

Scale curve values to a specified range.

```python
gr = w.data['GR']

# Normalize to 0-1 range (default)
gr_norm = gr.normalize()

# Normalize with min/max values
gr_norm = gr.normalize(vmin=0, vmax=150)  # Use fixed endpoints

# Check the range
print(f"Min: {gr_norm.values.min()}, Max: {gr_norm.values.max()}")
```

### Normalization Use Cases
- Cross-well comparison with different GR ranges
- Input preparation for machine learning
- Volume of shale calculation
- Data visualization with consistent scales

## Resample

Change the depth sampling interval.

```python
gr = w.data['GR']
print(f"Original step: {gr.step}")

# Resample to new step
gr_resampled = gr.resample(step=0.5)  # meters
print(f"New step: {gr_resampled.step}")

# Resample to match another curve
rhob = w.data['RHOB']
gr_matched = gr.resample(basis=rhob.basis)
```

### Resampling Notes
- Upsampling (finer step) uses interpolation
- Downsampling (coarser step) uses averaging
- Important for curve math operations (curves must share basis)
- Consider resampling all curves to common basis before analysis

## Clip

Extract data within a depth range.

```python
gr = w.data['GR']
print(f"Full range: {gr.start} - {gr.stop}")

# Clip to depth interval
gr_zone = gr.clip(top=1500, bottom=2000)
print(f"Clipped range: {gr_zone.start} - {gr_zone.stop}")

# Clip to formation interval
if 'TopFormationA' in w.tops and 'TopFormationB' in w.tops:
    gr_formation = gr.clip(
        top=w.tops['TopFormationA'],
        bottom=w.tops['TopFormationB']
    )
```

### Clipping Use Cases
- Zone-specific analysis
- Formation-based statistics
- Remove bad data at top/bottom of log
- Focus analysis on interval of interest

## Quality Checks

Assess curve data quality before processing.

```python
import numpy as np

gr = w.data['GR']

# Count null/invalid values
null_count = np.sum(np.isnan(gr.values))
null_pct = 100 * null_count / len(gr.values)
print(f"Null values: {null_count} ({null_pct:.1f}%)")

# Check for constant values
unique_count = len(np.unique(gr.values[~np.isnan(gr.values)]))
print(f"Unique values: {unique_count}")

# Check value range
valid = gr.values[~np.isnan(gr.values)]
print(f"Range: {valid.min():.1f} - {valid.max():.1f}")
print(f"Mean: {valid.mean():.1f}, Std: {valid.std():.1f}")

# Detect gaps (consecutive nulls)
is_null = np.isnan(gr.values)
diff = np.diff(is_null.astype(int))
gap_starts = np.where(diff == 1)[0]
gap_ends = np.where(diff == -1)[0]
if len(gap_starts) > 0:
    print(f"Found {len(gap_starts)} gaps in data")
```

## Combining Operations

Chain processing steps for complete workflow.

```python
from welly import Well

w = Well.from_las('well.las')
gr = w.data['GR']

# Full processing pipeline
gr_processed = (
    gr
    .clip(top=1000, bottom=3000)    # Limit to good data range
    .despike(window=5, z=2)          # Remove outliers
    .smooth(window=5)                # Light smoothing
    .resample(step=0.5)              # Regular sampling
    .normalize()                     # Scale to 0-1
)

# Store processed curve back in well
w.data['GR_PROC'] = gr_processed
```

### Recommended Processing Order
1. **Clip** - Remove bad intervals first
2. **Despike** - Remove outliers
3. **Smooth** - Reduce noise (optional)
4. **Resample** - Standardize sampling
5. **Normalize** - Scale values (if needed)

## Working with Multiple Curves

Apply consistent processing across curves.

```python
from welly import Well, Project

w = Well.from_las('well.las')

# Process multiple curves the same way
curves_to_process = ['GR', 'NPHI', 'RHOB']
step = 0.5

for name in curves_to_process:
    if name in w.data:
        curve = w.data[name]
        processed = (
            curve
            .despike(window=5, z=2)
            .resample(step=step)
        )
        w.data[f'{name}_PROC'] = processed

# Verify all processed curves have same basis
bases = [w.data[f'{n}_PROC'].basis for n in curves_to_process if f'{n}_PROC' in w.data]
print(f"All bases equal: {all(np.array_equal(bases[0], b) for b in bases)}")
```
