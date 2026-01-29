# Rock Physics Equations

## Table of Contents
- [Elastic Moduli](#elastic-moduli)
- [Velocity-Moduli Relations](#velocity-moduli-relations)
- [Empirical Relations](#empirical-relations)
- [Fluid Substitution](#fluid-substitution)
- [Effective Medium Models](#effective-medium-models)
- [Common Mineral Properties](#common-mineral-properties)
- [Common Fluid Properties](#common-fluid-properties)

## Elastic Moduli

### From Velocities
```python
from bruges.rockphysics import moduli

# Bulk modulus (K) in GPa
K = moduli.bulk(vp, vs, rho)  # K = rho * (Vp^2 - 4/3 * Vs^2)

# Shear modulus (mu) in GPa
mu = moduli.shear(vs, rho)    # mu = rho * Vs^2

# Young's modulus (E) in GPa
E = moduli.youngs(vp, vs, rho)

# Poisson's ratio (nu)
nu = moduli.poissons(vp, vs)  # nu = (Vp^2 - 2*Vs^2) / (2*(Vp^2 - Vs^2))
```

### Equations

| Modulus | Symbol | Formula | Unit |
|---------|--------|---------|------|
| Bulk | K | rho * (Vp^2 - 4/3 * Vs^2) | GPa |
| Shear | mu | rho * Vs^2 | GPa |
| Young's | E | 9*K*mu / (3*K + mu) | GPa |
| Poisson's | nu | (Vp^2 - 2*Vs^2) / (2*(Vp^2 - Vs^2)) | - |
| Lambda | lam | rho * (Vp^2 - 2*Vs^2) | GPa |

## Velocity-Moduli Relations

### Velocities from Moduli
```python
from bruges.rockphysics import moduli

vp = moduli.vp_from_moduli(K, mu, rho)  # Vp = sqrt((K + 4/3*mu) / rho)
vs = moduli.vs_from_moduli(mu, rho)     # Vs = sqrt(mu / rho)
```

### Vp/Vs Ratio
```python
# For Poisson's ratio nu:
vp_vs = np.sqrt((2 - 2*nu) / (1 - 2*nu))

# Typical values:
# Sandstone (dry): 1.5 - 1.7
# Sandstone (brine): 1.7 - 2.0
# Shale: 1.7 - 2.5
# Carbonate: 1.8 - 2.0
```

## Empirical Relations

### Gardner (Density from Vp)
```python
from bruges.rockphysics import gardner

rho = gardner(vp)  # rho = a * Vp^b (default: a=0.31, b=0.25)
# Input: Vp in m/s
# Output: rho in g/cc
```

### Castagna Mudrock Line (Vs from Vp)
```python
from bruges.rockphysics import castagna

vs = castagna(vp)  # Vs = 0.8621*Vp - 1172 (mudrocks)
# Input: Vp in m/s
# Output: Vs in m/s
```

### Han (Vp from Porosity and Clay)
```python
# Vp = 5.59 - 6.93*phi - 2.18*C  (km/s)
# Where phi = porosity, C = clay fraction
```

### Raymer-Hunt-Gardner (Sonic-Porosity)
```python
# Vp = (1-phi)^2 * Vp_matrix + phi * Vp_fluid
```

## Fluid Substitution

### Gassmann Equation
```python
from bruges.rockphysics import gassmann

vp_new, vs_new, rho_new = gassmann(
    vp_sat, vs_sat, rho_sat,  # Saturated rock properties
    k_min, rho_min,            # Mineral bulk modulus and density
    k_fl1, rho_fl1,            # Original fluid
    k_fl2, rho_fl2,            # New fluid
    phi                        # Porosity
)
```

### Gassmann Assumptions
1. Porous rock is isotropic and homogeneous
2. Pore space is well connected (high permeability)
3. Fluid does not interact with solid (inert)
4. Low frequency (seismic, not ultrasonic)
5. Shear modulus independent of fluid

### Step-by-Step Gassmann
```python
# 1. Calculate dry rock modulus from saturated
K_sat = moduli.bulk(vp_sat, vs_sat, rho_sat)
mu = moduli.shear(vs_sat, rho_sat)

# 2. Calculate dry frame modulus
K_dry = (K_sat * (phi*K_min/K_fl1 + 1 - phi) - K_min) / \
        (phi*K_min/K_fl1 + K_sat/K_min - 1 - phi)

# 3. Substitute new fluid
K_sat_new = K_dry + (1 - K_dry/K_min)^2 / \
            (phi/K_fl2 + (1-phi)/K_min - K_dry/K_min^2)

# 4. New density
rho_new = rho_sat - phi*rho_fl1 + phi*rho_fl2

# 5. New velocities
vp_new = moduli.vp_from_moduli(K_sat_new, mu, rho_new)
vs_new = moduli.vs_from_moduli(mu, rho_new)
```

## Effective Medium Models

### Voigt-Reuss-Hill Average
```python
# Voigt (upper bound): K_v = sum(f_i * K_i)
# Reuss (lower bound): 1/K_r = sum(f_i / K_i)
# Hill (average): K_h = (K_v + K_r) / 2
```

### Hashin-Shtrikman Bounds
```python
# Tighter bounds than Voigt-Reuss for two-phase mixtures
# Used for mineral-pore or mineral-mineral mixtures
```

## Common Mineral Properties

| Mineral | K (GPa) | mu (GPa) | rho (g/cc) |
|---------|---------|----------|------------|
| Quartz | 37 | 44 | 2.65 |
| Calcite | 77 | 32 | 2.71 |
| Dolomite | 95 | 45 | 2.87 |
| Clay | 21 | 7 | 2.60 |
| Feldspar | 38 | 15 | 2.63 |

## Common Fluid Properties

| Fluid | K (GPa) | rho (g/cc) |
|-------|---------|------------|
| Brine (typical) | 2.5 | 1.05 |
| Oil (light) | 0.9 | 0.80 |
| Oil (heavy) | 1.5 | 0.95 |
| Gas (shallow) | 0.02 | 0.10 |
| Gas (deep) | 0.10 | 0.25 |

Note: Fluid properties vary significantly with pressure, temperature, and composition. Use Batzle-Wang equations for accurate values.

## Batzle-Wang Fluid Properties

```python
# For accurate fluid properties at reservoir conditions:
# K_brine = f(T, P, salinity)
# K_oil = f(T, P, API gravity, GOR)
# K_gas = f(T, P, gas gravity)
```
