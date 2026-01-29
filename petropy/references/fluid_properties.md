# Fluid Property Models Reference

## Table of Contents
- [Formation Water Resistivity](#formation-water-resistivity)
- [Hydrocarbon Properties](#hydrocarbon-properties)
- [Mud Filtrate](#mud-filtrate)
- [Temperature and Pressure](#temperature-and-pressure)

## Formation Water Resistivity

### Rw from Salinity
```
Rw = 1 / (salinity * conductivity_factor)

Temperature correction (Arps):
Rw2 = Rw1 * (T1 + 21.5) / (T2 + 21.5)  # Temperatures in Celsius
Rw2 = Rw1 * (T1 + 6.77) / (T2 + 6.77)  # Temperatures in Fahrenheit
```

### Rw from SP Log
```
SSP = -K * log10(Rmf/Rw)
K = 61 + 0.133 * T  # T in Fahrenheit

Solving for Rw:
Rw = Rmf / 10^(-SSP/K)
```

### Rw from Water Sample
```python
import numpy as np

def rw_from_salinity(salinity_ppm, temperature_c):
    """
    Calculate Rw from salinity (NaCl equivalent).

    Args:
        salinity_ppm: Salinity in ppm (mg/L)
        temperature_c: Temperature in Celsius

    Returns:
        Rw in ohm-m
    """
    # Conductivity factor (simplified)
    salinity_mol = salinity_ppm / 58443  # Convert to mol/L
    rw_25c = 1 / (salinity_ppm * 0.00001 * 1.5)

    # Temperature correction
    rw = rw_25c * (25 + 21.5) / (temperature_c + 21.5)
    return rw

def rw_temperature_correction(rw1, temp1, temp2):
    """Correct Rw from temp1 to temp2 (both in Celsius)."""
    return rw1 * (temp1 + 21.5) / (temp2 + 21.5)

def rw_from_sp(sp, rmf, temperature_f):
    """
    Calculate Rw from SP log.

    Args:
        sp: SP deflection (mV), negative into sand
        rmf: Mud filtrate resistivity at formation temp (ohm-m)
        temperature_f: Formation temperature (Fahrenheit)

    Returns:
        Rw in ohm-m
    """
    k = 61 + 0.133 * temperature_f
    rw = rmf / np.power(10, -sp / k)
    return rw
```

### Typical Rw Values

| Water Type | Salinity (ppm) | Rw at 75F (ohm-m) |
|------------|----------------|-------------------|
| Fresh | <1,000 | >5.0 |
| Brackish | 1,000-10,000 | 0.5-5.0 |
| Saline | 10,000-100,000 | 0.05-0.5 |
| Brine | >100,000 | <0.05 |

## Hydrocarbon Properties

### Oil Density
```
API gravity = (141.5 / SG) - 131.5
SG = 141.5 / (API + 131.5)

Where:
  SG = specific gravity relative to water
  API = API gravity (degrees)
```

### Gas Compressibility Factor (Z-factor)
```
Standing-Katz correlation (simplified):
Z = A + B/Ppr + C/Ppr^3

Where:
  Ppr = P/Pc (pseudo-reduced pressure)
  Tpr = T/Tc (pseudo-reduced temperature)
```

### Gas Formation Volume Factor
```
Bg = 0.0283 * Z * T / P

Where:
  Z = gas compressibility factor
  T = temperature (Rankine)
  P = pressure (psia)
  Bg = res bbl/scf
```

### Oil Formation Volume Factor (Standing)
```
Bo = 0.9759 + 0.00012 * (Rs * sqrt(gamma_g / gamma_o) + 1.25 * T)^1.2

Where:
  Rs = solution GOR (scf/stb)
  gamma_g = gas specific gravity
  gamma_o = oil specific gravity
  T = temperature (F)
```

### Implementation
```python
import numpy as np

def api_to_sg(api):
    """Convert API gravity to specific gravity."""
    return 141.5 / (api + 131.5)

def sg_to_api(sg):
    """Convert specific gravity to API gravity."""
    return (141.5 / sg) - 131.5

def gas_fvf(pressure_psia, temperature_f, z_factor):
    """
    Calculate gas formation volume factor.

    Returns:
        Bg in res bbl/scf
    """
    temp_r = temperature_f + 459.67
    bg = 0.0283 * z_factor * temp_r / pressure_psia
    return bg

def oil_fvf_standing(rs, gamma_g, gamma_o, temperature_f):
    """
    Calculate oil formation volume factor using Standing correlation.

    Args:
        rs: Solution GOR (scf/stb)
        gamma_g: Gas specific gravity (air = 1)
        gamma_o: Oil specific gravity (water = 1)
        temperature_f: Temperature (Fahrenheit)

    Returns:
        Bo in res bbl/stb
    """
    term = rs * np.sqrt(gamma_g / gamma_o) + 1.25 * temperature_f
    bo = 0.9759 + 0.00012 * np.power(term, 1.2)
    return bo

def oil_viscosity_beggs(api, temperature_f, rs=0):
    """
    Estimate oil viscosity using Beggs-Robinson correlation.

    Args:
        api: Oil API gravity
        temperature_f: Temperature (Fahrenheit)
        rs: Solution GOR (scf/stb), 0 for dead oil

    Returns:
        Viscosity in cp
    """
    # Dead oil viscosity
    x = np.exp(6.9824 - 0.04658 * api)
    y = np.power(10, x)
    mu_od = np.power(10, y * np.power(temperature_f, -1.163)) - 1

    if rs == 0:
        return mu_od

    # Live oil correction
    a = 10.715 * np.power(rs + 100, -0.515)
    b = 5.44 * np.power(rs + 150, -0.338)
    mu_o = a * np.power(mu_od, b)
    return mu_o
```

## Mud Filtrate

### Rmf Estimation
```
From mud weight:
Rmf_75F = 0.75 * Rm_75F  (for freshwater mud)
Rmf_75F = 0.85 * Rm_75F  (for NaCl mud)

Temperature correction same as Rw:
Rmf2 = Rmf1 * (T1 + 21.5) / (T2 + 21.5)
```

### Rmc (Mudcake Resistivity)
```
Rmc = 0.5 * Rmf  (typical approximation)
```

### Implementation
```python
def rmf_from_rm(rm, mud_type='fresh', temperature_c=25):
    """
    Estimate mud filtrate resistivity from mud resistivity.

    Args:
        rm: Mud resistivity at temperature_c (ohm-m)
        mud_type: 'fresh' or 'nacl'
        temperature_c: Temperature (Celsius)

    Returns:
        Rmf in ohm-m at given temperature
    """
    if mud_type == 'fresh':
        factor = 0.75
    else:
        factor = 0.85

    return rm * factor

def rmf_temperature_correction(rmf1, temp1, temp2):
    """Correct Rmf from temp1 to temp2 (both in Celsius)."""
    return rmf1 * (temp1 + 21.5) / (temp2 + 21.5)
```

## Temperature and Pressure

### Geothermal Gradient
```
T_formation = T_surface + gradient * TVD

Typical gradients:
  - Normal: 1.6 F/100ft (30 C/km)
  - High: 2.0+ F/100ft (36+ C/km)
```

### Hydrostatic Pressure
```
P_hydrostatic = 0.433 * SG_water * TVD  (psi, ft)
P_hydrostatic = 0.0981 * SG_water * TVD  (MPa, m)

Normal gradient: 0.465 psi/ft (10.5 kPa/m)
```

### Overburden Pressure
```
P_overburden = integral(rho_bulk * g * dz)

Typical gradient: 1.0-1.1 psi/ft (22-25 kPa/m)
```

### Implementation
```python
import numpy as np

def formation_temperature(tvd_ft, surface_temp_f=60, gradient_f_per_100ft=1.6):
    """
    Calculate formation temperature from depth.

    Args:
        tvd_ft: True vertical depth (feet)
        surface_temp_f: Surface temperature (Fahrenheit)
        gradient_f_per_100ft: Geothermal gradient (F per 100 ft)

    Returns:
        Formation temperature (Fahrenheit)
    """
    return surface_temp_f + (gradient_f_per_100ft / 100) * tvd_ft

def hydrostatic_pressure(tvd_ft, water_sg=1.0):
    """
    Calculate hydrostatic pressure.

    Args:
        tvd_ft: True vertical depth (feet)
        water_sg: Water specific gravity (default 1.0)

    Returns:
        Pressure in psi
    """
    return 0.433 * water_sg * tvd_ft

def overburden_pressure(tvd_ft, avg_bulk_density=2.3):
    """
    Estimate overburden pressure.

    Args:
        tvd_ft: True vertical depth (feet)
        avg_bulk_density: Average bulk density (g/cc)

    Returns:
        Pressure in psi
    """
    # Convert g/cc to psi/ft: 1 g/cc = 0.433 psi/ft
    gradient = 0.433 * avg_bulk_density
    return gradient * tvd_ft

def pore_pressure_gradient(pressure_psi, tvd_ft):
    """Calculate pore pressure gradient in ppg equivalent."""
    return pressure_psi / (0.052 * tvd_ft)
```

## Fluid Contact Estimation

### Capillary Pressure
```
Pc = (2 * sigma * cos(theta)) / r

Height above FWL:
h = Pc / (delta_rho * g)
```

### Free Water Level (FWL) from Logs
```python
import numpy as np

def estimate_fwl(depth, sw, phi, threshold=0.9):
    """
    Estimate free water level from saturation profile.

    Args:
        depth: Depth array
        sw: Water saturation array
        phi: Porosity array (to exclude non-reservoir)
        threshold: Sw threshold for water zone (default 0.9)

    Returns:
        Estimated FWL depth
    """
    # Find where Sw exceeds threshold in reservoir rock
    reservoir = phi > 0.05
    water_zone = (sw > threshold) & reservoir

    if np.any(water_zone):
        # FWL is top of water zone
        fwl = depth[water_zone].min()
        return fwl
    return None

def transition_zone_height(sw, depth, owc_depth):
    """
    Analyze transition zone characteristics.

    Args:
        sw: Water saturation array
        depth: Depth array
        owc_depth: Oil-water contact depth

    Returns:
        Dictionary with transition zone properties
    """
    above_owc = depth < owc_depth
    sw_above = sw[above_owc]
    depth_above = depth[above_owc]

    # Find where Sw drops below irreducible
    swi_approx = np.min(sw_above)
    swi_depth = depth_above[sw_above == swi_approx][0] if swi_approx < 0.3 else None

    return {
        'owc': owc_depth,
        'swi': swi_approx,
        'swi_depth': swi_depth,
        'transition_height': owc_depth - swi_depth if swi_depth else None
    }
```

## Typical Fluid Properties

### Oil Properties by API

| API | Density (g/cc) | Type |
|-----|----------------|------|
| <10 | >1.0 | Extra Heavy |
| 10-22 | 0.92-1.0 | Heavy |
| 22-32 | 0.87-0.92 | Medium |
| 32-42 | 0.82-0.87 | Light |
| >42 | <0.82 | Condensate |

### Gas Properties

| Property | Typical Range | Unit |
|----------|---------------|------|
| Specific Gravity | 0.55-0.90 | (air=1) |
| Z-factor | 0.7-1.0 | dimensionless |
| Bg | 0.002-0.010 | res bbl/scf |
| Viscosity | 0.01-0.03 | cp |

### Formation Water

| Property | Fresh | Saline | Brine |
|----------|-------|--------|-------|
| Salinity (ppm) | <1,000 | 10,000-100,000 | >100,000 |
| Rw at 75F | >5.0 | 0.05-0.5 | <0.05 |
| Density (g/cc) | 1.00 | 1.02-1.07 | 1.07-1.20 |
