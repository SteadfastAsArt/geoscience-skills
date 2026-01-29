# Dispersion Curves Reference

## Table of Contents
- [Phase vs Group Velocity](#phase-vs-group-velocity)
- [Mode Numbering](#mode-numbering)
- [Wave Types](#wave-types)
- [Dispersion Characteristics](#dispersion-characteristics)
- [Measurement Techniques](#measurement-techniques)

## Phase vs Group Velocity

### Phase Velocity (c)
The velocity at which a single frequency component propagates.

```python
from disba import PhaseDispersion

pd = PhaseDispersion(*zip(thickness, vp, vs, rho))
phase_vel = pd(periods, mode=0, wave='rayleigh')
```

### Group Velocity (U)
The velocity at which energy (wave packet) propagates. Related to phase velocity by:

```
U = c + T * (dc/dT)
```

where T is period.

```python
from disba import GroupDispersion

gd = GroupDispersion(*zip(thickness, vp, vs, rho))
group_vel = gd(periods, mode=0, wave='rayleigh')
```

### Key Differences

| Property | Phase Velocity | Group Velocity |
|----------|---------------|----------------|
| Physical meaning | Wavefront propagation | Energy propagation |
| Measurement | Cross-correlation | Envelope tracking |
| Typical value | Usually higher | Usually lower |
| Relation to structure | Direct from c(T) | Derivative of c(T) |

## Mode Numbering

### Fundamental Mode (mode=0)
- Lowest velocity at each period
- Most commonly measured
- Penetrates deepest for a given period
- Most stable in computation

### Higher Modes (mode=1, 2, ...)
- Higher velocities than fundamental
- Shallower sensitivity
- May not exist at all periods
- Require specific velocity structures

```python
# Check which modes exist
for mode in range(5):
    try:
        c = pd(periods, mode=mode, wave='rayleigh')
        print(f"Mode {mode}: computed for {len(c)} periods")
    except Exception as e:
        print(f"Mode {mode}: not available - {e}")
```

### Mode Characteristics

| Mode | Velocity | Depth Sensitivity | Stability |
|------|----------|-------------------|-----------|
| 0 (Fundamental) | Lowest | Deepest | Most stable |
| 1 (First overtone) | Higher | Shallower | Less stable |
| 2+ (Higher overtones) | Highest | Shallowest | Least stable |

## Wave Types

### Rayleigh Waves
- Particle motion: Retrograde ellipse (vertical + radial)
- Sensitive to: Vs (primary), Vp (secondary), density
- Existence: Always present in layered media
- Typical use: Primary wave for ambient noise tomography

```python
cpr = pd(periods, mode=0, wave='rayleigh')
```

### Love Waves
- Particle motion: Horizontal (SH), transverse to propagation
- Sensitive to: Vs only (not Vp or density in isotropic media)
- Existence: Requires low-velocity layer over half-space
- Typical use: Constrain Vs independently of Vp

```python
cpl = pd(periods, mode=0, wave='love')
```

### Comparing Wave Types

```python
import matplotlib.pyplot as plt

periods = np.linspace(0.1, 5.0, 50)
pd = PhaseDispersion(*zip(thickness, vp, vs, rho))

cpr = pd(periods, mode=0, wave='rayleigh')
cpl = pd(periods, mode=0, wave='love')

plt.plot(periods, cpr, 'b-', label='Rayleigh')
plt.plot(periods, cpl, 'g-', label='Love')
plt.xlabel('Period (s)')
plt.ylabel('Phase velocity (km/s)')
plt.legend()
```

## Dispersion Characteristics

### Normal Dispersion
Phase velocity increases with period (deeper sampling = faster velocity).
Typical of Earth models with velocity increasing with depth.

### Anomalous Dispersion
Phase velocity decreases with period at some frequencies.
Indicates low-velocity zone at depth.

### Dispersion Curve Shape Indicators

| Shape | Geological Interpretation |
|-------|---------------------------|
| Smooth increase | Gradual velocity increase with depth |
| Sharp kink | Velocity discontinuity (e.g., Moho) |
| Flat section | Thick layer with uniform velocity |
| Velocity decrease | Low velocity zone present |

## Measurement Techniques

### FTAN (Frequency-Time Analysis)
- Measures group velocity
- Uses narrow bandpass filtering
- Envelope of filtered signal
- Common for earthquake data

### Phase Cross-Correlation
- Measures phase velocity
- Cross-correlate two stations
- Phase of cross-spectrum
- Common for ambient noise

### Array Methods (SPAC, MASW)
- Simultaneous phase velocity
- Spatial autocorrelation
- Multi-channel analysis
- Common for engineering applications

## Period-Depth Relationship

Approximate rule of thumb for Rayleigh waves:
- Sensitivity depth ~ 1/3 wavelength
- wavelength = velocity * period

```python
# Approximate depth of maximum sensitivity
def approx_sensitivity_depth(period, avg_velocity=3.0):
    """
    Estimate depth of maximum sensitivity.

    Args:
        period: Period in seconds
        avg_velocity: Average velocity in km/s

    Returns:
        Approximate depth in km
    """
    wavelength = avg_velocity * period
    return wavelength / 3.0

# Example: 10s period, 3 km/s average
depth = approx_sensitivity_depth(10.0, 3.0)  # ~10 km
```

## Frequency vs Period Convention

disba uses **period** (seconds). To use frequency:

```python
# Convert frequency (Hz) to period (s)
frequencies = np.linspace(0.2, 10.0, 50)  # Hz
periods = 1.0 / frequencies  # seconds

# Sort by increasing period for plotting
sort_idx = np.argsort(periods)
periods = periods[sort_idx]

cpr = pd(periods, mode=0, wave='rayleigh')
```
