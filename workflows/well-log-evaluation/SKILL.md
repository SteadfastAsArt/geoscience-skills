---
name: well-log-evaluation
description: |
  Complete well log evaluation workflow from LAS/DLIS loading through QC,
  petrophysical analysis, lithology classification, and visualization.
  Use when performing formation evaluation from well log data.
license: MIT
metadata:
  skill_type: workflow
  version: 1.0.2
  author: Geoscience Skills
  tags: '["Well Logs", "Petrophysics", "LAS", "DLIS", "Formation Evaluation", "Workflow"]'
  dependencies: '["lasio", "numpy", "pandas", "welly", "setuptools<81", "petropy", "striplog", "pyvista"]'
  complements: '["lasio", "dlisio", "welly", "petropy", "striplog", "pyvista"]'
  workflow_role: analysis
---

# Well Log Evaluation Workflow

End-to-end pipeline for formation evaluation, from loading well log files
through quality control, petrophysical analysis, lithology classification,
and multi-dimensional visualization.

## Skill Chain

```text
lasio/dlisio     welly           petropy         striplog        pyvista
[File I/O]   --> [QC & Prep]  --> [Petrophysics] --> [Lithology] --> [3D Viz]
  |               |                |                 |               |
  LAS parsing     Despike          Vshale calc       Facies log      3D well
  DLIS frames     Normalize        Porosity          Intervals       Fence diagram
  Curve extract   Merge curves     Sw, Perm          Correlation     Property vol
```

## Decision Points

| Question | If Yes | If No |
|----------|--------|-------|
| LAS format (.las)? | Use `lasio` for loading | Check DLIS format |
| DLIS format (.dlis)? | Use `dlisio` for loading | Check file type |
| Multiple wells or curve QC needed? | Use `welly` for management | Use lasio directly |
| Full formation evaluation (Sw, phi, Vsh)? | Use `petropy` | Compute manually with numpy |
| Need lithology column or stratigraphic log? | Use `striplog` | Skip to visualization |
| 3D well trajectory visualization? | Use `pyvista` | Use matplotlib for log plots |

## Step-by-Step Orchestration

### Stage 1: Data Loading (lasio / dlisio)

The LAS example below assumes depth in metres, GR in API, bulk density in
g/cm³, and resistivity in ohm-m. Inspect the headers and convert other units
before continuing. The DLIS block is an alternative inspection entrypoint;
select a frame, map mnemonics, and supply the same units before Stage 2.

```python
import lasio
import numpy as np
import pandas as pd

# Load LAS file
las = lasio.read('well_A.las')
df = las.df().rename_axis('DEPT').reset_index()
null_val = float(las.well['NULL'].value)
df = df.replace(null_val, np.nan)
if las.curves[0].unit.strip().lower() not in {'m', 'metre', 'meter'}:
    raise ValueError('Convert the depth basis to metres before this example')
if (len(df) < 2 or not np.isfinite(df['DEPT']).all()
        or not np.all(np.diff(df['DEPT']) > 0)):
    raise ValueError('QC the depth basis: require finite, strictly increasing samples')

# Inspect available curves
print(las.curves.keys())  # ['DEPT', 'GR', 'RHOB', 'NPHI', 'RT', 'DT']
well_name = las.well['WELL'].value
```

```python
import dlisio

# Load DLIS file (for modern well data)
with dlisio.dlis.load('well_B.dlis') as files:
    f = files[0]
    for frame in f.frames:
        print(frame.name, [ch.name for ch in frame.channels])
    # Extract channels to numpy arrays
    frame = f.frames[0]
    depth = frame.channels[0].curves()
    gr = frame.channels[1].curves()
```

### Stage 2: QC and Preparation (welly)

```python
from welly import Well

# Build from Stage 1's validated/converted dataframe so edits are retained.
w = Well.from_df(df.set_index('DEPT'),
                 units={'GR': 'API', 'RHOB': 'g/cm3', 'RT': 'ohm-m'})

required = ['GR', 'RHOB', 'RT']  # NPHI is optional for this density-only example.
missing = set(required) - set(w.data)
if missing:
    raise ValueError(f'Missing required curves: {sorted(missing)}')

# Review the despiking parameters against real beds; retain GR in API units.
# despike returns a new Curve, so explicitly use it for subsequent resampling.
w.data['GR'] = w.data['GR'].despike(window_length=33, z=2.0)

# Sample only the common measured depth range; do not extrapolate edge values.
step_m = 0.5
start = max(w.data[key].start for key in required)
stop = min(w.data[key].stop for key in required)
if not np.isfinite([start, stop]).all() or stop <= start:
    raise ValueError('Curves need an overlapping, increasing depth range')
basis = start + np.arange(int(np.floor((stop - start) / step_m)) + 1) * step_m
if len(basis) < 2:
    raise ValueError('Need at least two samples on the target depth basis')
df = w.df(keys=required, basis=basis).replace([np.inf, -np.inf], np.nan)
df = df.rename_axis('DEPT').reset_index()

# Keep missing rows so later classification cannot bridge unlogged intervals.
df['QC_VALID'] = (np.isfinite(df[required]).all(axis=1)
                  & (df['RHOB'] > 0) & (df['RT'] > 0))
```

The [welly Curve guide](https://code.agilescientific.com/welly/userguide/Curves.html)
describes despiking and resampling. These snippets are tested with welly 0.5.2
and pandas 2.3.3; welly 0.5.2 also requires `setuptools<81` for `pkg_resources`.

### Stage 3: Petrophysical Analysis

This runnable calculation uses the **QC dataframe from Stage 2**. The sand/shale
GR endpoints, fluid density, Rw at formation temperature, and Archie parameters
below are illustrative inputs requiring local calibration. Archie applies to
clean formations; use an appropriate shale-aware model for shaly intervals.
For a PetroPy multimineral model, first export the QC curves and configure
formation tops, fluid properties, and model parameters; follow the
[PetroPy API](https://toddheitmann.github.io/PetroPy/class/Log.html).

```python
valid = df['QC_VALID'].to_numpy(dtype=bool)
gr_sand, gr_shale = 20.0, 120.0  # API, calibrated endpoints (example values)
if not np.isfinite([gr_sand, gr_shale]).all() or gr_shale <= gr_sand:
    raise ValueError('GR endpoints must be finite with shale > sand')
vshale = np.where(valid, np.clip((df['GR'] - gr_sand) / (gr_shale - gr_sand), 0, 1), np.nan)

# 2. Porosity from density log
rho_matrix = 2.65   # g/cc (quartz)
rho_fluid = 1.0     # g/cc (freshwater)
phi_density = (rho_matrix - df['RHOB']) / (rho_matrix - rho_fluid)
phi_density = phi_density.where(valid & phi_density.between(0, 1))

# 3. Water saturation (Archie equation)
a, m, n = 1.0, 2.0, 2.0  # Archie parameters
Rw = 0.05                  # Formation water resistivity (ohm-m)
Rt = df['RT'].values       # True resistivity
phi = phi_density.values
Sw_raw = np.full(len(df), np.nan)
usable = valid & np.isfinite(phi) & (phi > 0)
Sw_raw[usable] = ((a * Rw) / (phi[usable]**m * Rt[usable]))**(1/n)
Sw = np.clip(Sw_raw, 0, 1)
df['VSH'], df['PHI_D'], df['SW'] = vshale, phi_density, Sw
df['SW_CLIPPED'] = Sw_raw > 1  # Retain a flag to review model/input mismatch.
df.to_csv('well_A_evaluated.csv', index=False)
```

Estimate permeability only with a calibrated model and its required inputs
(for example, irreducible water saturation or NMR bound/free-fluid volumes).
The Archie saturation above is not automatically irreducible saturation.

### Stage 4: Lithology Classification (striplog)

```python
from striplog import Striplog, Component, Interval

# Build lithology log from Vshale cutoffs
intervals = []
depth = df['DEPT'].values
for i in range(len(depth) - 1):
    if not np.isfinite(vshale[i:i+2]).all():
        continue  # Preserve gaps; do not invent a lithology across missing data.
    if vshale[i] < 0.3:
        lith = Component({'lithology': 'sandstone'})
    elif vshale[i] < 0.6:
        lith = Component({'lithology': 'siltstone'})
    else:
        lith = Component({'lithology': 'shale'})
    intervals.append(Interval(top=depth[i], base=depth[i+1], components=[lith]))

if not intervals:
    raise ValueError('No adjacent valid samples for lithology intervals')
strip = Striplog(intervals).merge_neighbours()
```

Optional display:

```python
strip.plot(aspect=10)
```

### Stage 5: Visualization (pyvista)

Use a surveyed trajectory with `MD_M`, `X_M`, `Y_M`, and `TVDSS_M` columns in
`trajectory.csv`; MD must use the same datum as the logs. X/Y use a documented
projected CRS in metres, and TVDSS is positive down from the stated vertical
datum. Measured depth is not vertical depth in a deviated well.

```python
import pyvista as pv

# Interpolate surveyed coordinates onto the evaluated log sample depths.
survey = pd.read_csv('trajectory.csv')
md = survey['MD_M'].to_numpy()
if (len(md) < 2 or not np.isfinite(survey[['MD_M', 'X_M', 'Y_M', 'TVDSS_M']]).all().all()
        or not np.all(np.diff(md) > 0)):
    raise ValueError('Survey coordinates must be finite with increasing MD')
depth = df['DEPT'].to_numpy()
if depth.min() < md[0] or depth.max() > md[-1]:
    raise ValueError('Survey must cover the log depth range')
trajectory = np.column_stack([
    np.interp(depth, md, survey['X_M']),
    np.interp(depth, md, survey['Y_M']),
    -np.interp(depth, md, survey['TVDSS_M']),
])
well_path = pv.lines_from_points(trajectory)  # Keep one point per log sample.
well_path['GR'] = df['GR'].values
well_path['Porosity'] = phi_density.values
```

Optional interactive display:

```python
plotter = pv.Plotter()
plotter.add_mesh(well_path, scalars='Porosity', cmap='viridis',
                 line_width=5, render_lines_as_tubes=True)
plotter.show()
```

## Common Pipelines

### Standard Formation Evaluation
```text
- [ ] Load LAS file with `lasio.read()`, replace null values with NaN
- [ ] Inspect GR, RHOB and RT for this example; add NPHI or DT for models that require them
- [ ] QC curves with welly: despike, check ranges, identify washouts (caliper)
- [ ] Calculate Vshale from GR (linear, Larionov, or Clavier method)
- [ ] Calculate porosity from density or neutron-density crossplot
- [ ] Calculate water saturation using Archie or dual-water model
- [ ] Estimate permeability from Timur-Coates or Wyllie-Rose
- [ ] Flag pay zones: phi > cutoff, Sw < cutoff, Vsh < cutoff
- [ ] Generate composite log plot (GR, resistivity, porosity, Sw, pay flag)
- [ ] Export results to LAS or CSV
```

### Multi-Well Correlation
```text
- [ ] Load multiple LAS files with lasio or welly batch loading
- [ ] Standardize curve mnemonics across wells (GR, GRGC, SGR -> GR)
- [ ] Normalize GR logs to common scale across wells
- [ ] Pick formation tops manually or from Vshale transitions
- [ ] Create striplog for each well with formation intervals
- [ ] Build correlation panel with matplotlib or pyvista
- [ ] Export formation tops to CSV
```

### Quick Log QC
```text
- [ ] Load LAS file with `lasio.read()`
- [ ] Check depth range, step, and null values
- [ ] Print curve statistics: min, max, mean, NaN count
- [ ] Flag out-of-range values (GR: 0-300, RHOB: 1.5-3.0, NPHI: -0.05-0.6)
- [ ] Check for constant or stuck readings
- [ ] Identify depth intervals with poor data (washout from caliper)
- [ ] Plot all curves for visual inspection
```

## When to Use

Use the well log evaluation workflow when:

- Performing formation evaluation from LAS or DLIS well log data
- Running petrophysical calculations (Vshale, porosity, Sw, permeability)
- Building lithology classifications from log responses
- Correlating formations across multiple wells
- Generating composite log displays or 3D well visualizations

Use individual domain skills when:
- Only reading/writing LAS files (use `lasio` alone)
- Only parsing DLIS data (use `dlisio` alone)
- Only making stereonet plots from oriented data (use `mplstereonet`)

## Common Issues

| Issue | Solution |
|-------|----------|
| LAS encoding errors | Use `lasio.read(f, encoding='latin-1')` |
| Curves have different depth sampling | Resample with `welly` or `np.interp` |
| Negative porosity values | Flag invalid samples and check matrix/fluid density assumptions |
| Sw > 1.0 from Archie | Check Rw, Archie parameters; use clay-corrected model |
| Vshale > 1 in hot shales | Apply non-linear Vshale correction (Larionov) |
| DLIS multi-frame confusion | Iterate `f.frames` to find correct frame with target channels |
