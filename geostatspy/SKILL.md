---
name: geostatspy
description: Geostatistics in Python. GSLIB-inspired library for variogram analysis, kriging, and geostatistical simulation for spatial data analysis.
---

# GeostatsPy - Geostatistical Analysis

Help users perform variogram analysis, kriging, and geostatistical simulation.

## Installation

```bash
pip install geostatspy
```

## Core Concepts

### Geostatistics Workflow
1. **Exploratory Data Analysis** - Statistics, histograms, spatial plots
2. **Variogram Analysis** - Model spatial correlation
3. **Estimation** - Kriging for optimal predictions
4. **Simulation** - Generate realizations with uncertainty

### Key Functions
| Category | Functions |
|----------|-----------|
| Visualization | `locmap`, `pixelplt`, `hist` |
| Variogram | `gamv`, `vmodel` |
| Kriging | `kb2d`, `kb3d` |
| Simulation | `sgsim`, `sisim` |
| Transforms | `nscore`, `backtr` |

## Common Workflows

### 1. Load and Explore Data
```python
import geostatspy.GSLIB as GSLIB
import geostatspy.geostats as geostats
import pandas as pd
import numpy as np

# Load data
df = pd.read_csv('data.csv')

# Basic statistics
print(df['porosity'].describe())

# Location map
GSLIB.locmap(
    df, 'X', 'Y', 'porosity',
    xmin=0, xmax=1000, ymin=0, ymax=1000,
    vmin=0.05, vmax=0.25,
    title='Porosity'
)

# Histogram
GSLIB.hist(
    df['porosity'],
    xmin=0, xmax=0.3,
    log=False,
    cumul=False,
    bins=30,
    xlabel='Porosity',
    title='Porosity Distribution'
)
```

### 2. Normal Score Transform
```python
# Transform to Gaussian distribution
df['npor'], tvpor, tnspor = geostats.nscore(df, 'porosity')

# Check transform
GSLIB.hist(df['npor'], xlabel='Normal Score Porosity')
```

### 3. Calculate Experimental Variogram
```python
# 2D variogram
lag_dist = 50      # Lag distance
lag_tol = 25       # Lag tolerance
n_lags = 15        # Number of lags
azimuth = 0        # Direction (0 = N-S)
atol = 22.5        # Angular tolerance
bandh = 9999       # Horizontal bandwidth

# Calculate variogram
lag, gamma, npairs = geostats.gamv(
    df, 'X', 'Y', 'npor',
    tmin=-9999, tmax=9999,
    xlag=lag_dist, xltol=lag_tol,
    nlag=n_lags,
    azm=azimuth, atol=atol,
    bandwh=bandh, bandwd=bandh
)

# Plot variogram
import matplotlib.pyplot as plt
plt.plot(lag, gamma, 'o-')
plt.xlabel('Lag Distance')
plt.ylabel('Semivariance')
plt.title('Experimental Variogram')
```

### 4. Fit Variogram Model
```python
# Define variogram model parameters
nug = 0.0          # Nugget
nst = 1            # Number of structures
it = 1             # Structure type (1=spherical, 2=exponential, 3=gaussian)
cc = 1.0           # Sill contribution
azm = 0            # Azimuth
hmaj = 300         # Major range
hmin = 300         # Minor range (isotropic if = hmaj)

# Create model
vario_model = GSLIB.make_variogram(
    nug=nug, nst=nst,
    it1=it, cc1=cc, azi1=azm, hmaj1=hmaj, hmin1=hmin
)

# Plot model against experimental
lag_model = np.linspace(0, 500, 100)
gamma_model = geostats.vmodel(
    lag_model,
    nug, nst,
    [it], [cc], [azm], [hmaj], [hmin]
)

plt.plot(lag, gamma, 'o', label='Experimental')
plt.plot(lag_model, gamma_model, '-', label='Model')
plt.legend()
```

### 5. Simple Kriging
```python
# Grid parameters
xmin, xmax = 0, 1000
ymin, ymax = 0, 1000
nx, ny = 50, 50
xsize = (xmax - xmin) / nx
ysize = (ymax - ymin) / ny

# Kriging parameters
ndmin = 1          # Min data points
ndmax = 10         # Max data points
radius = 500       # Search radius

# Simple kriging
krig_est, krig_var = geostats.kb2d(
    df, 'X', 'Y', 'npor',
    tmin=-9999, tmax=9999,
    nx=nx, xmn=xmin+xsize/2, xsiz=xsize,
    ny=ny, ymn=ymin+ysize/2, ysiz=ysize,
    nxdis=1, nydis=1,
    ndmin=ndmin, ndmax=ndmax,
    radius=radius,
    ktype=0,  # 0=simple, 1=ordinary
    skmean=0.0,  # Mean for simple kriging
    vario=vario_model
)

# Plot results
GSLIB.pixelplt(
    krig_est,
    xmin, xmax, ymin, ymax,
    nx, xsize, ny, ysize,
    title='Kriging Estimate',
    xlabel='X', ylabel='Y'
)
```

### 6. Ordinary Kriging
```python
# Ordinary kriging (unknown mean)
krig_est, krig_var = geostats.kb2d(
    df, 'X', 'Y', 'npor',
    tmin=-9999, tmax=9999,
    nx=nx, xmn=xmin+xsize/2, xsiz=xsize,
    ny=ny, ymn=ymin+ysize/2, ysiz=ysize,
    nxdis=1, nydis=1,
    ndmin=ndmin, ndmax=ndmax,
    radius=radius,
    ktype=1,  # Ordinary kriging
    skmean=0.0,
    vario=vario_model
)
```

### 7. Sequential Gaussian Simulation
```python
# SGSIM parameters
seed = 73073

# Run simulation
sim = geostats.sgsim(
    df, 'X', 'Y', 'npor',
    wcol=-1, scol=-1,  # No secondary variable
    tmin=-9999, tmax=9999,
    itrans=0,  # Already transformed
    ismooth=0,
    dession=0, dmession=0,
    zmin=-4, zmax=4,
    ltail=1, ltpar=0,
    utail=1, utpar=0,
    nsim=1,  # Number of realizations
    nx=nx, xmn=xmin+xsize/2, xsiz=xsize,
    ny=ny, ymn=ymin+ysize/2, ysiz=ysize,
    nz=1, zmn=0, zsiz=1,
    seed=seed,
    ndmin=ndmin, ndmax=ndmax,
    nodmax=10,
    radius=radius, radius1=radius,
    sang1=0, sang2=0, sang3=0,
    mxctx=10, mxcty=10, mxctz=1,
    ktype=0,
    vario=vario_model
)

# Back-transform to original units
sim_bt = geostats.backtr(sim.flatten(), tvpor, tnspor, zmin=0, zmax=0.3)
sim_bt = sim_bt.reshape(sim.shape)
```

### 8. Multiple Realizations
```python
n_realizations = 100
simulations = []

for i in range(n_realizations):
    sim = geostats.sgsim(
        df, 'X', 'Y', 'npor',
        # ... parameters ...
        nsim=1,
        seed=seed + i,
        # ... more parameters ...
    )
    simulations.append(sim)

simulations = np.array(simulations)

# Calculate statistics
mean_map = simulations.mean(axis=0)
std_map = simulations.std(axis=0)
p10_map = np.percentile(simulations, 10, axis=0)
p90_map = np.percentile(simulations, 90, axis=0)
```

### 9. Declustering
```python
# Cell declustering
wts, cell_size, ncut = geostats.declus(
    df, 'X', 'Y', 'porosity',
    iminmax=1,  # 1=minimize mean
    noff=10,
    ncell=20,
    cmin=10, cmax=500
)

# Declustered statistics
print(f"Naive mean: {df['porosity'].mean():.4f}")
print(f"Declustered mean: {np.average(df['porosity'], weights=wts):.4f}")
```

### 10. Indicator Kriging
```python
# Threshold for indicator transform
threshold = 0.15
df['ind'] = (df['porosity'] > threshold).astype(float)

# Indicator variogram and kriging
lag, gamma_ind, npairs = geostats.gamv(
    df, 'X', 'Y', 'ind',
    # ... parameters ...
)

# Indicator kriging gives probability
prob_est, prob_var = geostats.kb2d(
    df, 'X', 'Y', 'ind',
    # ... parameters ...
)
```

## Variogram Models

| Code | Model | Description |
|------|-------|-------------|
| 1 | Spherical | Most common, finite range |
| 2 | Exponential | Reaches sill asymptotically |
| 3 | Gaussian | Very smooth, parabolic near origin |
| 4 | Power | Unbounded, fractal-like |

## Tips

1. **Always check data distribution** - Transform if needed
2. **Use normal scores** - Many methods assume Gaussian
3. **Validate variograms** - Check against theory and cross-validation
4. **Start isotropic** - Add anisotropy if justified
5. **Multiple realizations** - Assess uncertainty properly

## Common Parameters

| Parameter | Description |
|-----------|-------------|
| `nug` | Nugget effect (measurement error + micro-scale variation) |
| `sill` | Total variance (nugget + structure contributions) |
| `range` | Distance at which correlation becomes negligible |
| `azimuth` | Direction of maximum continuity |

## Resources

- GitHub: https://github.com/GeostatsGuy/GeostatsPy
- GSLIB Book: Deutsch & Journel (1998)
- Tutorials: https://github.com/GeostatsGuy/PythonNumericalDemos
- PyGSLIB: Alternative implementation
