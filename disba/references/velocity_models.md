# Velocity Model Configuration

## Table of Contents
- [Model Structure](#model-structure)
- [Parameter Units](#parameter-units)
- [Common Velocity Profiles](#common-velocity-profiles)
- [Model Constraints](#model-constraints)
- [Empirical Relations](#empirical-relations)

## Model Structure

### Layer Definition

A disba velocity model consists of horizontal layers defined by four parameters:

```python
import numpy as np

# Each array has one element per layer
thickness = np.array([0.5, 1.0, 2.0, 0.0])  # km
vp = np.array([1.5, 2.5, 4.0, 6.0])          # km/s
vs = np.array([0.8, 1.4, 2.3, 3.5])          # km/s
rho = np.array([1.8, 2.0, 2.3, 2.6])         # g/cm3
```

### Half-Space Convention

The **last layer** represents a half-space (infinite thickness):
- Set `thickness[-1] = 0.0` to indicate half-space
- Properties of half-space affect long-period dispersion

```python
# Correct: last layer is half-space
thickness = np.array([1.0, 2.0, 0.0])  # 3 layers, last is infinite

# Incorrect: no half-space
thickness = np.array([1.0, 2.0, 3.0])  # Will cause errors
```

### Creating the Model

```python
from disba import PhaseDispersion

# Method 1: Zip arrays
pd = PhaseDispersion(*zip(thickness, vp, vs, rho))

# Method 2: Explicit tuples
layers = [
    (0.5, 1.5, 0.8, 1.8),  # (thickness, vp, vs, rho)
    (1.0, 2.5, 1.4, 2.0),
    (0.0, 4.0, 2.3, 2.3),  # half-space
]
pd = PhaseDispersion(*layers)
```

## Parameter Units

| Parameter | Unit | Notes |
|-----------|------|-------|
| thickness | km | Use 0 for half-space |
| vp | km/s | P-wave velocity |
| vs | km/s | S-wave velocity |
| rho | g/cm3 | Density |
| period | s | Input to dispersion calculation |

### Unit Conversion

```python
# Meters to kilometers
thickness_m = np.array([500, 1000, 2000, 0])
thickness_km = thickness_m / 1000.0

# m/s to km/s
vs_ms = np.array([800, 1400, 2300, 3500])
vs_kms = vs_ms / 1000.0

# kg/m3 to g/cm3
rho_kgm3 = np.array([1800, 2000, 2300, 2600])
rho_gcc = rho_kgm3 / 1000.0
```

## Common Velocity Profiles

### Simple Gradient Model

```python
def gradient_model(n_layers=10, vs_top=0.5, vs_bot=4.0, total_depth=10.0):
    """Create a linear gradient Vs model."""
    layer_thickness = total_depth / n_layers
    thickness = np.full(n_layers + 1, layer_thickness)
    thickness[-1] = 0.0  # half-space

    vs = np.linspace(vs_top, vs_bot, n_layers + 1)
    vp = vs * 1.73  # Vp/Vs ratio
    rho = 0.32 * vp + 0.77  # Gardner

    return thickness, vp, vs, rho
```

### Low Velocity Zone (LVZ)

```python
def lvz_model():
    """Model with a low velocity zone."""
    thickness = np.array([1.0, 1.0, 2.0, 0.0])
    vs = np.array([1.0, 0.7, 2.0, 3.5])  # LVZ at 1-2 km
    vp = vs * 1.73
    rho = 0.32 * vp + 0.77

    return thickness, vp, vs, rho
```

### Continental Crust

```python
def continental_crust():
    """Simplified continental crust model."""
    # Sediments, upper crust, lower crust, mantle
    thickness = np.array([2.0, 15.0, 18.0, 0.0])
    vs = np.array([2.0, 3.5, 3.9, 4.5])
    vp = np.array([3.5, 6.1, 6.8, 8.1])
    rho = np.array([2.3, 2.7, 2.9, 3.3])

    return thickness, vp, vs, rho
```

### Oceanic Crust

```python
def oceanic_crust():
    """Simplified oceanic crust model."""
    # Water, sediments, layer 2, layer 3, mantle
    thickness = np.array([4.0, 0.5, 2.0, 5.0, 0.0])
    vs = np.array([0.0, 1.5, 3.0, 3.8, 4.5])
    vp = np.array([1.5, 2.5, 5.5, 7.0, 8.1])
    rho = np.array([1.03, 2.0, 2.6, 2.9, 3.3])

    return thickness, vp, vs, rho
```

### Near-Surface Engineering

```python
def engineering_site():
    """Typical near-surface engineering model."""
    # Soil, weathered rock, rock, bedrock
    thickness = np.array([0.005, 0.010, 0.020, 0.0])  # km (5m, 10m, 20m)
    vs = np.array([0.15, 0.30, 0.50, 1.0])  # km/s
    vp = vs * 2.0  # Higher Vp/Vs in shallow soils
    rho = np.array([1.6, 1.8, 2.0, 2.2])

    return thickness, vp, vs, rho
```

## Model Constraints

### Physical Constraints

```python
def validate_model(thickness, vp, vs, rho):
    """Check model validity."""
    errors = []

    # Vs must be less than Vp
    if np.any(vs >= vp):
        errors.append("Vs must be less than Vp")

    # All values must be positive
    if np.any(vp <= 0) or np.any(vs <= 0) or np.any(rho <= 0):
        errors.append("Velocities and density must be positive")

    # Thickness must be non-negative
    if np.any(thickness[:-1] <= 0):
        errors.append("Layer thickness must be positive (except half-space)")

    # Last layer should be half-space
    if thickness[-1] != 0.0:
        errors.append("Last layer should have thickness=0 (half-space)")

    # Reasonable Vp/Vs ratio (1.5 - 2.5 typical)
    ratio = vp / vs
    if np.any(ratio < 1.4) or np.any(ratio > 3.0):
        errors.append(f"Unusual Vp/Vs ratio detected: {ratio}")

    return errors
```

### Poisson's Ratio Limits

Vp/Vs ratio is related to Poisson's ratio:

```python
def vp_vs_to_poisson(vp_vs_ratio):
    """Convert Vp/Vs ratio to Poisson's ratio."""
    return (vp_vs_ratio**2 - 2) / (2 * (vp_vs_ratio**2 - 1))

# Valid range: Poisson's ratio 0 to 0.5
# Corresponds to Vp/Vs: sqrt(2) to infinity
# Typical rocks: Vp/Vs 1.6-2.0, Poisson 0.18-0.33
```

## Empirical Relations

### Vp-Vs Relations

```python
# Brocher (2005) empirical relation for Vp > 1.5 km/s
def brocher_vs(vp):
    """Estimate Vs from Vp using Brocher (2005)."""
    return 0.7858 - 1.2344*vp + 0.7949*vp**2 - 0.1238*vp**3 + 0.0064*vp**4

# Simple constant ratio
def simple_vs(vp, ratio=1.73):
    """Estimate Vs from Vp using constant ratio."""
    return vp / ratio

# Castagna mudrock line
def castagna_vs(vp):
    """Estimate Vs from Vp using Castagna mudrock line."""
    return (vp - 1.36) / 1.16
```

### Density Relations

```python
# Gardner et al. (1974)
def gardner_density(vp):
    """Estimate density from Vp using Gardner relation."""
    return 0.31 * vp**0.25  # vp in km/s, returns g/cm3

# Nafe-Drake curve (approximation)
def nafe_drake_density(vp):
    """Estimate density from Vp using Nafe-Drake."""
    return 1.6612 * vp - 0.4721 * vp**2 + 0.0671 * vp**3 - 0.0043 * vp**4 + 0.000106 * vp**5

# Linear approximation (commonly used)
def linear_density(vp):
    """Simple linear density estimate."""
    return 0.32 * vp + 0.77
```

### Complete Model from Vs Only

```python
def vs_to_full_model(vs, thickness, vp_vs_ratio=1.73):
    """
    Create full model from Vs profile only.

    Args:
        vs: S-wave velocity array (km/s)
        thickness: Layer thickness array (km)
        vp_vs_ratio: Vp/Vs ratio (default 1.73)

    Returns:
        thickness, vp, vs, rho
    """
    vp = vs * vp_vs_ratio
    rho = 0.32 * vp + 0.77  # Linear density relation

    return thickness, vp, vs, rho
```

## Model Resolution

### Layer Thickness Guidelines

| Application | Typical Layer Thickness | Period Range |
|-------------|------------------------|--------------|
| Engineering (MASW) | 1-5 m | 0.05-1 s |
| Shallow crustal | 0.5-2 km | 1-20 s |
| Regional | 2-10 km | 10-100 s |
| Global | 10-50 km | 50-300 s |

### Minimum Layers for Period

Rule of thumb: At least 3-5 layers per wavelength for accurate dispersion.

```python
def minimum_layers(min_period, max_depth, avg_velocity=3.0):
    """
    Estimate minimum number of layers for accurate dispersion.

    Args:
        min_period: Minimum period in seconds
        max_depth: Maximum model depth in km
        avg_velocity: Average velocity in km/s

    Returns:
        Suggested number of layers
    """
    min_wavelength = avg_velocity * min_period
    layers_per_wavelength = 4
    return int(max_depth / min_wavelength * layers_per_wavelength) + 1
```
