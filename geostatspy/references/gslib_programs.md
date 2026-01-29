# GSLIB Programs Reference

GeostatsPy implements key programs from GSLIB (Geostatistical Software Library).

## Table of Contents
- [Data Analysis](#data-analysis)
- [Variogram Programs](#variogram-programs)
- [Estimation Programs](#estimation-programs)
- [Simulation Programs](#simulation-programs)
- [Utility Programs](#utility-programs)

## Data Analysis

### HISTPLT - Histogram Plot
```python
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

### LOCMAP - Location Map
```python
GSLIB.locmap(
    df, 'X', 'Y', 'porosity',
    xmin=0, xmax=1000, ymin=0, ymax=1000,
    vmin=0.05, vmax=0.25,
    title='Porosity Map',
    vlabel='Porosity (v/v)'
)
```

### PIXELPLT - Pixel Plot for Grids
```python
GSLIB.pixelplt(
    grid_data,
    xmin, xmax, ymin, ymax,
    nx, xsiz, ny, ysiz,
    title='Kriging Estimate',
    xlabel='X', ylabel='Y',
    vlabel='Porosity'
)
```

## Variogram Programs

### GAMV - Experimental Variogram
Calculates experimental semivariogram from irregularly spaced data.

```python
lag, gamma, npairs = geostats.gamv(
    df, 'X', 'Y', 'npor',
    tmin=-9999, tmax=9999,    # Trimming limits
    xlag=50,                   # Lag distance
    xltol=25,                  # Lag tolerance (usually 0.5 * xlag)
    nlag=15,                   # Number of lags
    azm=0,                     # Azimuth (0=N, 90=E)
    atol=22.5,                 # Angular tolerance
    bandwh=9999,               # Horizontal bandwidth
    bandwd=9999                # Vertical bandwidth
)
```

**Parameters:**
| Parameter | Description | Typical Value |
|-----------|-------------|---------------|
| `xlag` | Lag spacing | Data spacing |
| `xltol` | Lag tolerance | 0.5 * xlag |
| `nlag` | Number of lags | 10-20 |
| `azm` | Direction | 0, 45, 90, 135 |
| `atol` | Angular tolerance | 22.5 for 4 dirs |
| `bandwh` | Horizontal bandwidth | 9999 (large) |

### VMODEL - Variogram Model
Evaluates variogram model at specified lags.

```python
gamma_model = geostats.vmodel(
    lags,              # Array of lag distances
    nug,               # Nugget
    nst,               # Number of structures
    [it1, it2],        # Structure types
    [cc1, cc2],        # Sill contributions
    [azi1, azi2],      # Azimuths
    [hmaj1, hmaj2],    # Major ranges
    [hmin1, hmin2]     # Minor ranges
)
```

### MAKE_VARIOGRAM - Create Variogram Model
```python
# Single structure (isotropic spherical)
vario = GSLIB.make_variogram(
    nug=0.0,           # Nugget
    nst=1,             # Number of structures
    it1=1,             # Type: 1=sph, 2=exp, 3=gaus
    cc1=1.0,           # Sill contribution
    azi1=0,            # Azimuth
    hmaj1=300,         # Major range
    hmin1=300          # Minor range
)

# Nested structures (nugget + 2 structures)
vario = GSLIB.make_variogram(
    nug=0.1,
    nst=2,
    it1=1, cc1=0.4, azi1=45, hmaj1=100, hmin1=50,
    it2=1, cc2=0.5, azi2=45, hmaj2=400, hmin2=200
)
```

## Estimation Programs

### KB2D - 2D Kriging
Simple or ordinary kriging on a 2D grid.

```python
est, var = geostats.kb2d(
    df, 'X', 'Y', 'npor',
    tmin=-9999, tmax=9999,    # Trimming limits
    nx=50, xmn=25, xsiz=50,   # Grid X: ncells, origin, cell size
    ny=50, ymn=25, ysiz=50,   # Grid Y: ncells, origin, cell size
    nxdis=1, nydis=1,         # Block discretization
    ndmin=1,                   # Minimum data points
    ndmax=10,                  # Maximum data points
    radius=500,                # Search radius
    ktype=0,                   # 0=simple, 1=ordinary
    skmean=0.0,               # Mean for simple kriging
    vario=vario
)
```

**Kriging Types:**
| ktype | Method | When to Use |
|-------|--------|-------------|
| 0 | Simple Kriging | Known stationary mean |
| 1 | Ordinary Kriging | Unknown local mean |

### KB3D - 3D Kriging
Extension to 3D grids with additional z-parameters.

```python
est, var = geostats.kb3d(
    df, 'X', 'Y', 'Z', 'npor',
    # ... similar parameters plus z-grid specs
    nz=20, zmn=5, zsiz=10,
    # ... and vertical search
    radius_vert=50
)
```

## Simulation Programs

### SGSIM - Sequential Gaussian Simulation
Generates conditional realizations honoring data and variogram.

```python
sim = geostats.sgsim(
    df, 'X', 'Y', 'npor',
    wcol=-1, scol=-1,          # Weight/secondary columns (-1=none)
    tmin=-9999, tmax=9999,     # Trimming limits
    itrans=0,                   # 0=already transformed, 1=transform
    ismooth=0,                  # Smoothing flag
    dession=0, dmession=0,      # Debugging
    zmin=-4, zmax=4,           # Min/max for transformation
    ltail=1, ltpar=0,          # Lower tail: 1=linear
    utail=1, utpar=0,          # Upper tail: 1=linear
    nsim=1,                     # Number of realizations
    nx=50, xmn=25, xsiz=50,
    ny=50, ymn=25, ysiz=50,
    nz=1, zmn=0, zsiz=1,
    seed=73073,                 # Random seed
    ndmin=1, ndmax=10,         # Min/max conditioning data
    nodmax=10,                  # Max previously simulated nodes
    radius=500, radius1=500,   # Search radii
    sang1=0, sang2=0, sang3=0, # Search angles
    mxctx=10, mxcty=10, mxctz=1,  # Covariance lookup
    ktype=0,                    # Kriging type
    vario=vario
)
```

### SISIM - Sequential Indicator Simulation
For categorical variables or multiple cutoffs.

```python
# Define thresholds and indicator variograms
thresholds = [0.10, 0.15, 0.20]  # Porosity cutoffs
# Each threshold needs its own indicator variogram
```

## Utility Programs

### NSCORE - Normal Score Transform
```python
df['npor'], tvpor, tnspor = geostats.nscore(df, 'porosity')
# tvpor: original values (sorted)
# tnspor: normal scores (sorted)
```

### BACKTR - Back Transform
```python
original = geostats.backtr(
    nscore_data,       # Normal score values
    tvpor,             # Original values from nscore
    tnspor,            # Normal scores from nscore
    zmin=0.0,          # Minimum allowed value
    zmax=0.35          # Maximum allowed value
)
```

### DECLUS - Declustering
```python
wts, cell_size, ncut = geostats.declus(
    df, 'X', 'Y', 'porosity',
    iminmax=1,         # 1=minimize, 2=maximize mean
    noff=10,           # Number of offsets
    ncell=20,          # Number of cell sizes to try
    cmin=10,           # Minimum cell size
    cmax=500           # Maximum cell size
)
```

## Variogram Model Types

| Code | Name | Formula | Range Behavior |
|------|------|---------|----------------|
| 1 | Spherical | 1.5(h/a) - 0.5(h/a)^3 | Finite at a |
| 2 | Exponential | 1 - exp(-3h/a) | Practical at a |
| 3 | Gaussian | 1 - exp(-3(h/a)^2) | Practical at a |
| 4 | Power | (h)^w | Unbounded |

## Common Workflows

### Omnidirectional Variogram
```python
lag, gamma, npairs = geostats.gamv(
    df, 'X', 'Y', 'npor',
    xlag=50, xltol=25, nlag=15,
    azm=0, atol=90,        # 90 degree tolerance = omnidirectional
    bandwh=9999, bandwd=9999
)
```

### Directional Variograms (4 directions)
```python
directions = [0, 45, 90, 135]  # N-S, NE-SW, E-W, NW-SE
variograms = {}

for azm in directions:
    lag, gamma, npairs = geostats.gamv(
        df, 'X', 'Y', 'npor',
        xlag=50, xltol=25, nlag=15,
        azm=azm, atol=22.5,    # 22.5 for 4 directions
        bandwh=9999, bandwd=9999
    )
    variograms[azm] = (lag, gamma, npairs)
```

### Cross-Validation
```python
# Leave-one-out cross-validation
errors = []
for i in range(len(df)):
    train = df.drop(i)
    test_x, test_y = df.iloc[i]['X'], df.iloc[i]['Y']
    test_val = df.iloc[i]['npor']

    # Krige at test location
    est, var = geostats.kb2d(train, 'X', 'Y', 'npor', ...)

    # Find estimate at test location
    # Compare with test_val
```
