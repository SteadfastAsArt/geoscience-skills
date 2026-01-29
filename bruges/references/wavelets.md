# Seismic Wavelets

## Table of Contents
- [Wavelet Basics](#wavelet-basics)
- [Ricker Wavelet](#ricker-wavelet)
- [Ormsby Wavelet](#ormsby-wavelet)
- [Klauder Wavelet](#klauder-wavelet)
- [Wavelet Selection](#wavelet-selection)
- [Frequency and Resolution](#frequency-and-resolution)

## Wavelet Basics

A seismic wavelet is the basic pulse shape used in seismic reflection. Key properties:

| Property | Description | Unit |
|----------|-------------|------|
| Dominant frequency | Peak frequency of amplitude spectrum | Hz |
| Duration | Length of wavelet in time | s |
| Phase | Zero-phase, minimum-phase, or mixed | degrees |
| Sample rate (dt) | Time between samples | s |

## Ricker Wavelet

Also known as the Mexican Hat wavelet. Zero-phase, symmetric.

### Parameters
```python
from bruges.filters import ricker

t, wavelet = ricker(
    duration=0.128,  # Total length in seconds
    dt=0.001,        # Sample interval in seconds
    f=25             # Dominant frequency in Hz
)
```

### Characteristics
- **Zero-phase**: Symmetric about t=0
- **Single parameter**: Controlled by dominant frequency f
- **Bandwidth**: Peak frequency = f, bandwidth ~ 1.3*f
- **Side lobes**: Has negative side lobes

### Frequency Content
```
f_low = f / sqrt(3)   # ~0.58 * f
f_peak = f             # Dominant frequency
f_high = f * sqrt(3)  # ~1.73 * f
```

### Common Frequencies
| Environment | Frequency (Hz) |
|-------------|---------------|
| Shallow marine | 40-60 |
| Deep marine | 20-40 |
| Onshore | 15-35 |
| Deep exploration | 10-20 |

## Ormsby Wavelet

Trapezoidal bandpass wavelet. More control over frequency content.

### Parameters
```python
from bruges.filters import ormsby

f = [5, 10, 50, 60]  # [f1, f2, f3, f4] in Hz
t, wavelet = ormsby(
    duration=0.128,
    dt=0.001,
    f=f
)
```

### Frequency Corners
```
f1: Low cut (start of ramp up)
f2: Low pass (end of ramp up, start of flat)
f3: High pass (end of flat, start of ramp down)
f4: High cut (end of ramp down)

Amplitude spectrum:
        ____f2____f3____
       /                \
      /                  \
_____f1                  f4_____
```

### Typical Ormsby Bandwidths
| Type | f1 | f2 | f3 | f4 |
|------|----|----|----|----|
| Broadband | 2 | 6 | 80 | 100 |
| Standard | 5 | 10 | 50 | 60 |
| Low freq | 3 | 8 | 30 | 40 |
| High freq | 10 | 20 | 80 | 100 |

## Klauder Wavelet

Linear sweep (chirp) wavelet, used for Vibroseis modeling.

### Parameters
```python
from bruges.filters import klauder

t, wavelet = klauder(
    duration=0.128,
    dt=0.001,
    f=[10, 80],     # Start and end frequencies
    taper=20        # Taper length
)
```

## Wavelet Selection

### By Application
| Application | Wavelet | Why |
|-------------|---------|-----|
| General modeling | Ricker | Simple, one parameter |
| Realistic bandwidth | Ormsby | Control corners |
| Vibroseis synthetic | Klauder | Matches acquisition |
| AVO modeling | Ricker/Ormsby | Zero-phase preferred |

### By Data Type
| Data | Recommended |
|------|-------------|
| Marine streamer | Ormsby (broadband) |
| Land Vibroseis | Klauder or Ormsby |
| Air gun | Ormsby |
| Dynamite | Ricker |

## Frequency and Resolution

### Vertical Resolution
```
Tuning thickness = lambda/4 = V / (4*f)

Example: V=3000 m/s, f=30 Hz
lambda = 3000/30 = 100 m
Tuning thickness = 25 m
```

### Resolution Table
| Frequency (Hz) | Wavelength at 3000 m/s | Tuning (m) |
|----------------|------------------------|------------|
| 10 | 300 m | 75 |
| 20 | 150 m | 37.5 |
| 30 | 100 m | 25 |
| 50 | 60 m | 15 |
| 80 | 37.5 m | 9.4 |

### Frequency vs Depth
Higher frequencies attenuate faster. Rule of thumb:
```
f_dominant ~ 100 / sqrt(depth_km)

Example depths:
1 km: ~100 Hz
2 km: ~70 Hz
4 km: ~50 Hz
```

## Creating Synthetic Seismograms

```python
import numpy as np
from bruges.filters import ricker
from scipy.signal import convolve

# 1. Create reflectivity from impedance
impedance = vp * rho
rc = np.diff(impedance) / (impedance[:-1] + impedance[1:])

# 2. Create wavelet
_, wavelet = ricker(0.128, 0.001, 30)

# 3. Convolve
synthetic = convolve(rc, wavelet, mode='same')
```

## Phase Considerations

| Phase | Description | Use |
|-------|-------------|-----|
| Zero-phase | Symmetric, peak at t=0 | Ideal for interpretation |
| Minimum-phase | Causal, energy front-loaded | Realistic acquisition |
| Mixed-phase | Combination | Processed data |

### Phase Rotation
```python
from scipy.signal import hilbert

# 90-degree phase rotation
analytic = hilbert(wavelet)
rotated_90 = np.imag(analytic)

# Arbitrary rotation
def phase_rotate(wavelet, angle_deg):
    angle_rad = np.deg2rad(angle_deg)
    analytic = hilbert(wavelet)
    return np.real(analytic) * np.cos(angle_rad) + \
           np.imag(analytic) * np.sin(angle_rad)
```
