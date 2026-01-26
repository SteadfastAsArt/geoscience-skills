---
name: gprpy
description: Ground-penetrating radar (GPR) data processing and visualization. Load, process, and interpret radar profiles with GUI and scripting interfaces.
---

# GPRPy - Ground Penetrating Radar Processing

Help users process and visualize ground-penetrating radar data.

## Installation

```bash
pip install gprpy
```

## Core Concepts

### What GPRPy Does
- Load various GPR file formats
- Signal processing (dewow, gain, filters)
- Velocity analysis (CMP/WARR)
- Time-to-depth conversion
- Profile visualization and export

### Supported Formats
| Format | Manufacturer |
|--------|-------------|
| .DZT | GSSI |
| .DT1 | Sensors & Software |
| .GPR | MALA |
| .rd3/.rad | MALA |
| .sgy | SEG-Y |

## Common Workflows

### 1. Load and Display Profile
```python
import gprpy.gprpy as gp
import matplotlib.pyplot as plt

# Load GPR data
data = gp.gprpyProfile()
data.importdata('profile.DZT')

# Display profile
data.showProfile()
plt.show()

# Print info
print(f"Number of traces: {data.data.shape[1]}")
print(f"Samples per trace: {data.data.shape[0]}")
print(f"Time range: {data.twtt.max():.1f} ns")
```

### 2. Basic Processing Workflow
```python
import gprpy.gprpy as gp

# Load data
data = gp.gprpyProfile()
data.importdata('profile.DZT')

# Processing steps
data.dewow(window=10)              # Remove low-frequency wow
data.remMeanTrace(ntraces=50)      # Remove background
data.tpowGain(power=1.5)           # Time-power gain
data.agcGain(window=25)            # Automatic gain control

# Display processed
data.showProfile()
```

### 3. Apply Filters
```python
import gprpy.gprpy as gp

data = gp.gprpyProfile()
data.importdata('profile.DZT')

# Bandpass filter
data.bandpassFilter(
    minfreq=100,   # MHz
    maxfreq=800    # MHz
)

# Or lowpass/highpass
data.lowpassFilter(maxfreq=500)
data.highpassFilter(minfreq=50)

data.showProfile()
```

### 4. Time-to-Depth Conversion
```python
import gprpy.gprpy as gp

data = gp.gprpyProfile()
data.importdata('profile.DZT')

# Process first
data.dewow(window=10)
data.tpowGain(power=1.5)

# Convert to depth
velocity = 0.1  # m/ns (typical for dry sand)
data.topoCorrect(topofile='topography.txt', velocity=velocity)

# Or simple conversion without topography
data.setVelocity(velocity)

data.showProfile(yrng=[0, 5])  # Show top 5 meters
```

### 5. Topographic Correction
```python
import gprpy.gprpy as gp
import numpy as np

data = gp.gprpyProfile()
data.importdata('profile.DZT')

# Load topography (position, elevation)
# File format: x, elevation
topo = np.loadtxt('topography.txt')

# Apply correction
data.topoCorrect(
    topofile='topography.txt',
    velocity=0.1  # m/ns
)

data.showProfile()
```

### 6. Velocity Analysis (CMP)
```python
import gprpy.gprpy as gp

# Load CMP/WARR data
cmp = gp.gprpyCMP()
cmp.importdata('cmp_survey.DZT')

# Analyze velocity
cmp.showCMP()

# Semblance analysis
cmp.semblance(vmin=0.05, vmax=0.15, vstep=0.01)
cmp.showSemblance()

# Pick velocities interactively
# Or set manually
velocity = 0.09  # m/ns
```

### 7. Export Processed Data
```python
import gprpy.gprpy as gp

data = gp.gprpyProfile()
data.importdata('profile.DZT')

# Process
data.dewow(window=10)
data.tpowGain(power=1.5)

# Export as image
data.exportFig('processed_profile.png', dpi=300)

# Export as SEG-Y
data.exportSEGY('processed_profile.sgy')

# Export as ASCII
data.exportASCII('processed_profile.txt')
```

### 8. Adjust Profile Display
```python
import gprpy.gprpy as gp
import matplotlib.pyplot as plt

data = gp.gprpyProfile()
data.importdata('profile.DZT')
data.dewow(window=10)

# Custom display
fig, ax = plt.subplots(figsize=(12, 6))

data.showProfile(
    ax=ax,
    color='seismic',      # Colormap
    contrast=2.0,         # Amplitude contrast
    yrng=[0, 100],        # Y range (ns or m)
    xrng=[0, 50],         # X range (m)
    showlnhp=True         # Show line/hyperbol a
)

plt.title('GPR Profile - Line 1')
plt.savefig('profile.png', dpi=300, bbox_inches='tight')
```

### 9. Hyperbola Fitting
```python
import gprpy.gprpy as gp

data = gp.gprpyProfile()
data.importdata('profile.DZT')
data.dewow(window=10)

# Interactive hyperbola fitting
# In GUI mode, use 'h' key to fit hyperbolae
# Velocity is calculated from hyperbola shape

# Or use programmatically
data.showProfile()
# Click on hyperbola apex, then on hyperbola limb
# Velocity is displayed
```

### 10. Multiple Profiles
```python
import gprpy.gprpy as gp
import matplotlib.pyplot as plt
import glob

# Load all profiles
files = glob.glob('survey/*.DZT')
profiles = []

for f in files:
    data = gp.gprpyProfile()
    data.importdata(f)
    data.dewow(window=10)
    data.tpowGain(power=1.5)
    profiles.append(data)

# Plot all profiles
fig, axes = plt.subplots(len(profiles), 1, figsize=(12, 4*len(profiles)))

for ax, data, f in zip(axes, profiles, files):
    data.showProfile(ax=ax)
    ax.set_title(f)

plt.tight_layout()
plt.savefig('all_profiles.png', dpi=200)
```

### 11. Remove Ringing
```python
import gprpy.gprpy as gp

data = gp.gprpyProfile()
data.importdata('profile.DZT')

# Remove horizontal ringing (background removal)
data.remMeanTrace(ntraces=100)

# Or use f-k filter for dipping noise
# (requires manual implementation or external tools)

data.showProfile()
```

### 12. GUI Mode
```python
import gprpy.gprpy as gp

# Launch GUI for interactive processing
# In terminal:
# gprpy

# Or from Python:
data = gp.gprpyProfile()
data.importdata('profile.DZT')

# Interactive processing window
data.showGUI()
```

## Processing Parameters

| Parameter | Typical Value | Description |
|-----------|---------------|-------------|
| Dewow window | 5-20 ns | Low-freq removal window |
| Gain power | 1.0-2.0 | Time-power gain exponent |
| AGC window | 10-50 ns | Automatic gain window |
| Bandpass | 100-800 MHz | Frequency filter range |

## Velocity Values

| Material | Velocity (m/ns) |
|----------|-----------------|
| Air | 0.30 |
| Dry sand | 0.10-0.15 |
| Wet sand | 0.06-0.08 |
| Dry soil | 0.08-0.12 |
| Wet soil | 0.05-0.08 |
| Limestone | 0.10-0.12 |
| Granite | 0.10-0.13 |
| Water | 0.033 |
| Ice | 0.16-0.17 |

## Tips

1. **Always dewow first** - Removes low-frequency drift
2. **Apply gain after dewow** - Better amplitude balance
3. **Use CMP for velocity** - More accurate than hyperbola fitting
4. **Check time zero** - Critical for depth conversion
5. **Document processing** - Keep track of parameters

## Resources

- GitHub: https://github.com/NSGeophysics/GPRPy
- Documentation: See GitHub wiki
- Citation: SEG Library publication
