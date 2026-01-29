# GPR Processing Workflow Reference

## Table of Contents
- [Overview](#overview)
- [Step 1: Data Loading](#step-1-data-loading)
- [Step 2: Dewow Filter](#step-2-dewow-filter)
- [Step 3: Background Removal](#step-3-background-removal)
- [Step 4: Gain Application](#step-4-gain-application)
- [Step 5: Frequency Filtering](#step-5-frequency-filtering)
- [Step 6: Velocity Analysis](#step-6-velocity-analysis)
- [Step 7: Depth Conversion](#step-7-depth-conversion)
- [Step 8: Topographic Correction](#step-8-topographic-correction)
- [Step 9: Export](#step-9-export)
- [Processing Tips](#processing-tips)

## Overview

Standard GPR processing follows this sequence:
1. Load raw data
2. Remove DC bias and low-frequency drift (dewow)
3. Remove horizontal ringing (background removal)
4. Apply gain to compensate for attenuation
5. Filter unwanted frequencies
6. Determine subsurface velocity
7. Convert time to depth
8. Apply topographic corrections
9. Export results

## Step 1: Data Loading

```python
import gprpy.gprpy as gp

data = gp.gprpyProfile()
data.importdata('profile.DZT')

# Inspect data
print(f"Number of traces: {data.data.shape[1]}")
print(f"Samples per trace: {data.data.shape[0]}")
print(f"Time range: {data.twtt.min():.1f} to {data.twtt.max():.1f} ns")
print(f"Profile length: {data.profilePos.max():.1f} m")
```

### File Format Notes

| Format | Notes |
|--------|-------|
| .DZT (GSSI) | Most common, includes header with settings |
| .DT1 (Sensors & Software) | Requires matching .HD header file |
| .GPR (MALA) | XML-based header |
| .rd3/.rad (MALA) | Older MALA format |
| .sgy (SEG-Y) | Standard seismic format |

## Step 2: Dewow Filter

Removes low-frequency "wow" caused by inductive coupling between transmitter and receiver.

```python
# Window size in nanoseconds (5-20 ns typical)
data.dewow(window=10)
```

### Parameter Selection

| Antenna Frequency | Recommended Window |
|-------------------|-------------------|
| 100 MHz | 15-20 ns |
| 250 MHz | 10-15 ns |
| 500 MHz | 5-10 ns |
| 1000+ MHz | 3-5 ns |

**Rule of thumb**: Window should be ~1 wavelength of the center frequency.

## Step 3: Background Removal

Removes horizontal ringing and system noise that appears as horizontal banding.

```python
# Number of traces to average for background estimation
data.remMeanTrace(ntraces=50)
```

### Parameter Selection

| Survey Type | Recommended ntraces |
|-------------|---------------------|
| Uniform terrain | 50-100 |
| Variable terrain | 20-50 |
| Short profiles | 10-20 |
| Targeted anomalies | Avoid or use small window |

**Warning**: Aggressive background removal can attenuate flat-lying reflectors.

## Step 4: Gain Application

Compensates for signal attenuation with depth. Two main types:

### Time-Power Gain (SEC Gain)

```python
# Power exponent (1.0-2.0 typical)
data.tpowGain(power=1.5)
```

| Condition | Recommended Power |
|-----------|-------------------|
| Low attenuation (dry) | 1.0-1.2 |
| Moderate attenuation | 1.3-1.7 |
| High attenuation (wet) | 1.8-2.5 |

### Automatic Gain Control (AGC)

```python
# Window size in nanoseconds
data.agcGain(window=25)
```

| Purpose | Recommended Window |
|---------|-------------------|
| Preserve relative amplitudes | 50-100 ns |
| Enhance weak reflectors | 10-25 ns |
| Maximum enhancement | 5-10 ns |

**Note**: AGC destroys true amplitude information. Use tpowGain for quantitative analysis.

## Step 5: Frequency Filtering

### Bandpass Filter
```python
data.bandpassFilter(minfreq=100, maxfreq=800)  # MHz
```

### Lowpass Filter
```python
data.lowpassFilter(maxfreq=500)  # Remove high-frequency noise
```

### Highpass Filter
```python
data.highpassFilter(minfreq=50)  # Remove remaining low-frequency noise
```

### Recommended Filter Settings

| Antenna Frequency | Bandpass Range |
|-------------------|----------------|
| 100 MHz | 25-200 MHz |
| 250 MHz | 60-500 MHz |
| 500 MHz | 125-1000 MHz |
| 1000 MHz | 250-2000 MHz |

**Rule of thumb**: Pass band = 0.25 to 2.0 times the center frequency.

## Step 6: Velocity Analysis

### Method 1: Hyperbola Fitting

```python
# Display profile with hyperbola fitting capability
data.showProfile()
# Click on hyperbola apex, then on hyperbola limb
# Velocity is calculated from hyperbola curvature
```

### Method 2: CMP/WARR Analysis

```python
cmp = gp.gprpyCMP()
cmp.importdata('cmp_survey.DZT')
cmp.showCMP()

# Semblance analysis
cmp.semblance(vmin=0.05, vmax=0.15, vstep=0.01)
cmp.showSemblance()
```

### Velocity Selection

| Material | Velocity (m/ns) | Dielectric Constant |
|----------|-----------------|---------------------|
| Air | 0.30 | 1 |
| Ice | 0.16-0.17 | 3-4 |
| Dry sand | 0.10-0.15 | 4-9 |
| Dry soil | 0.08-0.12 | 5-15 |
| Limestone (dry) | 0.10-0.12 | 6-9 |
| Granite | 0.10-0.13 | 5-9 |
| Asphalt | 0.08-0.12 | 5-15 |
| Wet sand | 0.06-0.08 | 15-25 |
| Wet soil | 0.05-0.08 | 15-30 |
| Concrete | 0.06-0.10 | 9-25 |
| Clay | 0.05-0.08 | 15-40 |
| Fresh water | 0.033 | 81 |
| Sea water | 0.01 | ~81 |

**Velocity formula**: v = c / sqrt(er) where c = 0.3 m/ns and er = relative permittivity

## Step 7: Depth Conversion

```python
# Set velocity for depth conversion
velocity = 0.1  # m/ns
data.setVelocity(velocity)

# Display in depth
data.showProfile(yrng=[0, 5])  # Show top 5 meters
```

### Depth Calculation
- Depth = (Two-way travel time x Velocity) / 2
- Example: 50 ns at 0.1 m/ns = 2.5 m depth

## Step 8: Topographic Correction

```python
# Topography file format: position (m), elevation (m)
# Example content:
# 0.0  100.0
# 5.0  100.5
# 10.0  101.2

data.topoCorrect(topofile='topography.txt', velocity=0.1)
```

### Topography File Requirements
- Two columns: horizontal position, elevation
- Tab or space delimited
- Positions must match or span profile positions
- Interpolation is applied if needed

## Step 9: Export

### Export Image
```python
data.exportFig('processed_profile.png', dpi=300)
```

### Export SEG-Y
```python
data.exportSEGY('processed_profile.sgy')
```

### Export ASCII
```python
data.exportASCII('processed_profile.txt')
```

### Export Metadata
```python
# Save processing history
with open('processing_log.txt', 'w') as f:
    f.write(f"File: profile.DZT\n")
    f.write(f"Dewow: window=10\n")
    f.write(f"Background: ntraces=50\n")
    f.write(f"Gain: tpow=1.5\n")
    f.write(f"Velocity: {velocity} m/ns\n")
```

## Processing Tips

### General Guidelines

1. **Process incrementally**: Apply one step at a time and review results
2. **Preserve raw data**: Always work on copies, never modify originals
3. **Document parameters**: Record all processing settings for reproducibility
4. **Compare before/after**: Use side-by-side displays to evaluate each step

### Common Mistakes

| Mistake | Solution |
|---------|----------|
| Over-gained data | Reduce gain power or AGC window |
| Lost flat reflectors | Reduce background removal aggressiveness |
| Noisy shallow section | Check dewow window size |
| Incorrect depths | Verify velocity from hyperbola or CMP |
| Wrapped reflections | Check time zero correction |

### Quality Control Checklist

- [ ] Time zero is correct (first arrival aligned)
- [ ] DC offset removed (dewow applied)
- [ ] Horizontal banding minimized
- [ ] Deep reflectors visible (gain adequate)
- [ ] Signal-to-noise ratio acceptable
- [ ] Velocity verified by hyperbola or CMP
- [ ] Depth scale reasonable for known targets
- [ ] Processing parameters documented

### Batch Processing Considerations

```python
import glob

# Standard parameters for consistent processing
DEWOW_WINDOW = 10
BACKGROUND_TRACES = 50
GAIN_POWER = 1.5
VELOCITY = 0.1

files = glob.glob('survey/*.DZT')
for f in files:
    data = gp.gprpyProfile()
    data.importdata(f)
    data.dewow(window=DEWOW_WINDOW)
    data.remMeanTrace(ntraces=BACKGROUND_TRACES)
    data.tpowGain(power=GAIN_POWER)
    data.setVelocity(VELOCITY)
    data.exportFig(f.replace('.DZT', '_processed.png'), dpi=200)
```
