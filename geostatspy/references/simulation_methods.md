# Geostatistical Simulation Methods

## Table of Contents
- [Overview](#overview)
- [Sequential Gaussian Simulation (SGSIM)](#sequential-gaussian-simulation-sgsim)
- [Sequential Indicator Simulation (SISIM)](#sequential-indicator-simulation-sisim)
- [Multiple Realizations](#multiple-realizations)
- [Post-Processing](#post-processing)
- [Best Practices](#best-practices)

## Overview

Simulation generates multiple equiprobable realizations that:
- Honor the conditioning data exactly
- Reproduce the variogram model
- Capture spatial uncertainty

**Kriging vs Simulation:**
| Aspect | Kriging | Simulation |
|--------|---------|------------|
| Output | Single estimate | Multiple realizations |
| Smoothing | Yes (variance reduction) | No (full variance) |
| Uncertainty | Kriging variance | Ensemble statistics |
| Use case | Best estimate | Risk assessment |

## Sequential Gaussian Simulation (SGSIM)

### Algorithm Steps
1. Transform data to normal scores
2. Define a random path through all grid nodes
3. At each node:
   - Find nearby conditioning data and previously simulated nodes
   - Perform simple kriging
   - Draw from conditional distribution N(SK estimate, SK variance)
   - Add simulated value to conditioning set
4. Back-transform to original units

### Basic SGSIM
```python
import geostatspy.GSLIB as GSLIB
import geostatspy.geostats as geostats
import numpy as np

# Normal score transform
df['npor'], tvpor, tnspor = geostats.nscore(df, 'porosity')

# Variogram model
vario = GSLIB.make_variogram(nug=0.0, nst=1, it1=1, cc1=1.0,
                              azi1=0, hmaj1=300, hmin1=300)

# Single realization
sim = geostats.sgsim(
    df, 'X', 'Y', 'npor',
    wcol=-1, scol=-1,
    tmin=-9999, tmax=9999,
    itrans=0,              # Data already transformed
    ismooth=0,
    dession=0, dmession=0,
    zmin=-4, zmax=4,
    ltail=1, ltpar=0,
    utail=1, utpar=0,
    nsim=1,
    nx=50, xmn=25, xsiz=50,
    ny=50, ymn=25, ysiz=50,
    nz=1, zmn=0, zsiz=1,
    seed=73073,
    ndmin=1, ndmax=10,
    nodmax=10,
    radius=500, radius1=500,
    sang1=0, sang2=0, sang3=0,
    mxctx=10, mxcty=10, mxctz=1,
    ktype=0,
    vario=vario
)

# Back-transform
sim_original = geostats.backtr(sim.flatten(), tvpor, tnspor,
                                zmin=0.0, zmax=0.35)
sim_original = sim_original.reshape(sim.shape)
```

### Key Parameters

| Parameter | Description | Guidance |
|-----------|-------------|----------|
| `itrans` | Transform flag | 0 if pre-transformed, 1 to transform |
| `nsim` | Number of realizations | 1 per call, loop for multiple |
| `seed` | Random seed | Change for each realization |
| `ndmax` | Max conditioning data | 10-20 typically |
| `nodmax` | Max simulated nodes | 10-20 typically |
| `radius` | Search radius | > variogram range |
| `mxctx/y/z` | Covariance lookup | 10 usually sufficient |

### Tail Extrapolation
Controls behavior beyond data range:

| ltail/utail | Meaning |
|-------------|---------|
| 1 | Linear extrapolation |
| 2 | Power model |
| 4 | Hyperbolic |

```python
# Conservative tails (recommended)
ltail=1, ltpar=0,  # Linear lower tail
utail=1, utpar=0   # Linear upper tail
```

## Sequential Indicator Simulation (SISIM)

For categorical variables or non-Gaussian distributions.

### Indicator Transform
```python
# Single threshold
threshold = 0.15
df['ind'] = (df['porosity'] > threshold).astype(float)

# Multiple thresholds
thresholds = [0.08, 0.12, 0.16, 0.20]
for i, t in enumerate(thresholds):
    df[f'ind_{i}'] = (df['porosity'] > t).astype(float)
```

### Indicator Variograms
Each threshold needs its own variogram:
```python
ind_varios = []
for i, t in enumerate(thresholds):
    # Calculate indicator variogram
    lag, gamma, npairs = geostats.gamv(
        df, 'X', 'Y', f'ind_{i}',
        xlag=50, xltol=25, nlag=15,
        azm=0, atol=90, bandwh=9999, bandwd=9999
    )

    # Fit model
    vario = GSLIB.make_variogram(nug=0.05, nst=1, it1=1,
                                  cc1=0.2, azi1=0, hmaj1=200, hmin1=200)
    ind_varios.append(vario)
```

### Facies Simulation
```python
# For categorical facies (sand, shale, limestone)
# 1. Define indicator for each facies
# 2. Calculate indicator variogram for each
# 3. Run SISIM
# 4. Post-process to ensure single facies per cell
```

## Multiple Realizations

### Generating Ensemble
```python
n_realizations = 100
simulations = []

for i in range(n_realizations):
    sim = geostats.sgsim(
        df, 'X', 'Y', 'npor',
        wcol=-1, scol=-1,
        tmin=-9999, tmax=9999,
        itrans=0, ismooth=0,
        dession=0, dmession=0,
        zmin=-4, zmax=4,
        ltail=1, ltpar=0,
        utail=1, utpar=0,
        nsim=1,
        nx=50, xmn=25, xsiz=50,
        ny=50, ymn=25, ysiz=50,
        nz=1, zmn=0, zsiz=1,
        seed=73073 + i,        # Different seed each time
        ndmin=1, ndmax=10,
        nodmax=10,
        radius=500, radius1=500,
        sang1=0, sang2=0, sang3=0,
        mxctx=10, mxcty=10, mxctz=1,
        ktype=0,
        vario=vario
    )

    # Back-transform
    sim_bt = geostats.backtr(sim.flatten(), tvpor, tnspor,
                              zmin=0.0, zmax=0.35)
    simulations.append(sim_bt.reshape(sim.shape))

simulations = np.array(simulations)  # Shape: (n_real, ny, nx)
```

### Ensemble Statistics
```python
# E-type estimate (mean)
e_type = simulations.mean(axis=0)

# Standard deviation (uncertainty)
std_map = simulations.std(axis=0)

# Percentiles
p10 = np.percentile(simulations, 10, axis=0)
p50 = np.percentile(simulations, 50, axis=0)
p90 = np.percentile(simulations, 90, axis=0)

# Probability above threshold
prob_high = (simulations > 0.15).mean(axis=0)
```

## Post-Processing

### Checking Reproduction

#### Histogram Reproduction
```python
# Compare histogram of simulations to input data
all_sim_values = simulations.flatten()

plt.figure(figsize=(10, 4))
plt.subplot(1, 2, 1)
plt.hist(df['porosity'], bins=30, density=True, alpha=0.7, label='Data')
plt.subplot(1, 2, 2)
plt.hist(all_sim_values, bins=30, density=True, alpha=0.7, label='Simulations')
```

#### Variogram Reproduction
```python
# Calculate variogram from one realization
# Compare to input variogram model
```

### Volume Calculations
```python
# Calculate connected volumes, reserves, etc.
cell_volume = xsiz * ysiz * zsiz  # Cell volume in appropriate units

# Total pore volume per realization
pore_volumes = []
for sim in simulations:
    pore_vol = np.sum(sim * cell_volume)
    pore_volumes.append(pore_vol)

# Statistics
mean_pv = np.mean(pore_volumes)
p10_pv = np.percentile(pore_volumes, 10)
p90_pv = np.percentile(pore_volumes, 90)
```

## Best Practices

### Data Preparation
1. **Quality control** - Remove outliers, check coordinates
2. **Decluster** - Weight clustered data appropriately
3. **Transform** - Use normal scores for SGSIM
4. **Check stationarity** - Verify mean/variance don't trend

### Variogram Modeling
1. **Start omnidirectional** - Get overall structure
2. **Check anisotropy** - Compare directional variograms
3. **Ensure positive definiteness** - Use valid model combinations
4. **Match sill to variance** - Sill should equal data variance

### Simulation Settings
1. **Search radius > range** - Ensure proper conditioning
2. **Enough realizations** - 50-100 minimum for uncertainty
3. **Different seeds** - Each realization needs unique seed
4. **Check reproduction** - Validate histogram and variogram

### Common Issues

| Issue | Cause | Solution |
|-------|-------|----------|
| Artifacts | Search too small | Increase radius |
| Wrong variance | Bad back-transform | Check zmin/zmax |
| Trends | Non-stationarity | Detrend first |
| Bull's eyes | Nugget effect | Verify nugget in model |

### Memory Management
```python
# For large models, process in batches
batch_size = 10
for batch_start in range(0, n_realizations, batch_size):
    batch_end = min(batch_start + batch_size, n_realizations)

    # Generate batch
    batch_sims = []
    for i in range(batch_start, batch_end):
        sim = geostats.sgsim(...)
        batch_sims.append(sim)

    # Process and save batch
    np.save(f'sims_{batch_start}_{batch_end}.npy', np.array(batch_sims))
```
